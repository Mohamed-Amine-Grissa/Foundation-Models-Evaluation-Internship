"""Merges the generator responses into one blind labeling sheet.

The sheet shows, per row, what the rubric (prompts/rubric_v1.md) says the
labeler sees: question, reference answer, accepted variants, response. Which
model wrote each response is kept out of the sheet, in answer_key.json, and
rows are shuffled with a fixed seed.

Usage (from repo root):  python week2_judge/build_labeling_sheet.py
"""
import csv
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.config import REPO_ROOT

SHUFFLE_SEED = 42
GENERATORS = ["qwen2.5-1.5b-instruct-q4_k_m", "Llama-3.2-3B-Instruct-Q4_K_M",
              "qwen2.5-0.5b-instruct-q4_k_m"]

QUESTIONS_JSONL = REPO_ROOT / "data" / "task" / "questions.jsonl"
RESP_DIR = REPO_ROOT / "results" / "week2" / "responses"
OUT_DIR = REPO_ROOT / "results" / "week2" / "labeling"

def main() -> None:
    questions = {q["id"]: q for q in map(json.loads, QUESTIONS_JSONL.read_text(encoding="utf-8").splitlines())}
    items = []
    for stem in GENERATORS:
        path = RESP_DIR / f"{stem}.jsonl"
        if not path.exists():
            sys.exit(f"missing {path.relative_to(REPO_ROOT)}; run generate_responses.py for that model first")
        items += [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l]

    random.Random(SHUFFLE_SEED).shuffle(items)
    rows, key = [], {}
    for row_id, it in enumerate(items, start=1):
        q = questions[it["question_id"]]
        key[row_id] = {"question_id": it["question_id"], "model_file": it["model_file"],
                       "finish_reason": it["finish_reason"]}
        rows.append({
            "row_id": row_id,
            "question": q["question"],
            "reference_answer": q["reference_answer"],
            "accepted_variants": "; ".join(q["accepted_variants"]),
            "response": it["response"],
            "human_label": "",     # correct / incorrect, per prompts/rubric_v1.md
            "human_note": "",      # optional, never changes the label
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # utf-8-sig so Excel shows characters such as "°" correctly
    with open(OUT_DIR / "to_label.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    (OUT_DIR / "answer_key.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
    print(f"Wrote {len(rows)} rows to {(OUT_DIR / 'to_label.csv').relative_to(REPO_ROOT)}")
    print(f"Wrote {(OUT_DIR / 'answer_key.json').relative_to(REPO_ROOT)} (do not open before labeling)")

if __name__ == "__main__":
    main()
