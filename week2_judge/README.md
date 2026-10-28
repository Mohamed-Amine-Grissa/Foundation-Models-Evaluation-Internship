# Week 2 — AI as a judge

**Question:** how often does a local AI judge (Phi-3.5-mini) give the same
correct / incorrect label as my own labels, on responses from three local
generators to the shared task (`data/task/questions.jsonl`), with both labelers
following the same rubric (`prompts/rubric_v1.md`)?

## Step 2 — generate responses and the blind labeling sheet

For each generator, start the chat llama-server on `chat_port` from
`config.toml` serving that model, then from the repo root:

```bash
python week2_judge/generate_responses.py --model qwen2.5-1.5b-instruct-q4_k_m.gguf
python week2_judge/generate_responses.py --model qwen2.5-0.5b-instruct-q4_k_m.gguf
python week2_judge/generate_responses.py --model Llama-3.2-3B-Instruct-Q4_K_M.gguf
```

One response per question per model: temperature 0.7, seed 42, `max_tokens`
512, system prompt `prompts/week2_generator_system_v1.txt` (asks for a final
line "Final answer: …"). The script refuses to run if the server serves a
different model. `finish_reason` and the completion token count are saved for
every response.

Then build the sheet:

```bash
python week2_judge/build_labeling_sheet.py
```

The 60 responses (20 questions × 3 generators, so each question appears
3 times) are shuffled (seed 42). Each row shows the question,
reference answer, accepted variants and response, which is what the rubric
says the labeler sees. The generating model is not in the sheet.

## Step 3 — label the sheet

```bash
python week2_judge/label.py
```

Shows one row at a time (row id, question, reference answer, accepted
variants, response) and asks for `c` (correct) / `i` (incorrect) and an
optional note. Each label is written to `to_label.csv` immediately; `q` or
Ctrl+C quits, and the next run resumes at the first unlabeled row. The tool
only reads `to_label.csv`, never `answer_key.json` or `results/week2/responses/`.
Close the CSV in Excel while labeling, or the write fails.

## Step 4 — run the judge

```bash
.venv\Scripts\python.exe week2_judge/run_judge.py
```

Starts the chat llama-server with `judge_model` (Phi-3.5-mini), judges all 60
rows and stops the server. Temperature 0, seed 42, `n_predict` 256, prompt
`prompts/judge_v1.txt` (contains the full `prompts/rubric_v1.md`; v1 is frozen,
later versions get a new file). The judge sees only the question, reference
answer, accepted variants and response columns of `to_label.csv`, never
`human_label`, `human_note` or `answer_key.json`.

Output is constrained to `{"verdict": "correct" | "incorrect", "reason": …}`
with a JSON schema. On this llama-server build, `response_format` on
`/v1/chat/completions` fails for Phi-3.5 ("Unexpected empty grammar stack"),
so the script formats the prompt with the server's chat template
(`/apply-template`) and calls `/completion` with `json_schema`. Outputs are
still parsed and parse failures counted.

## Step 5 — agreement

```bash
.venv\Scripts\python.exe week2_judge/agreement.py
```

Raw agreement rate, Cohen's kappa and the judge-vs-human confusion matrix,
overall, per question category and per generator. These measure agreement
between two labelers, not the judge's accuracy. Rows with no human label, an
unmapped label or a judge parse failure are listed and excluded. Kappa is
`n/a` when expected agreement is 1 (both labelers gave one label to every row
of the subset).

## Writes

- `results/week2/responses/<model>.jsonl` — question, response, `finish_reason`, completion tokens, sampling settings
- `results/week2/responses/<model>.run_log.json` — model filename and hash, llama.cpp build, prompt version, seed, SHA-256 of the questions file
- `results/week2/labeling/to_label.csv` — the blind sheet; fill in `human_label` (`correct` / `incorrect`) and optionally `human_note`, with `label.py` or by hand
- `results/week2/labeling/answer_key.json` — row → question id, model, `finish_reason`
- `results/week2/judge/judge_v1.jsonl` — per row: verdict, reason, raw output, parse error, stop type
- `results/week2/judge/judge_v1.run_log.json` — judge model hash, llama.cpp build, prompt/rubric hashes, schema, parse failures
- `results/week2/judge/agreement.json`, `agreement_table.md` — agreement statistics and label mapping
- `results/week2/judge/disagreements.csv` — every row where judge and human differ, with model
- `report/generated/week2_agreement.tex` — the agreement table for the report

## Keeping the labeling blind

Label every row of `to_label.csv` before opening `answer_key.json` or the
files in `results/week2/responses/`: both reveal which model wrote each
response.
