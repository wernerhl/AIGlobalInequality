# AI Capital and the Crowding Out of Development Investment

Werner Hernani-Limarino (AI Analytics and Bolivian Academy of Economic Sciences)

A two-sector model in which AI capital complements skilled labor, development capital (health, schooling, infrastructure, climate adaptation, humanitarian capacity) complements unskilled labor, both are financed from a common pool, and funders appropriate only part of the return to development capital.

## Contents

- `paper/ai_crowdout.tex`: theoretical manuscript (AEA template)
- `paper/ai_crowdout.pdf`: compiled theoretical manuscript
- `paper/ai_boom_development_finance.tex`: descriptive companion paper, "Abundant Capital, Scarce Appropriability: Development Finance during the AI Investment Boom"
- `paper/ai_boom_development_finance.pdf`: compiled descriptive paper
- `paper/figures/`: figures produced by the empirical pipeline
- `paper/refs.bib`: bibliography
- `paper/AEA.cls`, `paper/aea.bst`, `paper/multicol.sty`, `paper/setspace.sty`: AEA template files

## Build

```
cd paper
pdflatex ai_crowdout && bibtex ai_crowdout && pdflatex ai_crowdout && pdflatex ai_crowdout
pdflatex ai_boom_development_finance && bibtex ai_boom_development_finance && pdflatex ai_boom_development_finance && pdflatex ai_boom_development_finance
```

## Empirics

`empirics/` contains a data pipeline for the testable predictions in Section IV: SEC EDGAR capex and earnings-release dates for the AI firms, Yahoo prices and EPS surprises, FRED rates and ICE BofA EM spreads, Ken French factors, the constructed AI return shocks, and first-pass event-day regressions. See `empirics/README.md` and `empirics/output/results.md`.
