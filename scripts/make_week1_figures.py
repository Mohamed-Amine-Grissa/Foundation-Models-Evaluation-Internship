"""Builds Week 1 figures (figures/*.pdf) and booktabs tables (report/generated/*.tex)
from the CSVs in results/week1/. Inputs that do not exist yet are skipped.

Tables are bare tabular environments: caption, label and float placement stay
in the LaTeX source that \\input's them. They require \\usepackage{booktabs}.

Usage (from repo root):  python scripts/make_week1_figures.py
"""
import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.config import REPO_ROOT

RESULTS = REPO_ROOT / "results" / "week1"
FIG_DIR = REPO_ROOT / "figures"
TABLE_DIR = REPO_ROOT / "report" / "generated"

CATEGORY_ORDER = ["near_duplicate", "paraphrase", "meaning_flip", "unrelated"]
CATEGORY_FR = {
    "near_duplicate": "Quasi-doublon",
    "paraphrase": "Paraphrase",
    "meaning_flip": "Inversion de sens",
    "unrelated": "Sans rapport",
}
SIM_METRICS = [("exact_match", "Correspondance exacte"), ("bleu", "BLEU"),
               ("rouge_l", "ROUGE-L"), ("cosine", "Similarité cosinus")]

_LATEX_ESCAPES = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
                  "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
                  "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}

def tex(s: str) -> str:
    return "".join(_LATEX_ESCAPES.get(ch, ch) for ch in str(s))

def read_csv(path: Path) -> list[dict] | None:
    if not path.exists():
        print(f"[skip] {path.relative_to(REPO_ROOT)} not found")
        return None
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_table(name: str, colspec: str, header: list[str], body: list[list[str]]) -> None:
    lines = [rf"\begin{{tabular}}{{{colspec}}}", r"\toprule",
             " & ".join(header) + r" \\", r"\midrule"]
    lines += [" & ".join(row) + r" \\" for row in body]
    lines += [r"\bottomrule", r"\end{tabular}", ""]
    out = TABLE_DIR / name
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out.relative_to(REPO_ROOT)}")

def perplexity_outputs() -> None:
    rows = read_csv(RESULTS / "perplexity" / "perplexity.csv")
    if not rows:
        return
    names = [Path(r["file"]).stem for r in rows]
    ppl = [float(r["ppl"]) for r in rows]
    ci = [float(r["ci"]) for r in rows]

    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.bar(names, ppl, yerr=ci, capsize=4, color="#4C72B0")
    ax.set_yscale("log")
    ax.set_ylabel("Perplexité (échelle log)")
    ax.set_xlabel("Fichier du corpus")
    ax.grid(axis="y", which="both", alpha=0.3)
    fig.tight_layout()
    out = FIG_DIR / "week1_perplexity.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"Wrote {out.relative_to(REPO_ROOT)}")

    write_table("week1_perplexity.tex", "lrrrr",
                ["Fichier", "Perplexité", r"$\pm$", "Entropie croisée (bits)",
                 "Entropie croisée (nats)"],
                [[tex(r["file"]), f"{float(r['ppl']):.4f}", f"{float(r['ci']):.4f}",
                  f"{float(r['cross_entropy_bits']):.3f}",
                  f"{float(r['cross_entropy_nats']):.3f}"] for r in rows])

def similarity_outputs() -> None:
    rows = read_csv(RESULTS / "similarity" / "similarity.csv")
    if not rows:
        return
    rows.sort(key=lambda r: (CATEGORY_ORDER.index(r["category"]), int(r["pair_id"])))

    # x positions: one slot per pair, an empty slot between categories
    xs, cat_spans, x, prev = [], {}, 0, None
    for r in rows:
        if prev is not None and r["category"] != prev:
            x += 1
        xs.append(x)
        cat_spans.setdefault(r["category"], []).append(x)
        prev = r["category"]
        x += 1

    width = 0.2
    fig, ax = plt.subplots(figsize=(10, 4))
    for j, (key, label) in enumerate(SIM_METRICS):
        offs = [xi + (j - 1.5) * width for xi in xs]
        ax.bar(offs, [float(r[key]) for r in rows], width, label=label)
    ax.set_xticks(xs, [f"P{r['pair_id']}" for r in rows], fontsize=8)
    for cat, span in cat_spans.items():
        ax.text(sum(span) / len(span), -0.16, CATEGORY_FR[cat], ha="center",
                va="top", transform=ax.get_xaxis_transform(), fontsize=9)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.legend(ncol=4, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, 1.15))
    ax.grid(axis="y", alpha=0.3)
    fig.subplots_adjust(bottom=0.22, top=0.85)
    out = FIG_DIR / "week1_similarity.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"Wrote {out.relative_to(REPO_ROOT)}")

    write_table("week1_similarity.tex", "lp{3.4cm}p{3.4cm}crrr",
                ["Paire", "Référence", "Réponse", "Exacte", "BLEU", "ROUGE-L", "Cosinus"],
                [[f"P{r['pair_id']} ({tex(CATEGORY_FR[r['category']])})",
                  tex(r["reference"]), tex(r["response"]),
                  "Oui" if r["exact_match"] == "1" else "Non",
                  f"{float(r['bleu']):.3f}", f"{float(r['rouge_l']):.3f}",
                  f"{float(r['cosine']):.3f}"] for r in rows])

def pass_at_k_outputs() -> None:
    rows = read_csv(RESULTS / "functional" / "pass_at_k.csv")
    if not rows:
        return
    body = []
    for r in rows:
        name = "Moyenne" if r["problem_id"] == "MEAN" else rf"\texttt{{{tex(r['problem_id'])}}}"
        body.append([name, r["c"], r["n"], f"{float(r['pass@1']):.3f}",
                     f"{float(r['pass@5']):.3f}"])
    write_table("week1_pass_at_k.tex", "lrrrr",
                ["Problème", "$c$", "$n$", "pass@1", "pass@5"], body)

def main() -> None:
    FIG_DIR.mkdir(exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    perplexity_outputs()
    similarity_outputs()
    pass_at_k_outputs()

if __name__ == "__main__":
    main()
