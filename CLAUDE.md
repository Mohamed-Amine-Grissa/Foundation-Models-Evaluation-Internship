# Project rules
- The report is in FRENCH, built on the LaTeX template in report/ (I will add it
  myself). Do not alter the template's layout once it's there.
- Never invent or estimate a number. Every figure/table in the report comes from
  files in results/. If a result is missing, write "À compléter" in the report and
  list it in TODO_RESULTS.md.
- Never conflate agreement with correlation, or either with accuracy, anywhere in
  code comments, docs, or report text.
- Report negative or surprising results honestly (e.g. a cosine similarity that
  contradicts the expected pattern) — do not rerun an experiment to force an
  expected result.
- Do not refactor working experiment scripts beyond moving them; use `git mv`.
- Generated tables/figures go to report/generated/ and are \input'ed into the
  LaTeX source, never retyped by hand.
- Paraphrase from references/book-excerpts/ when writing report prose about
  concepts — never copy multi-sentence passages verbatim.
- After each report chapter is written, compile with latexmk and fix errors
  before continuing.
- Model paths, ports, and local environment facts live in config.toml — read
  from there, never hardcode a path.
