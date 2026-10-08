# Perplexity

**Question:** how surprised is the chat model (Qwen2.5-1.5B-Instruct) by texts of
increasing difficulty — HTML boilerplate, easy, medium and hard prose, and
gibberish? Lower perplexity means the model predicts the text better.

## Run

From the repo root, with the venv active (no llama-server needed):

```
python week1_metrics/perplexity/run_perplexity.py
```

Runs `llama-perplexity.exe -m <chat_model> -f <file> -c 128 -t 8` on every
`data/corpus/*.txt`. Binary and model paths come from `config.toml`.

## Writes

- `results/week1/perplexity/raw/<file>.txt` — full llama-perplexity output per corpus file
- `results/week1/perplexity/perplexity.csv` — `file, ppl, ci, cross_entropy_bits, cross_entropy_nats`
- `results/week1/perplexity/run_log.json` — model hash, llama.cpp build, commands
