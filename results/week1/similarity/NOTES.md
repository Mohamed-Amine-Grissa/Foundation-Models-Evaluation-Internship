# Limitations of the Week 1 similarity results

1. **Few pairs per category.** 16 pairs in total: 3 near_duplicate,
   4 paraphrase, 6 meaning_flip, 3 unrelated (`data/similarity_pairs.csv`).

2. **One embedding model.** All cosine values come from a single model,
   nomic-embed-text-v1.5, quantized to Q4_K_M, served by llama-server. The
   `"search_document: "` prefix was applied to both the reference and the
   response.

3. **Non-zero cosine baseline.** The three unrelated pairs score a cosine
   similarity of 0.52 to 0.62 (`similarity.csv`, P13–P15), not 0.
