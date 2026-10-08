# Limitations of the Week 1 perplexity results

1. **Small sample per file.** With `-c 128`, llama-perplexity scored each corpus
   file on only 2 chunks of 128 tokens (see `raw/*.txt`: "calculating perplexity
   over 2 chunks, n_ctx=128"). The resulting intervals are wide, and
   `1_easy.txt` (7.3457 ± 1.4789) and `2_medium.txt` (9.0598 ± 1.4649) overlap
   within their intervals, so their ordering is not established by this run.

2. **Repetition inside `4_gibberish.txt`.** The file reuses the same word
   sequences several times: 265 words drawn from only 64 distinct words, and 39
   of its 207 distinct 4-word sequences occur more than once (e.g. "fish jumping
   quietly forty" appears 4 times). Once a sequence has appeared earlier in the
   context window, the model can predict it more easily, so in-context
   repetition likely lowers the perplexity measured for this file compared with
   gibberish that never repeats.
