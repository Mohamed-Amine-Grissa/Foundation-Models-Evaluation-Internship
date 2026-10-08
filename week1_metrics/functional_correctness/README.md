# Functional correctness

**Question:** how often does the chat model (Qwen2.5-1.5B-Instruct) write Python
functions that actually pass unit tests, measured as pass@1 and pass@5?

## Run

Start the chat llama-server on `chat_port` from `config.toml`, then from the
repo root:

```
python week1_metrics/functional_correctness/run_functional.py
```

For each of the 6 problems in `data/code_problems.json`, generates 5 samples
(temperature 0.8, seeds 1000–1004) with the system prompt in
`prompts/week1_functional_system_v1.txt`, extracts the first fenced code block,
and runs it with the problem's asserts in a fresh Python subprocess (temp dir,
5 s timeout). A sample passes only if every assert passes.

pass@k uses the unbiased estimator of Chen et al. (2021):
`pass@k = 1 - C(n-c, k) / C(n, k)` with `n` samples and `c` passing.
With n = 5, pass@5 is 1 if at least one sample passed and 0 otherwise.

## Writes

- `results/week1/functional/samples.jsonl` — every reply, extracted code, outcome (`pass` / `fail` / `timeout`) and error line
- `results/week1/functional/pass_at_k.csv` — `problem_id, n, c, pass@1, pass@5`, plus a `MEAN` row (n, c are totals; pass@k is the mean over problems)
- `results/week1/functional/run_log.json` — model hash, llama.cpp build, prompt version, seeds, temperature
