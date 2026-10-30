# The book's examples

Pemmaraju and Skiena, *Computational Discrete Mathematics: Combinatorics and
Graph Theory with Mathematica* (Cambridge University Press, 2003), comes with
notebooks of its examples. This directory turns them into the tests in
`test/test_book_examples.py`, with WMA's results as the expected ones.

- `cells/NB.json`: the input cells of each notebook, as `{"sec": section, "in": "HoldComplete[...]"}`. The notebooks are
  `Chapter3`, `Chapter4`, `Chapter5`, `newFeatures` ("New Features") and
  `tutorial` ("A Mathematica Tutorial for Combinatorica Users").
- `wma/NB.s1.jsonl`, `wma/NB.s2.jsonl`: every cell's result under WMA 15 with its own Combinatorica, with
  `SeedRandom[1]` and `SeedRandom[2]`. A cell whose result differs between the two seeds is random.
- `mathics/NB.jsonl`: the same cells under Mathics3, with this package. Each cell's time decides whether the
  tests evaluate it.
- `make_tests.py`: writes `test/data/book/NB.json` from the three. Each cell is checked against WMA,
  evaluated without a check (it is random, times something, or does not give WMA's result yet), or
  skipped (usage text, failed or too slow in `mathics/`). A cell that uses a symbol a skipped cell
  assigns is skipped too, and one that uses a symbol a slower cell assigns counts that cell's time.
  The cells in `xfail.json` are expected to fail, with the reason.

The results come from these harnesses:

- `run_wma.sh OUTDIR TIMEOUT`: runs every cell under `wolframscript`, using `run_wma.wls` and `drive_wma.py`.
- `run.sh OUTDIR TIMEOUT`: runs every cell under Mathics3, using `run_mathics.py` and `drive_mathics.py`.
  Each cell gets the time limit. After a hang the process restarts and replays the earlier cells.
- `compare.py WMA_DIR MATHICS_DIR [OUT.json]`: the share of cells that give WMA's result, per notebook.

To refresh the tests after Mathics3 or the package changes:

    bash book/run.sh /tmp/book 120
    python3 book/compare.py book/wma /tmp/book          # how many cells pass now
    cp /tmp/book/*.jsonl book/mathics/
    python3 book/make_tests.py book/wma book/mathics

By default the tests evaluate the cells that took at most 1 s in `mathics/`. To go further, set
`COMBINATORICA_BOOK_SECS` (for example to 5).
