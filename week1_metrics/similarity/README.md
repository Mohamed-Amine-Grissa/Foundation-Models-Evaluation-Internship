# Similarity metrics

**Question:** how do exact match, lexical similarity (BLEU, ROUGE-L) and semantic
similarity (embedding cosine) behave on pairs whose relationship is known —
near-duplicates, paraphrases, meaning flips (word substitution, punctuation,
word-order swaps, negation) and unrelated sentences? In particular: which
metrics score a meaning flip as "similar"?

## Run

Start the embedding llama-server on `embed_port` from `config.toml` (with
`--embeddings`), then from the repo root:

```
python week1_metrics/similarity/run_similarity.py
```

Pairs are read from `data/similarity_pairs.csv` (`category, reference, response`).
Embeddings use the `"search_document: "` prefix expected by nomic-embed-text-v1.5.

## Writes

- `results/week1/similarity/similarity.csv` — `pair_id, category, reference, response, exact_match, bleu, rouge_l, cosine`
- `results/week1/similarity/run_log.json` — embedding model hash, llama.cpp build, prefix, port
