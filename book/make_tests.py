"""Make the test data for test/test_book_examples.py from the book's notebook
cells, a WMA run of them and a Mathics3 run of them.

usage: make_tests.py WMA_DIR MATHICS_DIR [XFAIL.json]

WMA_DIR holds NB.s1.jsonl and NB.s2.jsonl (two random seeds) and MATHICS_DIR
holds NB.jsonl, as the harness in this directory writes them (see README.md).
XFAIL.json maps a notebook to {cell number: reason} for the cells that are
expected to fail, defaulting to book/xfail.json. Writes test/data/book/NB.json.

Each cell gets a mode:

  check  WMA's result is the expected one: the cell is deterministic (the
         same result with both seeds), does not time anything, and gave
         WMA's result in the Mathics3 run.
  run    evaluated, as later cells may need what it defines, but not checked.
  skip   not evaluated: usage text (Information[...]), a cell that could not
         be parsed, or one that failed or ran too long in the Mathics3 run.

"secs" is the time the cell took in the Mathics3 run, or longer when it
uses a symbol that an earlier, slower cell assigned: the time of that cell
then counts too, since the test leaves out the cells slower than its limit
and the symbol would be missing. A cell using a symbol that a skipped cell
assigned is skipped too.
"""

import json
import os
import re
import sys

NOTEBOOKS = ["Chapter3", "Chapter4", "Chapter5", "newFeatures", "tutorial"]
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "..", "test", "data", "book")

# Cells that time things or measure memory: their values cannot be compared.
TIMING_RE = re.compile(
    r"\b(Timing|AbsoluteTiming|ByteCount|MemoryInUse|MaxMemoryUsed|SessionTime)\["
)
# Cells slower than this in the Mathics3 run are never evaluated.
MAX_SECS = 5.0


def braces(s: str) -> str:
    """Turn WMA's FullForm List[...] into {...}, as Mathics3 prints it."""
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


def load(path):
    if not os.path.exists(path):
        return {}
    return {r["i"]: r for r in map(json.loads, open(path))}


# Symbols a cell assigns ("g = ...", "f[x_] := ...") and the symbols it uses.
ASSIGN_RE = re.compile(r"(?<![\w`$])([A-Za-z$][A-Za-z0-9$]*)\s*(?:\[[^\[\]]*\])?\s*:?=(?!=)")
# (not pattern names: the g in g_Graph)
SYMBOL_RE = re.compile(r"(?<![\w`$])[A-Za-z$][A-Za-z0-9$]*(?![A-Za-z0-9$]*_)")
STRING_RE = re.compile(r'"(?:[^"\\]|\\.)*"')


def symbols(text: str):
    """The symbols text assigns and the ones it uses."""
    text = STRING_RE.sub('""', text)
    if text.startswith("HoldComplete[") and text.endswith("]"):
        text = text[len("HoldComplete[") : -1]
    # The left-hand side of an assignment is not a use.
    return set(ASSIGN_RE.findall(text)), set(SYMBOL_RE.findall(ASSIGN_RE.sub("", text)))


def msg_names(msgs):
    return {m.group(0) for x in msgs for m in [re.search(r"(\$?\w+)::(\w+)", x)] if m}


def cell_mode(cell, w1, w2, m):
    """The mode of a cell, and why it is not checked."""
    text = cell["in"]
    if "Information[" in text:
        return "skip", "usage text"
    if text.startswith("PARSEFAIL:"):
        return "skip", "the notebook cell could not be parsed"
    if m is None or m["status"] not in ("ok", "msg"):
        return "skip", "Mathics3: %s" % (m or {}).get("status", "not run")
    if m["secs"] > MAX_SECS:
        return "skip", "Mathics3 takes %.0f s" % m["secs"]
    if w1 is None or w1["status"] in ("crash", "timeout"):
        return "run", "WMA has no result"
    if w2 is not None and w1["out"] != w2["out"]:
        return "run", "random"
    if TIMING_RE.search(text):
        return "run", "timing"
    if norm(w1["out"]) != norm(m["out"]):
        return "run", "differs from WMA"
    extra = msg_names(m["msgs"]) - msg_names(w1["msgs"])
    if w2 is not None:
        extra -= msg_names(w2["msgs"])
    if extra:
        return "run", "messages WMA does not give: " + " ".join(sorted(extra))
    return "check", ""


def main():
    wdir, mdir = sys.argv[1], sys.argv[2]
    xfail_path = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, "xfail.json")
    xfails = json.load(open(xfail_path)) if os.path.exists(xfail_path) else {}
    os.makedirs(OUT_DIR, exist_ok=True)
    for nb in NOTEBOOKS:
        cells = json.load(open(os.path.join(HERE, "cells", f"{nb}.json")))
        w1 = load(os.path.join(wdir, f"{nb}.s1.jsonl"))
        w2 = load(os.path.join(wdir, f"{nb}.s2.jsonl"))
        ms = load(os.path.join(mdir, f"{nb}.jsonl"))
        nb_xfails = xfails.get(nb, {})
        data = []
        # symbol -> (the cell that last assigned it, that cell's "secs";
        # None when the cell is skipped)
        assigned = {}
        for i, cell in enumerate(cells, 1):
            m = ms.get(i)
            mode, reason = cell_mode(cell, w1.get(i), w2.get(i), m)
            sets, uses = symbols(cell["in"])
            secs = m["secs"] if m is not None else None
            for sym in sorted(uses):
                j, needs = assigned.get(sym, (None, 0))
                if j is None:
                    continue
                if needs is None:
                    if mode != "skip":
                        mode, reason = "skip", f"uses {sym}, which skipped cell {j} assigns"
                elif secs is not None:
                    secs = max(secs, needs)
            for sym in sets:
                assigned[sym] = (i, None if mode == "skip" else secs)
            entry = {"i": i, "section": cell["sec"].strip(), "in": cell["in"], "mode": mode}
            if secs is not None:
                entry["secs"] = secs
            if mode == "check":
                entry["expected"] = norm(w1[i]["out"])
            elif reason:
                entry["reason"] = reason
            if mode != "skip" and str(i) in nb_xfails:
                entry["xfail"] = nb_xfails[str(i)]
            data.append(entry)
        with open(os.path.join(OUT_DIR, f"{nb}.json"), "w") as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
            f.write("\n")
        counts = {k: sum(e["mode"] == k for e in data) for k in ("check", "run", "skip")}
        print(nb, counts, "xfail", sum("xfail" in e for e in data))


if __name__ == "__main__":
    main()
