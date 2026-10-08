"""Functional correctness of generated code: n samples per problem, each run
against its asserts in an isolated subprocess, summarised as pass@k.

Requires the chat llama-server on chat_port (config.toml), serving the model
named by --model (default: chat_model). Results go to a per-model folder.
Usage (from repo root):
    python week1_metrics/functional_correctness/run_functional.py [--model <gguf file>]
"""
import argparse
import csv
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.config import REPO_ROOT, load_config, generator_path, llama_build
from common.llm import LlamaServerClient
from common.metrics import pass_at_k
from common.runlog import write_run_log, sha256_of_file

N_SAMPLES = 5
KS = (1, 5)
TEMPERATURE = 0.8
BASE_SEED = 1000          # sample i of every problem uses seed BASE_SEED + i
MAX_TOKENS = 512
TIMEOUT_S = 5
PROMPT_VERSION = "week1_functional_system_v1"

PROBLEMS_JSON = REPO_ROOT / "data" / "code_problems.json"
SYSTEM_PROMPT_FILE = REPO_ROOT / "prompts" / f"{PROMPT_VERSION}.txt"
RESULTS_DIR = REPO_ROOT / "results" / "week1" / "functional"   # one subfolder per model

_FENCE_RE = re.compile(r"```(?:python|py)?[ \t]*\r?\n(.*?)```", re.DOTALL | re.IGNORECASE)

def extract_code(text: str) -> tuple[str, str]:
    """Returns (code, method). Uses the first fenced block; falls back to the
    raw reply when the model used no fence."""
    m = _FENCE_RE.search(text)
    if m:
        return m.group(1), "fenced"
    return text, "raw_fallback"

def run_sample(code: str, tests: list[str]) -> tuple[str, str]:
    """Runs code + asserts in a fresh interpreter inside a temp dir.
    Returns (outcome, detail) with outcome in pass / fail / timeout."""
    program = code + "\n\n" + "\n".join(tests) + "\n"
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "sample.py"
        script.write_text(program, encoding="utf-8")
        try:
            proc = subprocess.run([sys.executable, str(script)], cwd=tmp,
                                  capture_output=True, text=True, timeout=TIMEOUT_S)
        except subprocess.TimeoutExpired:
            return "timeout", f"exceeded {TIMEOUT_S}s"
    if proc.returncode == 0:
        return "pass", ""
    err_lines = proc.stderr.strip().splitlines()
    return "fail", err_lines[-1] if err_lines else f"exit code {proc.returncode}"

def main() -> None:
    cfg = load_config()
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=cfg["llama_cpp"]["chat_model"],
                        help="generator GGUF filename from config.toml (must be the one the chat server is serving)")
    args = parser.parse_args()
    model = generator_path(cfg, args.model)
    OUT_DIR = RESULTS_DIR / model.stem
    client = LlamaServerClient(cfg["servers"]["chat_port"])
    served = [Path(m["id"]).name for m in requests.get(f"{client.base}/v1/models", timeout=10).json()["data"]]
    if model.name not in served:
        sys.exit(f"chat server is serving {served}, not {model.name}; refusing to mislabel results")
    system_prompt = SYSTEM_PROMPT_FILE.read_text(encoding="utf-8").strip()
    problems = json.loads(PROBLEMS_JSON.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    summary = []
    with open(OUT_DIR / "samples.jsonl", "w", encoding="utf-8") as samples_f:
        for prob in problems:
            passes = 0
            for i in range(N_SAMPLES):
                seed = BASE_SEED + i
                reply = client.chat(system_prompt, prob["prompt"],
                                    temperature=TEMPERATURE, max_tokens=MAX_TOKENS,
                                    seed=seed)["text"]
                code, method = extract_code(reply)
                outcome, detail = run_sample(code, prob["tests"])
                passes += outcome == "pass"
                samples_f.write(json.dumps({
                    "problem_id": prob["id"], "sample": i, "seed": seed,
                    "temperature": TEMPERATURE, "reply": reply, "code": code,
                    "extraction": method, "outcome": outcome, "detail": detail,
                }, ensure_ascii=False) + "\n")
                print(f"[{prob['id']:18}] sample {i} seed {seed}: {outcome} {detail}")
            row = {"problem_id": prob["id"], "n": N_SAMPLES, "c": passes}
            for k in KS:
                row[f"pass@{k}"] = pass_at_k(N_SAMPLES, passes, k)
            summary.append(row)

    # MEAN row: n and c are totals over all problems; pass@k is the mean of
    # the per-problem estimates (not recomputed from the totals)
    mean_row = {"problem_id": "MEAN", "n": N_SAMPLES * len(summary),
                "c": sum(r["c"] for r in summary)}
    for k in KS:
        mean_row[f"pass@{k}"] = sum(r[f"pass@{k}"] for r in summary) / len(summary)
    summary.append(mean_row)

    with open(OUT_DIR / "pass_at_k.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)

    write_run_log(str(OUT_DIR / "run_log.json"),
                  model_path=str(model),
                  llama_build=llama_build(cfg, "llama-server.exe"),
                  command=f"python week1_metrics/functional_correctness/run_functional.py --model {model.name}",
                  prompt_version=PROMPT_VERSION,
                  seed=BASE_SEED,
                  temperature=TEMPERATURE,
                  extra={"chat_port": cfg["servers"]["chat_port"],
                         "n_samples": N_SAMPLES, "seeds": [BASE_SEED + i for i in range(N_SAMPLES)],
                         "ks": list(KS), "max_tokens": MAX_TOKENS,
                         "timeout_s": TIMEOUT_S,
                         "problems_file": PROBLEMS_JSON.relative_to(REPO_ROOT).as_posix(),
                         "problems_sha256": sha256_of_file(str(PROBLEMS_JSON))})
    print(f"Wrote {OUT_DIR / 'samples.jsonl'} and {OUT_DIR / 'pass_at_k.csv'}")

if __name__ == "__main__":
    main()
