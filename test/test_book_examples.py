# -*- coding: utf-8 -*-
"""
The examples of Pemmaraju and Skiena's *Computational Discrete Mathematics:
Combinatorics and Graph Theory with Mathematica*, from the book's notebooks
(Chapters 3 to 5, and the notebooks "New Features" and "A Mathematica Tutorial
for Combinatorica Users"), checked against the results WMA gives.

The cells of each notebook are evaluated in order in one session, since
later cells use what earlier ones define. A cell whose WMA result is
deterministic is checked against it ("check"); the others are evaluated
but not checked ("run"). The data, in test/data/book/, is made by
book/make_tests.py; see book/README.md.

Only the cells that took at most COMBINATORICA_BOOK_SECS seconds (default
1) in the reference Mathics3 run are evaluated, and each one is stopped
after CELL_TIMEOUT seconds: a cell can take much longer than in the
reference run when an earlier cell it builds on was left out.
"""

import json
import os
import os.path as osp
import re
import signal
from test.helper import evaluate, reset_session, session

import pytest
from mathics.core.interrupt import TimeoutInterrupt

combinatorica_file = osp.normpath(
    osp.join(osp.dirname(__file__), "..", "Combinatorica", "CombinatoricaV201.m")
)
data_dir = osp.join(osp.dirname(__file__), "data", "book")
NOTEBOOKS = ["Chapter3", "Chapter4", "Chapter5", "newFeatures", "tutorial"]
MAX_SECS = float(os.environ.get("COMBINATORICA_BOOK_SECS", "1"))
CELL_TIMEOUT = 30

# The result of a cell as the WMA run recorded it: graphics by their head
# only, reals rounded to 5 decimal places, at most 4000 characters of
# FullForm.
CANON = r"""Book`canon[r_] := Which[
   MatchQ[r, _Graphics | _Graphics3D | _GraphicsArray | _Image],
     "<" <> SymbolName[Head[r]] <> ">",
   True, Module[{s = ToString[FullForm[r /. x_Real :> Round[10^5 x]]]},
     If[StringLength[s] > 4000, StringTake[s, 4000] <> "...", s]]]"""


def braces(s: str) -> str:
    """Turn FullForm List[...] into {...}."""
    out, stack, i, n = [], [], 0, len(s)
    while i < n:
        c = s[i]
        if c == '"':
            j = i + 1
            while j < n and s[j] != '"':
                j += 2 if s[j] == "\\" else 1
            out.append(s[i : j + 1])
            i = j + 1
            continue
        if s.startswith("List[", i) and (
            i == 0 or not (s[i - 1].isalnum() or s[i - 1] in "`$")
        ):
            out.append("{")
            stack.append("}")
            i += 5
            continue
        if c == "[":
            stack.append("]")
        elif c == "]":
            c = stack.pop() if stack else c
        out.append(c)
        i += 1
    return "".join(out)


def norm(s: str) -> str:
    return re.sub(r"\s+", "", braces(s))


def cells():
    for nb in NOTEBOOKS:
        for cell in json.load(open(osp.join(data_dir, f"{nb}.json"))):
            if cell["mode"] == "skip" or cell.get("secs", 0) > MAX_SECS:
                continue
            marks = []
            if "xfail" in cell:
                marks.append(pytest.mark.xfail(reason=cell["xfail"], strict=False))
            yield pytest.param(nb, cell, id=f"{nb}-{cell['i']}", marks=marks)


_loaded_notebook = None


@pytest.mark.parametrize(("notebook", "cell"), list(cells()))
def test_book_example(notebook, cell):
    global _loaded_notebook
    if _loaded_notebook != notebook:
        # A fresh session with the package for each notebook.
        reset_session()
        evaluate(f'Get["{combinatorica_file}"]')
        evaluate(CANON)
        _loaded_notebook = notebook
    # A cell may hold several expressions: all are evaluated, in order, and
    # the last one is the result. The session's own timeout stops the
    # evaluation between steps; the alarm is a backstop for Mathics3
    # versions that do not honor it.
    def on_alarm(signum, frame):
        raise TimeoutInterrupt()

    previous = signal.signal(signal.SIGALRM, on_alarm)
    signal.alarm(CELL_TIMEOUT + 10)
    try:
        result = session.evaluate_as_in_cli(
            f"Book`canon[Last[List @@ {cell['in']}]]", timeout=CELL_TIMEOUT
        )
    except TimeoutInterrupt:
        if cell["mode"] != "check":
            return
        pytest.fail(f"{notebook} cell {cell['i']} took more than {CELL_TIMEOUT} s")
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
    if cell["mode"] != "check":
        return
    out = result.result
    if isinstance(out, str) and out.startswith('"'):
        out = out[1:-1]
    assert norm(str(out)) == cell["expected"], (
        f"{notebook} cell {cell['i']} ({cell['section']}):\n"
        f"  {cell['in']}\ngives\n  {out}\nWMA gives\n  {cell['expected']}"
    )
