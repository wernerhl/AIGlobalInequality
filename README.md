# AI Capital and the Crowding Out of Development Investment

Werner Hernani-Limarino (AI Analytics and Bolivian Academy of Economic Sciences)

A two-sector model in which AI capital complements skilled labor, development capital (health, schooling, infrastructure, climate adaptation, humanitarian capacity) complements unskilled labor, both are financed from a common pool, and funders appropriate only part of the return to development capital.

## Contents

- `paper/ai_crowdout.tex`: manuscript (AEA template)
- `paper/ai_crowdout.pdf`: compiled manuscript
- `paper/refs.bib`: bibliography
- `paper/AEA.cls`, `paper/aea.bst`, `paper/multicol.sty`, `paper/setspace.sty`: AEA template files

## Build

```
cd paper
pdflatex ai_crowdout && bibtex ai_crowdout && pdflatex ai_crowdout && pdflatex ai_crowdout
```
