# Reusable Report Template

A stripped-down version of the Nexus report, kept generic so you can reuse it for
any internship/project report and just fill in the details each year.

## Structure

```
main.tex                     -> master file, compile this one
guard.tex                    -> cover page (title, name, company, supervisors)
Dedications.tex              -> optional dedications page (delete + remove the
                                 \include{Dedications} line in main.tex if unused)
remerciment.tex              -> acknowledgments page
Acronymes.tex                -> list of acronyms
general_introduction.tex     -> general introduction (unnumbered chapter)
Chapter1/Chapter1.tex        -> Context Presentation (company, project, objectives)
Chapter2/Chapter2.tex        -> Development Environment and Methodology
Chapter3/Chapter3.tex        -> Requirements Analysis and System Design
Chapter4/Chapter4.tex        -> Implementation and Features (one section per feature)
Chapter5/Chapter5.tex        -> Testing and Continuous Integration
Conclusion.tex                -> general conclusion (unnumbered chapter)
Resume.tex                   -> standalone one-page abstract (compiles separately)
LogoUSo.jpg, ISSAT.png       -> institution logos (kept, reusable every year)
ChapterN/images/             -> empty folders, put that year's screenshots/diagrams here
```

## How to use it each year

1. Copy this whole folder to a new location (or `git clone` a fresh copy).
2. Search the project for `[` and `TODO` (every editor can do this) and fill in
   every placeholder: your name, company, supervisors, and the actual content of
   each chapter.
3. Drop screenshots/diagrams into the matching `ChapterN/images/` folder and
   reference them in the `Screens` subsections of Chapter 4 (see the commented
   example in `Chapter4/Chapter4.tex`).
4. Chapter 4 is built around a copy-paste pattern: one `\section` per
   feature/module, each with a `Delivered Features` and a `Screens` subsection.
   Duplicate the block for as many features as you have.
5. Delete anything you don't need (e.g. `Dedications.tex`, the Security
   Requirements section in Chapter 3, or the CI/CD section in Chapter 5) --
   remember to also remove the matching `\include{...}` line in `main.tex` if
   you delete a whole file.
6. Compile with `latexmk -pdf main.tex`. The bibliography uses `biblatex` and
   Biber; `latexmk` runs the required steps automatically. To compile manually,
   run `pdflatex main.tex`, `biber main`, then `pdflatex main.tex` twice.

## Notes

- The preamble in `main.tex` (packages, fonts, colors, header/footer style) is
  untouched from the original report -- keep it as-is unless you want to change
  the visual style.
- `\minitoc` at the top of each chapter needs two compile passes to show up
  correctly; that's normal.
- The chapter *titles* (e.g. "Context Presentation") are generic on purpose --
  rename them to whatever fits your actual report (e.g. "Internship Context
  Presentation", "PFE Context Presentation") in each `ChapterN/ChapterN.tex`
  and in the outline listed in `general_introduction.tex`.

## Bibliography

- References are stored in `LLM_Evaluation_Sources_Used.bib` and appear after the
  conclusion under **Bibliographie**, with an entry in the table of contents.
- `\nocite{*}` in `main.tex` includes every source, even before you cite it in the
  report. Remove that command if you later want only cited references to appear.
- Cite a source using its key, for example `\cite{geron_hands-machine_nodate}`
  or `\cite{zhang_bertscore_2020}`. Keep original publication titles in their
  original language.
- Duplicate exports of MTEB, ROUGE, and the Brown et al. paper are merged. The
  review and meta-review remain separate entries; the latter uses the key
  `noauthor_metareview_nodate`.
