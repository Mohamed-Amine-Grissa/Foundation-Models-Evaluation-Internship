# Notes on the Week 1 functional-correctness results

## Code-extraction rules

- **Strict (primary result).** Used by `run_functional.py` for every
  `pass_at_k.csv`, `failures.csv` and the tables in `report/generated/`: the
  code is the first complete fenced block (opening and closing ```). If there
  is none, the raw reply is executed.
- **Lenient (sensitivity analysis only).** Used by
  `sensitivity_unclosed_fence.py` on the saved replies; nothing was generated
  again. Same as strict when a complete block exists; otherwise, if the reply
  contains an opening fence, the code is everything after that fence line.
  Results: `sensitivity_unclosed_fence/`.

Three replies have an opening fence and no closing fence: Llama-3.2-3B
fizzbuzz sample 1, Llama-3.2-3B second_largest sample 1, Qwen2.5-0.5B
run_length_encode sample 2. Under the strict rule all three fail with
`SyntaxError` and are classified "no code extracted". Under the lenient rule
Llama-3.2-3B second_largest sample 1 passes; the other two still fail
(`AssertionError`).

| Model | pass@1 strict (c/n) | pass@1 lenient (c/n) |
|---|---|---|
| Qwen2.5-1.5B | 0.800 (24/30) | 0.800 (24/30) |
| Qwen2.5-0.5B | 0.267 (8/30) | 0.267 (8/30) |
| Llama-3.2-3B | 0.833 (25/30) | 0.867 (26/30) |

The model ranking is the same under both rules.

## finish_reason of the three unclosed-fence replies

`finish_reason` was not saved: `run_functional.py` keeps only the reply text,
not the raw server response, so it cannot be read from the results. Generated
token counts were recovered without generating anything:

| Reply | Generated tokens | Source |
|---|---|---|
| Llama-3.2-3B fizzbuzz s1 | 98 | llama-server log of the Llama-3.2-3B run |
| Llama-3.2-3B second_largest s1 | 43 | llama-server log of the Llama-3.2-3B run |
| Qwen2.5-0.5B run_length_encode s2 | 304 (+1 end token) | saved reply re-tokenised with the model's tokenizer (`llama-tokenize`); the server log of that run was overwritten |

The server-log counts were matched to samples by request order and checked by
re-tokenising the saved replies, which gives exactly 1 token less than the log
in every checked case (the log includes the end-of-generation token). All three
are well below `max_tokens = 512`, which is consistent with "stop", not
"length"; this is inferred from token counts, not read from `finish_reason`.

## Limitations

- 6 problems.
- n = 5 samples per problem.
- Temperature 0.8 (seeds 1000–1004).
- One prompt set (`data/code_problems.json`, SHA-256
  `c5888d4c31398ca589edff2d05fe4ac976f59a620d5265dde9925100acadb703`) and one
  system prompt (`prompts/week1_functional_system_v1.txt`).
- Under the strict rule, Llama-3.2-3B (25/30) and Qwen2.5-1.5B (24/30) differ
  by 1 passing sample out of 30.
