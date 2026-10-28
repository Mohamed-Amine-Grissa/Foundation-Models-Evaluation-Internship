"""Terminal tool for labeling the blind sheet, one row at a time.

Reads and writes only results/week2/labeling/to_label.csv: it never opens
answer_key.json or results/week2/responses/, so it cannot reveal which model
wrote a response. Each label is saved to the CSV as soon as it is entered, and
a new session starts at the first row with no human_label.

Usage (from repo root):  python week2_judge/label.py
Keys: c = correct, i = incorrect, q = quit (after c/i, a note is optional).
"""
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.config import REPO_ROOT

SHEET = REPO_ROOT / "results" / "week2" / "labeling" / "to_label.csv"
LABELS = {"c": "correct", "i": "incorrect"}   # per prompts/rubric_v1.md

def load() -> tuple[list[str], list[dict]]:
    with open(SHEET, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)

def save(fields: list[str], rows: list[dict]) -> None:
    # write to a temp file then swap, so quitting mid-write never corrupts the sheet
    tmp = SHEET.with_suffix(".csv.tmp")
    with open(tmp, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, SHEET)

def show(row: dict, n_done: int, n_total: int) -> None:
    os.system("cls" if os.name == "nt" else "clear")
    print(f"Row {row['row_id']}   ({n_done}/{n_total} labeled)\n")
    print(f"QUESTION:\n{row['question']}\n")
    print(f"REFERENCE ANSWER:\n{row['reference_answer']}\n")
    print(f"ACCEPTED VARIANTS:\n{row['accepted_variants'] or '(none)'}\n")
    print("RESPONSE:\n" + "-" * 70)
    print(row["response"])
    print("-" * 70)

def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if not SHEET.exists():
        sys.exit(f"missing {SHEET.relative_to(REPO_ROOT)}; run build_labeling_sheet.py first")
    fields, rows = load()
    n_total = len(rows)
    try:
        for row in rows:
            if row["human_label"].strip():
                continue
            show(row, sum(1 for r in rows if r["human_label"].strip()), n_total)
            key = ""
            while key not in LABELS:
                key = input("[c] correct  [i] incorrect  [q] quit > ").strip().lower()
                if key == "q":
                    print("Stopped; the next run resumes at this row.")
                    return
            note = input("note (Enter for none) > ").strip()
            row["human_label"], row["human_note"] = LABELS[key], note
            save(fields, rows)
    except (KeyboardInterrupt, EOFError):
        print("\nStopped; labels entered so far are saved.")
        return
    except PermissionError:
        sys.exit(f"cannot write {SHEET.name} (open in Excel?); close it and rerun to resume")
    print(f"All {n_total} rows labeled.")

if __name__ == "__main__":
    main()
