# llm-eval-stage

Internship track (stage d'été) applying evaluation and prompt-engineering
techniques from Chip Huyen's *AI Engineering*, Chapters 3–5, over 5 weeks.
All experiments run locally via llama.cpp (CPU-only). See config.toml for
model/binary paths and CLAUDE.md for project rules.

## Setup
1. `python -m venv .venv`
2. Activate it, then `pip install -r requirements.txt`
3. Confirm `config.toml` paths match your local llama.cpp install
4. Start the chat and embedding llama-server instances on the ports in
   config.toml before running any week2+ scripts
