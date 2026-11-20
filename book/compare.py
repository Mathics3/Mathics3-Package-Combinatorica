"""Compare Mathics3 cell results against two WMA reference runs.

usage: compare.py WMA_DIR MATHICS_DIR [OUT.json]

WMA_DIR holds NAME.s1.jsonl and NAME.s2.jsonl (two random seeds);
MATHICS_DIR holds NAME.jsonl. Prints per-notebook counts and writes
the per-cell verdicts to OUT.json.

Verdicts:
  skip     an Information[...] cell (usage text, not a computation), a
           cell that could not be parsed into an input, or a failing cell
           that uses a symbol whose assigning cell could not be replayed
           after a restart ("skip-after-hang"), or a failing cell whose %
           refers to a skipped cell ("uses-skipped-out")
  pass     same output (or a random cell) and no messages WMA lacks
  wrong    different output
  msg      right output but messages WMA does not give
  error    crash, hang, timeout or abort (e.g. $RecursionLimit) in Mathics3
  wma-bad  WMA itself crashed or timed out; not counted

Cells that time something or measure memory (Timing, AbsoluteTiming,
ByteCount, ...), and cells that use a symbol such a cell assigned (rt in
ListPlot[First /@ rt]), are compared by shape only: every number is replaced by N,
in both WMA runs and in Mathics3, before the outputs are compared. A cell is
"random" when the two WMA runs differ; for these cells that too is decided
on the shape, so a different timing alone does not make a cell random.
"""

import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_tests import STRING_RE, symbols  # noqa: E402

NOTEBOOKS = ["Chapter3", "Chapter4", "Chapter5", "newFeatures", "tutorial"]
MSG_RE = re.compile(r"(\$?\w+)::(\w+)")


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
        if s.startswith("List[", i) and (i == 0 or not (s[i - 1].isalnum() or s[i - 1] in "`$")):
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


TIMING_RE = re.compile(r"\b(Timing|AbsoluteTiming|ByteCount|MemoryInUse|MaxMemoryUsed|SessionTime)\[")
NUMBER_RE = re.compile(r"-?\d+(\.\d*)?(\*\^-?\d+)?")


def norm(s: str) -> str:
    return re.sub(r"\s+", "", braces(s))


def shape(s: str) -> str:
    """The output with every number replaced by N: for cells whose values
    are times or memory sizes, only the structure can be compared."""
    return NUMBER_RE.sub("N", norm(s))


def statements(text: str):
    """The top-level statements of a cell: split at ; and , outside brackets."""
    text = STRING_RE.sub('""', text)
    if text.startswith("HoldComplete[") and text.endswith("]"):
        text = text[len("HoldComplete[") : -1]
    out, depth, cur = [], 0, ""
    for c in text:
        if c in "[{(":
            depth += 1
        elif c in "]})":
            depth -= 1
        if c in ";," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += c
    return out + [cur]


ASSIGN_TOP_RE = re.compile(r"^\s*([A-Za-z$][A-Za-z0-9$]*)\s*=(?!=)")


def timing_symbols(text: str):
    """The symbols a cell sets to timings: rt in rt = Table[Timing[...], ...],
    not c in Timing[c = ConnectedComponents[s]; ]."""
    return {
        m.group(1)
        for st in statements(text)
        for m in [ASSIGN_TOP_RE.match(st)]
        if m and TIMING_RE.search(st[m.end():])
    }


def msg_names(msgs):
    return {m.group(0) for x in msgs for m in [MSG_RE.search(x)] if m}


def load(path):
    if not os.path.exists(path):
        return {}
    return {r["i"]: r for r in map(json.loads, open(path))}


def verdict(w1, w2, m, ms, timed=False):
    v, why = verdict1(w1, w2, m, timed)
    if v in ("wrong", "msg", "error"):
        lost = m.get("replay_lost") or []
        lost_syms = set()
        for j in lost:
            if j in ms:
                lost_syms |= symbols(ms[j]["in"])[0]
        used = symbols(m["in"])[1]
        if used & lost_syms:
            # What it builds on could not be redone after a restart: the
            # failure says nothing about this cell.
            return "skip", ("skip-after-hang " + v + " " + why).strip()
        if m.get("replayed_after_restart") is False:  # older runs
            why = (why + " after-restart").strip()
    return v, why


def verdict1(w1, w2, m, timed=False):
    if "Information[" in m["in"]:
        return "skip", ""
    if m["in"].startswith("PARSEFAIL:"):
        # The notebook cell could not be turned into an input expression.
        return "skip", "parse-fail"
    if w1 is None or w1["status"] in ("crash", "timeout"):
        return "wma-bad", ""
    if m["status"] == "crash" and m["secs"] >= 0.98 * m.get("tmo", 120):
        # Older runs: the per-cell alarm interrupted a step. The harness now
        # records this itself as "timeout" with "crash_at_timeout".
        return "error", "timeout"
    if m["status"] in ("crash", "hang", "timeout", "aborted"):
        return "error", m["status"]
    timed = timed or bool(TIMING_RE.search(m["in"]))
    key = shape if timed else norm
    random = w2 is not None and key(w1["out"]) != key(w2["out"])
    same = key(w1["out"]) == key(m["out"])
    if not random and not same:
        return "wrong", "timing-shape" if timed else ""
    extra = msg_names(m["msgs"]) - msg_names(w1["msgs"]) - (msg_names(w2["msgs"]) if w2 else set())
    if extra:
        return "msg", " ".join(sorted(extra))
    return "pass", "random" if random else ""


def main():
    wdir, mdir = sys.argv[1], sys.argv[2]
    outp = sys.argv[3] if len(sys.argv) > 3 else None
    allrecs = []
    print(f"{'notebook':12} {'cells':>5} {'pass':>5} {'wrong':>5} {'msg':>4} {'error':>5} {'skip':>4} {'wma-bad':>7} {'pass%':>6} {'secs':>7}")
    for nb in NOTEBOOKS:
        w1 = load(os.path.join(wdir, f"{nb}.s1.jsonl"))
        w2 = load(os.path.join(wdir, f"{nb}.s2.jsonl"))
        ms = load(os.path.join(mdir, f"{nb}.jsonl"))
        if not ms:
            continue
        cnt = Counter()
        secs = 0.0
        prev = None
        timed_syms = set()  # symbols holding timings, e.g. rt in ListPlot[First /@ rt]
        for i, m in sorted(ms.items()):
            sets, uses = symbols(m["in"])
            timed = bool(TIMING_RE.search(m["in"])) or bool(uses & timed_syms)
            timed_syms = (timed_syms - sets) | timing_symbols(m["in"])
            v, why = verdict(w1.get(i), w2.get(i), m, ms, timed)
            if v != "pass" and "%" in STRING_RE.sub('""', m["in"]) and prev == "skip":
                # It uses the value of a cell that is not compared (usage text).
                v, why = "skip", "uses-skipped-out"
            prev = v
            cnt[v] += 1
            secs += m.get("secs") or 0
            allrecs.append({
                "nb": nb, "i": i, "verdict": v, "why": why, "in": m["in"],
                "mathics": m["out"][:600], "wma": (w1.get(i) or {}).get("out", "")[:600],
                "mathics_msgs": m["msgs"][:5], "wma_msgs": (w1.get(i) or {}).get("msgs", [])[:5],
                "secs": m.get("secs"), "wma_secs": (w1.get(i) or {}).get("secs"),
                "error": m.get("error", "")[-1500:],
            })
        counted = sum(cnt[k] for k in ("pass", "wrong", "msg", "error"))
        pct = 100 * cnt["pass"] / counted if counted else 0
        print(f"{nb:12} {len(ms):5} {cnt['pass']:5} {cnt['wrong']:5} {cnt['msg']:4} {cnt['error']:5} {cnt['skip']:4} {cnt['wma-bad']:7} {pct:5.1f}% {secs:7.1f}")
    if outp:
        json.dump(allrecs, open(outp, "w"), indent=1)


if __name__ == "__main__":
    main()
