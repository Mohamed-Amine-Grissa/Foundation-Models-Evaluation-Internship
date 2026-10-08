"""Classifies every failing sample from run_functional.py into exactly one category.

Categories, checked in this order (first match wins):
  no_code   - run_functional.py found no complete fenced code block (opening
              AND closing ```) and fell back to the raw reply
              (extraction == raw_fallback); this includes replies with an
              opening fence but no closing one
  timeout   - the sample exceeded the timeout in run_functional.py
  crash     - loading the code raised any exception (including SyntaxError,
              and AssertionError from asserts the model wrote into its own
              reply), or calling the function on a tested input raised an
              exception other than AssertionError
  format    - at least one failing assert received a return value that breaks
              the output-format rules stated in the prompt (FORMAT_CHECKS below)
  logic     - everything else: right format, wrong value

Each failing sample is re-executed in a fresh subprocess (temp dir, timeout) to
obtain the raw return value of every tested call.

Usage (from repo root):  python week1_metrics/functional_correctness/classify_failures.py
"""
import ast
import csv
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.config import REPO_ROOT

RESULTS_DIR = REPO_ROOT / "results" / "week1" / "functional"
PROBLEMS_JSON = REPO_ROOT / "data" / "code_problems.json"
CATEGORIES = ["format", "logic", "crash", "timeout", "no_code"]
TIMEOUT_S = 10

# Output-format rules from the prompts, checked on the raw return value.
FORMAT_CHECKS = r'''
import re
def _is_int(v): return isinstance(v, int) and not isinstance(v, bool)
FORMAT_CHECKS = {
    "is_palindrome": lambda v: isinstance(v, bool),
    "fizzbuzz": lambda v: isinstance(v, list) and all(
        isinstance(e, str) and (e in ("Fizz", "Buzz", "FizzBuzz") or e.isdigit()) for e in v),
    "second_largest": lambda v: v is None or _is_int(v),
    "run_length_encode": lambda v: isinstance(v, str) and re.fullmatch(r"(?:\D[1-9]\d*)*", v) is not None,
    "merge_intervals": lambda v: isinstance(v, list) and all(
        isinstance(i, list) and len(i) == 2 and all(_is_int(x) for x in i) for i in v),
    "roman_to_int": _is_int,
}
'''

HARNESS = FORMAT_CHECKS + r'''
import json, sys
problem_id, fn_name, tests = json.loads(sys.argv[1])
out = {"load_error": None, "tests": []}
ns = {}
try:
    exec(open("sample.py", encoding="utf-8").read(), ns)
except BaseException as e:
    out["load_error"] = type(e).__name__ + ": " + str(e)[:200]
    print(json.dumps(out)); sys.exit(0)
for test, call_src in tests:
    rec = {"test": test, "error": None, "format_ok": None, "passed": False}
    try:
        value = eval(call_src, ns)
        rec["value"] = repr(value)[:200]
        rec["format_ok"] = bool(FORMAT_CHECKS[problem_id](value))
        exec(test, ns)
        rec["passed"] = True
    except AssertionError:
        pass
    except BaseException as e:
        rec["error"] = type(e).__name__ + ": " + str(e)[:200]
    out["tests"].append(rec)
print(json.dumps(out))
'''

def call_source(test: str, fn_name: str) -> str:
    """Source of the first call to fn_name inside an assert statement."""
    tree = ast.parse(test)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == fn_name:
            return ast.unparse(node)
    raise ValueError(f"no call to {fn_name} in {test!r}")

def classify(sample: dict, problem: dict) -> tuple[str, str]:
    if sample["extraction"] == "raw_fallback":
        return "no_code", "no fenced code block in reply"
    if sample["outcome"] == "timeout":
        return "timeout", sample["detail"]
    tests = [(t, call_source(t, problem["function_name"])) for t in problem["tests"]]
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "sample.py").write_text(sample["code"], encoding="utf-8")
        (Path(tmp) / "harness.py").write_text(HARNESS, encoding="utf-8")
        try:
            proc = subprocess.run([sys.executable, "harness.py",
                                   json.dumps([problem["id"], problem["function_name"], tests])],
                                  cwd=tmp, capture_output=True, text=True, timeout=TIMEOUT_S)
        except subprocess.TimeoutExpired:
            return "timeout", f"re-execution exceeded {TIMEOUT_S}s"
    res = json.loads(proc.stdout.strip().splitlines()[-1])
    if res["load_error"]:
        return "crash", res["load_error"]
    crashed = [t for t in res["tests"] if t["error"]]
    if crashed:
        return "crash", f"{crashed[0]['error']} on `{crashed[0]['test']}`"
    failed = [t for t in res["tests"] if not t["passed"]]
    bad_format = [t for t in failed if t["format_ok"] is False]
    if bad_format:
        return "format", f"returned {bad_format[0]['value']} on `{bad_format[0]['test']}`"
    return "logic", f"returned {failed[0]['value']} on `{failed[0]['test']}`" if failed else "no failing assert reproduced"

def main() -> None:
    problems = {p["id"]: p for p in json.loads(PROBLEMS_JSON.read_text(encoding="utf-8"))}
    counts_rows = []
    for model_dir in sorted(d for d in RESULTS_DIR.iterdir() if (d / "samples.jsonl").exists()):
        samples = [json.loads(l) for l in (model_dir / "samples.jsonl").read_text(encoding="utf-8").splitlines() if l]
        rows = []
        for s in samples:
            if s["outcome"] == "pass":
                continue
            category, detail = classify(s, problems[s["problem_id"]])
            rows.append({"problem_id": s["problem_id"], "sample": s["sample"],
                         "seed": s["seed"], "category": category, "detail": detail})
        with open(model_dir / "failures.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["problem_id", "sample", "seed", "category", "detail"])
            w.writeheader()
            w.writerows(rows)
        counts = Counter(r["category"] for r in rows)
        counts_rows.append({"model": model_dir.name, **{c: counts.get(c, 0) for c in CATEGORIES},
                            "total_failures": len(rows), "total_samples": len(samples)})
        print(f"{model_dir.name}: {dict(counts)}  ({len(rows)}/{len(samples)} failing)")
        for r in rows:
            print(f"    {r['problem_id']:18} s{r['sample']} {r['category']:8} {r['detail']}")
    with open(RESULTS_DIR / "failure_counts.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["model", *CATEGORIES, "total_failures", "total_samples"])
        w.writeheader()
        w.writerows(counts_rows)
    print(f"Wrote {RESULTS_DIR / 'failure_counts.csv'}")

if __name__ == "__main__":
    main()
