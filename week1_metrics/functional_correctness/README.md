# Functional correctness

**Question:** how often do the local generator models write Python functions
that actually pass unit tests, measured as pass@1 and pass@5, and how do the
failing samples fail?

## Run

Start the chat llama-server on `chat_port` from `config.toml`, serving one of
the models listed in `llama_cpp.generators`, then from the repo root:

```bash
python week1_metrics/functional_correctness/run_functional.py --model <gguf file>
```

`--model` defaults to `chat_model` (Qwen2.5-1.5B-Instruct). The script checks
that the server is serving that model and refuses to run otherwise.

For each of the 6 problems in `data/code_problems.json`, generates 5 samples
(temperature 0.8, seeds 1000–1004) with the system prompt in
`prompts/week1_functional_system_v1.txt`, extracts the first fenced code block,
and runs it with the problem's asserts in a fresh Python subprocess (temp dir,
5 s timeout). A sample passes only if every assert passes.

pass@k uses the unbiased estimator of Chen et al. (2021):
`pass@k = 1 - C(n-c, k) / C(n, k)` with `n` samples and `c` passing.
With n = 5, pass@5 is 1 if at least one sample passed and 0 otherwise.

Then classify the failing samples of every model:

```bash
python week1_metrics/functional_correctness/classify_failures.py
```

Each failing sample gets exactly one category, first match wins:

1. no code extracted: no complete fenced block (opening and closing fence),
   so the raw reply was executed; a reply with an unclosed fence counts here
2. timeout
3. crash/exception: loading the code raised anything (including
   `SyntaxError`, or `AssertionError` from asserts the model wrote into its own
   reply), or a tested call raised an exception other than `AssertionError`
4. wrong output format: a return value that breaks the format rules stated in
   the prompt (wrong type or shape, e.g. a run-length string that is not
   character+count pairs)
5. logic error: right format, wrong value

## Writes

Per model, in `results/week1/functional/<model file stem>/`:

- `samples.jsonl` — every reply, extracted code, outcome (`pass` / `fail` / `timeout`) and error line
- `pass_at_k.csv` — `problem_id, n, c, pass@1, pass@5`, plus a `MEAN` row (n, c are totals; pass@k is the mean over problems)
- `run_log.json` — model filename and hash, llama.cpp build, prompt version, seeds, temperature, SHA-256 of `code_problems.json`
- `failures.csv` — one row per failing sample: category and the first offending return value or error

Across models: `results/week1/functional/failure_counts.csv`.
