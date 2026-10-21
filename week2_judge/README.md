# Week 2 — AI as a judge

**Question:** how often does a local AI judge (Phi-3.5-mini) give the same
correct / incorrect label as my own labels, on responses from two local
generators to the shared task (`data/task/questions.jsonl`), with both labelers
following the same rubric (`prompts/rubric_v1.md`)?

## Step 2 — generate responses and the blind labeling sheet

For each generator, start the chat llama-server on `chat_port` from
`config.toml` serving that model, then from the repo root:

```bash
python week2_judge/generate_responses.py --model qwen2.5-1.5b-instruct-q4_k_m.gguf
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

The 40 responses are shuffled (seed 42). Each row shows the question,
reference answer, accepted variants and response, which is what the rubric
says the labeler sees. The generating model is not in the sheet.

## Writes

- `results/week2/responses/<model>.jsonl` — question, response, `finish_reason`, completion tokens, sampling settings
- `results/week2/responses/<model>.run_log.json` — model filename and hash, llama.cpp build, prompt version, seed, SHA-256 of the questions file
- `results/week2/labeling/to_label.csv` — the blind sheet; fill in `human_label` (`correct` / `incorrect`) and optionally `human_note`
- `results/week2/labeling/answer_key.json` — row → question id, model, `finish_reason`

## Keeping the labeling blind

Label every row of `to_label.csv` before opening `answer_key.json` or the
files in `results/week2/responses/`: both reveal which model wrote each
response.
