# Labeling rubric v1 — final-answer correctness

This rubric is used, unchanged, by the human labeler and by the AI judge.

- **Task:** decide whether a model's response to one question from
  `data/task/questions.jsonl` gives the correct final answer.
- **Criterion:** correctness of the final answer only, checked against the
  question's `reference_answer` and `accepted_variants` (reference-based
  evaluation).
- **Scoring system:** binary classification, exactly one label per response:
  `correct` or `incorrect`.

The labeler (human or judge) sees: the question, the reference answer, the
accepted variants, and the full response.

## 1. Identify the final answer

The final answer is the single answer the response commits to, found in this
order:

1. an answer explicitly marked as final ("Final answer: …", "The answer is …",
   "**Answer:** …");
2. otherwise, the last answer to the question stated in the response.

If the response first states one answer and later explicitly corrects it
("…so 30 cents. Wait, that's wrong: the ball costs 15 cents."), the corrected,
later answer is the final answer.

If no final answer can be identified, the label is `incorrect`.

## 2. Compare it with the reference

The final answer is `correct` if it expresses **the same value** as the
`reference_answer`. The `accepted_variants` are examples of acceptable forms,
not an exhaustive list: an unlisted form that follows the rules below is also
`correct`.

Same value, accepted:

- letter case, surrounding whitespace, and surrounding punctuation or
  formatting (quotes, bold, a final full stop) are ignored;
- a number may be written in digits or in words ("6" = "six");
- a number may carry trailing zeros or a decimal point that do not change its
  value ("66" = "66.0" = "66.00");
- **the same value in an equivalent unit or format is correct**, whether or not
  it is listed: "15", "15 cents", "$0.15" and "0.15 dollars" are the same
  answer to a question asking for cents; "12:35" and "12:35 pm" are the same
  time; the unit may also be omitted when the question names it.

Not the same value, `incorrect`:

- a **different value**, including a rounded or approximate one ("about 22"
  or "23" for 22.50 is `incorrect`; "22.5" is `correct` because it is the
  same value);
- a **missing value**: a unit, a method or a formula without the value itself
  ("it costs some cents", "multiply 6 by 2.5");
- for names and words, a **misspelled** or **partial** form, unless it is
  listed in `accepted_variants` ("Austen" is accepted for f04 because it is
  listed; "Jane" or "Jane Austin" would not be).

## 3. Specific cases

| Case | Label |
| --- | --- |
| Correct final answer, correct reasoning | `correct` |
| **Correct final answer, wrong or missing reasoning** | `correct` — only the final answer is scored. The labeler may record the flawed reasoning in the note (section 4); the note never changes the label. |
| Wrong final answer, even with mostly correct reasoning | `incorrect` |
| **Extra text** (explanation, working, restating the question, pleasantries) around a correct final answer | `correct`, as long as the extra text does not state a different final answer |
| **Hedging** on a single answer ("I think it's 36", "probably Canberra") | judged on that answer: `correct` if it matches |
| **Multiple answers**: the response offers two or more different candidate final answers without committing to one ("either 15 or 30 cents", "Sydney or Canberra") | `incorrect`, even if one of them is right |
| Intermediate values in the working, followed by one committed final answer | judged on the committed final answer only |
| **Refusal**, "I don't know", or a request for clarification instead of an answer | `incorrect` |
| Response cut off or empty before any final answer | `incorrect` |
| Answers a different question than the one asked | `incorrect` |

## 4. Output

One label per response: `correct` or `incorrect`.

Optionally, a short free-text **note**, for example to record flawed reasoning
behind a correct final answer. The note is for later analysis only: it never
changes the label, and only the label is scored.

Human labels and judge labels
are later compared sample by sample; that comparison measures **agreement**
between the two labelers, which is different from correlation and from the
judge's accuracy, and is reported as such.
