# Foundation-Models-Evaluation-Internship

![Python](https://img.shields.io/badge/python-3.14-3776AB?logo=python&logoColor=white)
![llama.cpp](https://img.shields.io/badge/inference-llama.cpp-black)
![CPU only](https://img.shields.io/badge/hardware-CPU--only-lightgrey)
![Models](https://img.shields.io/badge/models-GGUF_Q4__K__M-FFD21E?logo=huggingface&logoColor=black)
![Report](https://img.shields.io/badge/report-LaTeX_(FR)-008080?logo=latex&logoColor=white)
![Last commit](https://img.shields.io/github/last-commit/Mohamed-Amine-Grissa/Foundation-Models-Evaluation-Internship)
![Repo size](https://img.shields.io/github/repo-size/Mohamed-Amine-Grissa/Foundation-Models-Evaluation-Internship)

Hands-on experiments in evaluating and prompting local LLMs, following Chapters 3–5 of Chip Huyen's AI Engineering. Perplexity, lexical and semantic similarity, functional correctness, LLM-as-a-judge, evaluation pipelines and prompt-injection tests, all run CPU-only with llama.cpp.

## Requirements

- Python 3.14 (tested on 3.14.3)
- llama.cpp built separately from <https://github.com/ggml-org/llama.cpp>
  (not included in this repo)
- Models downloaded with the Hugging Face `hf` CLI into llama.cpp's models
  folder: Qwen2.5-1.5B-Instruct (Q4_K_M GGUF) and nomic-embed-text-v1.5
  (Q4_K_M GGUF)

## Setup

1. `python -m venv .venv`
2. Activate it, then `pip install -r requirements.txt`
3. Confirm `config.toml` paths match your local llama.cpp install
4. Start the chat and embedding llama-server instances on the ports in
   config.toml before running any week2+ scripts

## Repository structure

- `common/` — shared Python utilities (LLM client, metrics, run logging)
- `data/` — input data, including the Week 1 corpus in `data/corpus/`
- `prompts/` — prompt templates used by the experiments
- `scripts/` — helper scripts
- `week1_metrics/` — Week 1: perplexity, exact match, lexical and semantic
  similarity, functional correctness of generated code
- `week2_judge/` — Week 2: LLM-as-a-judge checked against my own labels
  (agreement rate, disagreement analysis), plus pairwise comparison and
  Elo-style ranking of two local models
- `week3_pipeline/` — Week 3: evaluation pipeline combining a metric, the
  judge, and cost/latency into one scorecard across models or prompt variants
- `week4_prompting/` — Week 4: zero-shot vs. few-shot vs. chain-of-thought,
  scored with the Week 3 pipeline
- `week5_capstone/` — Week 5: prompt-injection tests (naive vs. hardened
  system prompt) and re-calibration of the Week 2 judge on the same gold set
- `results/` — experiment outputs, one subfolder per week
- `figures/` — generated figures
- `report/` — internship report (LaTeX, in French) and Zotero bibliography

## Note on references

`references/book-excerpts/` is intentionally not included in this repository:
it holds excerpts of a copyrighted book and is excluded via `.gitignore`.
