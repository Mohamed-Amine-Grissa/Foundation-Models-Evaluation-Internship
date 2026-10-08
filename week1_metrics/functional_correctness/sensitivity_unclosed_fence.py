"""Sensitivity analysis: re-scores the SAVED replies of every model under a
lenient extraction rule. Nothing is generated.

  strict  (primary result, run_functional.py): code = first complete fenced
          block (opening AND closing ```); otherwise the raw reply is executed.
  lenient (sensitivity only): same as strict when a complete block exists;
          otherwise, if the reply contains an opening fence, code = everything
          after that opening fence line.

Both rules are executed here with run_functional.run_sample (same sandbox and
timeout), and the strict outcomes are checked against the saved ones.

Usage (from repo root):  python week1_metrics/functional_correctness/sensitivity_unclosed_fence.py
"""
import csv
import importlib.util
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.config import REPO_ROOT, load_config
from common.metrics import pass_at_k

_spec = importlib.util.spec_from_file_location("run_functional", Path(__file__).with_name("run_functional.py"))
rf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rf)

RESULTS_DIR = REPO_ROOT / "results" / "week1" / "functional"
OUT_DIR = RESULTS_DIR / "sensitivity_unclosed_fence"
_OPEN_FENCE_RE = re.compile(r"```(?:python|py)?[ \t]*\r?\n", re.IGNORECASE)

def extract_lenient(text: str) -> tuple[str, str]:
    code, method = rf.extract_code(text)
    if method == "fenced":
        return code, "fenced"
    m = _OPEN_FENCE_RE.search(text)
    if m:
        return text[m.end():], "unclosed_fence"
    return text, "raw_fallback"

def main() -> None:
    problems = {p["id"]: p for p in json.loads(rf.PROBLEMS_JSON.read_text(encoding="utf-8"))}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    table, changed = [], []
    for model_file in load_config()["llama_cpp"]["generators"]:
        stem = Path(model_file).stem
        path = RESULTS_DIR / stem / "samples.jsonl"
        if not path.exists():
            continue
        samples = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l]
        counts = {pid: {"strict": 0, "lenient": 0, "n": 0} for pid in problems}
        for s in samples:
            tests = problems[s["problem_id"]]["tests"]
            strict_code, _ = rf.extract_code(s["reply"])
            strict_outcome, _ = rf.run_sample(strict_code, tests)
            if strict_outcome != s["outcome"]:
                sys.exit(f"strict re-run of {stem} {s['problem_id']} s{s['sample']} gave "
                         f"{strict_outcome}, saved outcome is {s['outcome']}")
            len_code, len_method = extract_lenient(s["reply"])
            len_outcome, len_detail = rf.run_sample(len_code, tests)
            c = counts[s["problem_id"]]
            c["n"] += 1
            c["strict"] += strict_outcome == "pass"
            c["lenient"] += len_outcome == "pass"
            if len_method != s["extraction"] or len_outcome != strict_outcome:
                changed.append({"model": stem, "problem_id": s["problem_id"], "sample": s["sample"],
                                "strict_extraction": s["extraction"], "strict_outcome": strict_outcome,
                                "lenient_extraction": len_method, "lenient_outcome": len_outcome,
                                "lenient_detail": len_detail})
        for pid, c in counts.items():
            table.append({"model": stem, "problem_id": pid, "n": c["n"],
                          "c_strict": c["strict"], "pass@1_strict": pass_at_k(c["n"], c["strict"], 1),
                          "c_lenient": c["lenient"], "pass@1_lenient": pass_at_k(c["n"], c["lenient"], 1)})
        rows = [r for r in table if r["model"] == stem]
        table.append({"model": stem, "problem_id": "MEAN", "n": sum(r["n"] for r in rows),
                      "c_strict": sum(r["c_strict"] for r in rows),
                      "pass@1_strict": sum(r["pass@1_strict"] for r in rows) / len(rows),
                      "c_lenient": sum(r["c_lenient"] for r in rows),
                      "pass@1_lenient": sum(r["pass@1_lenient"] for r in rows) / len(rows)})
        print(f"{stem}: strict {table[-1]['c_strict']}/{table[-1]['n']}, lenient {table[-1]['c_lenient']}/{table[-1]['n']}")

    with open(OUT_DIR / "pass_at_1_strict_vs_lenient.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0].keys()))
        w.writeheader()
        w.writerows(table)
    with open(OUT_DIR / "changed_samples.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["model", "problem_id", "sample", "strict_extraction", "strict_outcome",
                                          "lenient_extraction", "lenient_outcome", "lenient_detail"])
        w.writeheader()
        w.writerows(changed)
    for c in changed:
        print(f"  changed: {c['model']} {c['problem_id']} s{c['sample']}: "
              f"{c['strict_outcome']} -> {c['lenient_outcome']} {c['lenient_detail']}")
    print(f"Wrote {OUT_DIR.relative_to(REPO_ROOT)}")

if __name__ == "__main__":
    main()
