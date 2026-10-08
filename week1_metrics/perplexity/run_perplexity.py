"""Runs llama-perplexity on every corpus file and tabulates PPL / cross-entropy.

Usage (from repo root):  python week1_metrics/perplexity/run_perplexity.py
"""
import csv
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.config import REPO_ROOT, load_config, bin_path, model_path, llama_build
from common.metrics import parse_perplexity_output
from common.runlog import write_run_log

CTX = 128
THREADS = 8

CORPUS_DIR = REPO_ROOT / "data" / "corpus"
OUT_DIR = REPO_ROOT / "results" / "week1" / "perplexity"
RAW_DIR = OUT_DIR / "raw"

def main() -> None:
    cfg = load_config()
    exe = bin_path(cfg, "llama-perplexity.exe")
    model = model_path(cfg, "chat_model")
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    rows, commands = [], []
    for corpus_file in sorted(CORPUS_DIR.glob("*.txt")):
        cmd = [str(exe), "-m", str(model), "-f", str(corpus_file),
               "-c", str(CTX), "-t", str(THREADS)]
        # logged form: exe and model by name, corpus path relative to repo root
        commands.append(subprocess.list2cmdline(
            [exe.name, "-m", model.name, "-f", corpus_file.relative_to(REPO_ROOT).as_posix(),
             "-c", str(CTX), "-t", str(THREADS)]))
        print(f"[ppl] {corpus_file.name} ...", flush=True)
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        raw = proc.stdout + proc.stderr
        (RAW_DIR / corpus_file.name).write_text(raw, encoding="utf-8")
        if proc.returncode != 0:
            print(f"  llama-perplexity exited with {proc.returncode}; "
                  f"see {RAW_DIR / corpus_file.name}", file=sys.stderr)
            continue
        parsed = parse_perplexity_output(raw)
        rows.append({"file": corpus_file.name, **parsed})
        print(f"  PPL = {parsed['ppl']:.4f} +/- {parsed['ci']:.4f}")

    fields = ["file", "ppl", "ci", "cross_entropy_bits", "cross_entropy_nats"]
    with open(OUT_DIR / "perplexity.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    write_run_log(str(OUT_DIR / "run_log.json"),
                  model_path=str(model),
                  llama_build=llama_build(cfg),
                  command=" && ".join(commands),
                  extra={"ctx": CTX, "threads": THREADS,
                         "corpus_files": [r["file"] for r in rows]})
    print(f"Wrote {OUT_DIR / 'perplexity.csv'}")

if __name__ == "__main__":
    main()
