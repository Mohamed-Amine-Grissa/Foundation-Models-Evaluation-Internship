"""Compares the judge's verdicts (judge_v1.jsonl) with the human labels (to_label.csv).

Reports, overall, per question category and per generator model: raw agreement
rate, Cohen's kappa, and the judge-vs-human confusion matrix. These measure
agreement between two labelers; neither is the judge's accuracy.

Rows with no human label, a human label outside LABEL_MAP, or a judge verdict
that failed to parse are listed in agreement.json and excluded from every
statistic. to_label.csv and answer_key.json are only read.

Writes:
    results/week2/judge/agreement.json
    results/week2/judge/agreement_table.md
    results/week2/judge/disagreements.csv
    report/generated/week2_agreement.tex   (bare booktabs tabular)

Usage (from repo root):  .venv\\Scripts\\python.exe week2_judge/agreement.py
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.config import REPO_ROOT, load_config
from scripts.make_week1_figures import MODEL_LABELS, tex, write_table

# exact sheet value (after stripping whitespace) -> label; anything else is excluded
LABEL_MAP = {"correct": "correct", "incorrect": "incorrect"}
LABELS = ["correct", "incorrect"]
CATEGORY_ORDER = ["factual", "word_problem", "trap"]
CATEGORY_FR = {"factual": "Factuelle", "word_problem": "Problème à énoncé", "trap": "Question piège"}

QUESTIONS_JSONL = REPO_ROOT / "data" / "task" / "questions.jsonl"
LABEL_DIR = REPO_ROOT / "results" / "week2" / "labeling"
JUDGE_DIR = REPO_ROOT / "results" / "week2" / "judge"
JUDGE_JSONL = JUDGE_DIR / "judge_v1.jsonl"

def stats(pairs: list[tuple[str, str]]) -> dict:
    """pairs are (judge, human). Kappa is None when expected agreement is 1 (undefined)."""
    n = len(pairs)
    cm = {f"judge_{j}": {f"human_{h}": sum(1 for p in pairs if p == (j, h)) for h in LABELS} for j in LABELS}
    if n == 0:
        return {"n": 0, "raw_agreement": None, "cohen_kappa": None, "confusion_matrix": cm}
    p_o = sum(1 for j, h in pairs if j == h) / n
    p_e = sum((sum(1 for j, _ in pairs if j == lab) / n) * (sum(1 for _, h in pairs if h == lab) / n)
              for lab in LABELS)
    kappa = None if p_e == 1 else (p_o - p_e) / (1 - p_e)
    return {"n": n, "raw_agreement": p_o, "expected_agreement": p_e, "cohen_kappa": kappa,
            "confusion_matrix": cm}

def fmt(x: float | None, digits: int = 3) -> str:
    return "n/a" if x is None else f"{x:.{digits}f}"

def main() -> None:
    questions = {q["id"]: q for q in map(json.loads, QUESTIONS_JSONL.read_text(encoding="utf-8").splitlines()) if q}
    key = json.loads((LABEL_DIR / "answer_key.json").read_text(encoding="utf-8"))
    with open(LABEL_DIR / "to_label.csv", newline="", encoding="utf-8-sig") as f:
        sheet = {r["row_id"]: r for r in csv.DictReader(f)}
    judge = {j["row_id"]: j for j in map(json.loads, JUDGE_JSONL.read_text(encoding="utf-8").splitlines()) if j}

    if set(sheet) != set(key) or set(sheet) != set(judge):
        sys.exit("row ids differ between to_label.csv, answer_key.json and judge_v1.jsonl")

    excluded, items = [], []
    for row_id in sorted(sheet, key=int):
        raw = sheet[row_id]["human_label"].strip()
        reasons = []
        if not raw:
            reasons.append("no human_label")
        elif raw not in LABEL_MAP:
            reasons.append(f"unmapped human_label {raw!r}")
        if judge[row_id]["verdict"] is None:
            reasons.append(f"judge parse failure: {judge[row_id]['parse_error']}")
        if reasons:
            excluded.append({"row_id": row_id, "reasons": reasons})
            continue
        qid = key[row_id]["question_id"]
        items.append({"row_id": row_id, "question_id": qid, "category": questions[qid]["category"],
                      "model": Path(key[row_id]["model_file"]).stem,
                      "human": LABEL_MAP[raw], "judge": judge[row_id]["verdict"]})

    def subset(pred) -> dict:
        return stats([(it["judge"], it["human"]) for it in items if pred(it)])

    models = [Path(m).stem for m in load_config()["llama_cpp"]["generators"]]
    result = {
        "inputs": {"human_labels": "results/week2/labeling/to_label.csv",
                   "answer_key": "results/week2/labeling/answer_key.json",
                   "judge_verdicts": JUDGE_JSONL.relative_to(REPO_ROOT).as_posix()},
        "label_mapping": LABEL_MAP,
        "n_rows": len(sheet), "n_used": len(items), "excluded": excluded,
        "overall": subset(lambda it: True),
        "by_category": {c: subset(lambda it, c=c: it["category"] == c) for c in CATEGORY_ORDER},
        "by_model": {m: subset(lambda it, m=m: it["model"] == m) for m in models},
    }
    JUDGE_DIR.mkdir(parents=True, exist_ok=True)
    (JUDGE_DIR / "agreement.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    groups = ([("overall", "Ensemble", result["overall"])]
              + [(c, CATEGORY_FR[c], result["by_category"][c]) for c in CATEGORY_ORDER]
              + [(m, MODEL_LABELS.get(m, m), result["by_model"][m]) for m in models])
    def cells(s: dict) -> list[str]:
        cm = s["confusion_matrix"]
        return [str(s["n"]), fmt(s["raw_agreement"]), fmt(s["cohen_kappa"]),
                *[str(cm[f"judge_{j}"][f"human_{h}"]) for j in LABELS for h in LABELS]]

    md = ["| subset | n | raw agreement | Cohen's kappa | J=c, H=c | J=c, H=i | J=i, H=c | J=i, H=i |",
          "|---|---|---|---|---|---|---|---|"]
    md += [f"| {name} | " + " | ".join(cells(s)) + " |" for name, _, s in groups]
    md += ["", "J = judge (Phi-3.5-mini, judge_v1), H = human label; c = correct, i = incorrect.",
           f"Rows used: {len(items)}/{len(sheet)}; excluded: {len(excluded)}."]
    (JUDGE_DIR / "agreement_table.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    header = [["Sous-ensemble", "$n$", "Accord brut", r"$\kappa$ de Cohen",
               r"\multicolumn{2}{c}{Juge : correct}", r"\multicolumn{2}{c}{Juge : incorrect}"],
              ["", "", "", "", "H : correct", "H : incorrect", "H : correct", "H : incorrect"]]
    rules = [r"\cmidrule(lr){5-6} \cmidrule(lr){7-8}"]
    body = [[tex(label), *cells(s)] for _, label, s in groups]
    (REPO_ROOT / "report" / "generated").mkdir(parents=True, exist_ok=True)
    write_table("week2_agreement.tex", "lrrrrrrr", header, body, rules)

    fields = ["row_id", "question_id", "category", "model", "question", "reference_answer",
              "accepted_variants", "response", "human_label", "human_note", "judge_verdict", "judge_reason"]
    with open(JUDGE_DIR / "disagreements.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for it in items:
            if it["judge"] == it["human"]:
                continue
            s = sheet[it["row_id"]]
            w.writerow({"row_id": it["row_id"], "question_id": it["question_id"], "category": it["category"],
                        "model": it["model"], "question": s["question"],
                        "reference_answer": s["reference_answer"], "accepted_variants": s["accepted_variants"],
                        "response": s["response"], "human_label": it["human"], "human_note": s["human_note"],
                        "judge_verdict": it["judge"], "judge_reason": judge[it["row_id"]]["reason"]})

    print(f"label mapping: {LABEL_MAP}")
    print(f"rows used {len(items)}/{len(sheet)}; excluded: {excluded or 'none'}")
    print("\n".join(md[:len(groups) + 2]))
    print("Wrote agreement.json, agreement_table.md, disagreements.csv in", JUDGE_DIR.relative_to(REPO_ROOT))

if __name__ == "__main__":
    main()
