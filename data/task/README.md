# Shared task (Weeks 2–5)

`questions.jsonl` holds 20 English questions, each with one unambiguous
correct final answer: 7 factual short-answer (`f01`–`f07`), 9 multi-step word
problems (`w01`–`w09`, 2–4 steps of arithmetic or logic) and 4 trap questions
with a tempting wrong answer (`t01`–`t04`).

Fields: `id`, `category`, `question`, `reference_answer`, `accepted_variants`.
`accepted_variants` are examples of acceptable forms, not an exhaustive list;
responses are labeled with `prompts/rubric_v1.md`.

## Trap questions

`t01`, `t02` and `t03` are adapted from the Cognitive Reflection Test
(bat-and-ball, machines and widgets, lily pads). Their structure is kept but
their numbers are changed, to reduce the risk that a model answers from a
memorised version of the original puzzle.

| id | Puzzle | Reference answer | Tempting wrong answer |
| --- | --- | --- | --- |
| t01 | bat and ball, $1.30 total, bat $1.00 more | 15 cents | 30 cents |
| t02 | 6 machines / 6 minutes / 6 widgets → 90 machines, 90 widgets | 6 minutes | 90 minutes |
| t03 | lily pads double daily, whole lake in 36 days → half the lake | 35 days | 18 days |
| t04 | 17 sheep, all but 9 run away | 9 | 8 |

`t04` is not a Cognitive Reflection Test item and is unchanged.
