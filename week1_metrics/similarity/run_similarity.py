"""Scores reference/response pairs with exact match, BLEU, ROUGE-L and
embedding cosine similarity.

Requires the embedding llama-server on embed_port (config.toml).
Usage (from repo root):  python week1_metrics/similarity/run_similarity.py
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.config import REPO_ROOT, load_config, model_path, llama_build
from common.llm import LlamaServerClient
from common.metrics import exact_match, bleu, rouge_l, cosine_sim
from common.runlog import write_run_log

EMBED_PREFIX = "search_document: "

PAIRS_CSV = REPO_ROOT / "data" / "similarity_pairs.csv"
OUT_DIR = REPO_ROOT / "results" / "week1" / "similarity"

def main() -> None:
    cfg = load_config()
    client = LlamaServerClient(cfg["servers"]["embed_port"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(PAIRS_CSV, newline="", encoding="utf-8") as f:
        pairs = list(csv.DictReader(f))

    rows = []
    for i, p in enumerate(pairs):
        ref, resp = p["reference"], p["response"]
        cos = cosine_sim(client.embed(ref, prefix=EMBED_PREFIX),
                         client.embed(resp, prefix=EMBED_PREFIX))
        row = {
            "pair_id": i,
            "category": p["category"],
            "reference": ref,
            "response": resp,
            "exact_match": int(exact_match(ref, resp)),
            "bleu": bleu(ref, resp),
            "rouge_l": rouge_l(ref, resp),
            "cosine": cos,
        }
        rows.append(row)
        print(f"[{row['category']:14}] EM={row['exact_match']} BLEU={row['bleu']:.3f} "
              f"ROUGE-L={row['rouge_l']:.3f} cos={row['cosine']:.3f} | {ref!r} vs {resp!r}")

    with open(OUT_DIR / "similarity.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    write_run_log(str(OUT_DIR / "run_log.json"),
                  model_path=str(model_path(cfg, "embed_model")),
                  llama_build=llama_build(cfg, "llama-server.exe"),
                  command="python week1_metrics/similarity/run_similarity.py",
                  extra={"embed_port": cfg["servers"]["embed_port"],
                         "embed_prefix": EMBED_PREFIX,
                         "pairs_file": PAIRS_CSV.relative_to(REPO_ROOT).as_posix(),
                         "n_pairs": len(rows)})
    print(f"Wrote {OUT_DIR / 'similarity.csv'}")

if __name__ == "__main__":
    main()
