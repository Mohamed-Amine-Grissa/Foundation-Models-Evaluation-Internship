"""Generates one response per shared-task question with one generator model.

Requires the chat llama-server on chat_port (config.toml), serving the model
named by --model (default: chat_model). Responses go to
results/week2/responses/<model file stem>.jsonl.

Usage (from repo root):
    python week2_judge/generate_responses.py [--model <gguf file>]
"""
import argparse
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.config import REPO_ROOT, load_config, generator_path, llama_build
from common.llm import LlamaServerClient
from common.runlog import write_run_log, sha256_of_file

TEMPERATURE = 0.7
SEED = 42                 # same seed for every question and both models
MAX_TOKENS = 512
PROMPT_VERSION = "week2_generator_system_v1"

QUESTIONS_JSONL = REPO_ROOT / "data" / "task" / "questions.jsonl"
SYSTEM_PROMPT_FILE = REPO_ROOT / "prompts" / f"{PROMPT_VERSION}.txt"
OUT_DIR = REPO_ROOT / "results" / "week2" / "responses"

def main() -> None:
    cfg = load_config()
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=cfg["llama_cpp"]["chat_model"],
                        help="generator GGUF filename from config.toml (must be the one the chat server is serving)")
    args = parser.parse_args()
    model = generator_path(cfg, args.model)

    client = LlamaServerClient(cfg["servers"]["chat_port"])
    served = [Path(m["id"]).name for m in requests.get(f"{client.base}/v1/models", timeout=10).json()["data"]]
    if model.name not in served:
        sys.exit(f"chat server is serving {served}, not {model.name}; refusing to mislabel results")

    system_prompt = SYSTEM_PROMPT_FILE.read_text(encoding="utf-8").strip()
    questions = [json.loads(l) for l in QUESTIONS_JSONL.read_text(encoding="utf-8").splitlines() if l]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{model.stem}.jsonl"

    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        for q in questions:
            res = client.chat(system_prompt, q["question"], temperature=TEMPERATURE,
                              max_tokens=MAX_TOKENS, seed=SEED)
            choice = res["raw"]["choices"][0]
            usage = res["raw"].get("usage", {})
            f.write(json.dumps({
                "question_id": q["id"], "category": q["category"], "question": q["question"],
                "model_file": model.name, "seed": SEED, "temperature": TEMPERATURE,
                "max_tokens": MAX_TOKENS, "response": res["text"],
                "finish_reason": choice.get("finish_reason"),
                "completion_tokens": usage.get("completion_tokens"),
            }, ensure_ascii=False) + "\n")
            print(f"[{q['id']}] finish={choice.get('finish_reason')} tokens={usage.get('completion_tokens')}",
                  flush=True)

    write_run_log(str(OUT_DIR / f"{model.stem}.run_log.json"),
                  model_path=str(model),
                  llama_build=llama_build(cfg, "llama-server.exe"),
                  command=f"python week2_judge/generate_responses.py --model {model.name}",
                  prompt_version=PROMPT_VERSION, seed=SEED, temperature=TEMPERATURE,
                  extra={"chat_port": cfg["servers"]["chat_port"], "max_tokens": MAX_TOKENS,
                         "questions_file": QUESTIONS_JSONL.relative_to(REPO_ROOT).as_posix(),
                         "questions_sha256": sha256_of_file(str(QUESTIONS_JSONL)),
                         "n_questions": len(questions)})
    print(f"Wrote {out_path.relative_to(REPO_ROOT)}")

if __name__ == "__main__":
    main()
