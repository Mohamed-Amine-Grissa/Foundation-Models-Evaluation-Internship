"""Exact match, lexical (BLEU/ROUGE-L), semantic (cosine) similarity, and
parsing for llama-perplexity's text output."""
import re
import math
import numpy as np
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer

_smoothie = SmoothingFunction().method4
_rouge = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')
_PPL_RE = re.compile(r'Final estimate:\s*PPL\s*=\s*([\d.]+)\s*\+/-\s*([\d.]+)')

def exact_match(a: str, b: str) -> bool:
    return a.strip().lower() == b.strip().lower()

def bleu(reference: str, response: str) -> float:
    return sentence_bleu([reference.lower().split()], response.lower().split(),
                          smoothing_function=_smoothie)

def rouge_l(reference: str, response: str) -> float:
    return _rouge.score(reference, response)['rougeL'].fmeasure

def cosine_sim(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased pass@k estimator (Chen et al., 2021): 1 - C(n-c, k) / C(n, k),
    with n samples generated and c of them passing all tests."""
    if k > n:
        raise ValueError(f"k={k} cannot exceed n={n}")
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)

def parse_perplexity_output(raw_text: str) -> dict:
    """Strips ANSI color codes and extracts the PPL value + confidence interval
    from a saved llama-perplexity.exe run."""
    clean = _ANSI_RE.sub('', raw_text)
    m = _PPL_RE.search(clean)
    if not m:
        raise ValueError("No 'Final estimate: PPL = ...' line found in output")
    ppl = float(m.group(1))
    ci = float(m.group(2))
    return {
        "ppl": ppl,
        "ci": ci,
        "cross_entropy_bits": math.log2(ppl),
        "cross_entropy_nats": math.log(ppl),
    }
