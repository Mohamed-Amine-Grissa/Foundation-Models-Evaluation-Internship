"""Runs the AI judge (judge_model, Phi-3.5-mini) on every row of the labeling sheet.

The judge sees exactly what the human labeler saw: the question, reference
answer, accepted variants and response columns of to_label.csv, plus the full
rubric (prompts/rubric_v1.md) inside prompts/judge_v1.txt. The human_label and
human_note columns are never read into the prompt, and answer_key.json is not
opened, so the judge does not know which model wrote a response.

Output is constrained to the verdict JSON schema. On this llama-server build,
response_format json_schema on /v1/chat/completions fails for Phi-3.5
("Failed to initialize samplers: Unexpected empty grammar stack"), so the
prompt is formatted with the server's own chat template (/apply-template) and
sent to /completion with json_schema. Every output is still parsed, and parse
failures are recorded.

Starts and stops the chat llama-server itself (scripts/llama_servers.py).

Usage (from repo root):  .venv\\Scripts\\python.exe week2_judge/run_judge.py
"""
import csv
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.config import REPO_ROOT, load_config, llama_build
from common.runlog import write_run_log, sha256_of_file
from scripts.llama_servers import start, stop

TEMPERATURE = 0.0
SEED = 42
N_PREDICT = 256
PROMPT_VERSION = "judge_v1"
VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["correct", "incorrect"]},
        "reason": {"type": "string"},
    },
    "required": ["verdict", "reason"],
    "additionalProperties": False,
}
JUDGE_FIELDS = ["question", "reference_answer", "accepted_variants", "response"]

PROMPT_FILE = REPO_ROOT / "prompts" / f"{PROMPT_VERSION}.txt"
RUBRIC_FILE = REPO_ROOT / "prompts" / "rubric_v1.md"
SHEET = REPO_ROOT / "results" / "week2" / "labeling" / "to_label.csv"
OUT_DIR = REPO_ROOT / "results" / "week2" / "judge"

def load_rows() -> list[dict]:
    # keep only row_id and the columns the human labeler was shown
    with open(SHEET, newline="", encoding="utf-8-sig") as f:
        return [{"row_id": r["row_id"], **{k: r[k] for k in JUDGE_FIELDS}} for r in csv.DictReader(f)]

def build_prompt(template: str, rubric: str, row: dict) -> str:
    return (template.replace("{{RUBRIC}}", rubric)
                    .replace("{{QUESTION}}", row["question"])
                    .replace("{{REFERENCE_ANSWER}}", row["reference_answer"])
                    .replace("{{ACCEPTED_VARIANTS}}", row["accepted_variants"] or "(none)")
                    .replace("{{RESPONSE}}", row["response"]))

def parse_verdict(text: str) -> tuple[str | None, str | None, str | None]:
    """Returns (verdict, reason, error); verdict is None when parsing fails."""
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        return None, None, f"invalid JSON: {e}"
    if not isinstance(obj, dict) or obj.get("verdict") not in ("correct", "incorrect"):
        return None, None, "missing or invalid verdict"
    return obj["verdict"], obj.get("reason"), None

def main() -> None:
    cfg = load_config()
    judge_file = cfg["llama_cpp"]["judge_model"]
    judge = Path(cfg["llama_cpp"]["models_dir"]) / judge_file
    base = f"http://localhost:{cfg['servers']['chat_port']}"
    template = PROMPT_FILE.read_text(encoding="utf-8")
    rubric = RUBRIC_FILE.read_text(encoding="utf-8").strip()
    rows = load_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{PROMPT_VERSION}.jsonl"

    start(cfg, "chat", judge_file)
    try:
        served = [Path(m["id"]).name for m in requests.get(f"{base}/v1/models", timeout=10).json()["data"]]
        if judge.name not in served:
            sys.exit(f"chat server is serving {served}, not {judge.name}")
        n_fail = 0
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            for row in rows:
                messages = [{"role": "user", "content": build_prompt(template, rubric, row)}]
                prompt = requests.post(f"{base}/apply-template", json={"messages": messages},
                                       timeout=30).json()["prompt"]
                res = requests.post(f"{base}/completion", json={
                    "prompt": prompt, "temperature": TEMPERATURE, "seed": SEED,
                    "n_predict": N_PREDICT, "json_schema": VERDICT_SCHEMA}, timeout=300).json()
                verdict, reason, error = parse_verdict(res["content"])
                n_fail += verdict is None
                f.write(json.dumps({
                    "row_id": row["row_id"], "verdict": verdict, "reason": reason,
                    "parse_error": error, "raw_output": res["content"],
                    "stop_type": res.get("stop_type"), "tokens_predicted": res.get("tokens_predicted"),
                }, ensure_ascii=False) + "\n")
                print(f"[row {row['row_id']}] parsed={verdict is not None} stop={res.get('stop_type')}",
                      flush=True)
        build = llama_build(cfg, "llama-server.exe")
    finally:
        stop()

    write_run_log(str(OUT_DIR / f"{PROMPT_VERSION}.run_log.json"),
                  model_path=str(judge), llama_build=build,
                  command="python week2_judge/run_judge.py",
                  prompt_version=PROMPT_VERSION, seed=SEED, temperature=TEMPERATURE,
                  extra={"chat_port": cfg["servers"]["chat_port"], "n_predict": N_PREDICT,
                         "endpoint": "/apply-template + /completion",
                         "constrained_output": "json_schema", "verdict_schema": VERDICT_SCHEMA,
                         "prompt_sha256": sha256_of_file(str(PROMPT_FILE)),
                         "rubric_sha256": sha256_of_file(str(RUBRIC_FILE)),
                         "sheet_file": SHEET.relative_to(REPO_ROOT).as_posix(),
                         "sheet_columns_shown": JUDGE_FIELDS,
                         "n_rows": len(rows), "n_parse_failures": n_fail})
    print(f"Wrote {out_path.relative_to(REPO_ROOT)}; parse failures: {n_fail}/{len(rows)}")

if __name__ == "__main__":
    main()
