"""Compare Mathics3 cell results against two WMA reference runs.

usage: compare.py WMA_DIR MATHICS_DIR [OUT.json]

WMA_DIR holds NAME.s1.jsonl and NAME.s2.jsonl (two random seeds);
MATHICS_DIR holds NAME.jsonl. Prints per-notebook counts and writes
the per-cell verdicts to OUT.json.

Verdicts:
  skip     an Information[...] cell (usage text, not a computation), or a
           cell that could not be parsed into an input
  pass     same output (or a random cell) and no messages WMA lacks
  wrong    different output
  msg      right output but messages WMA does not give
  error    crash, hang, timeout or abort (e.g. $RecursionLimit) in Mathics3
  wma-bad  WMA itself crashed or timed out; not counted
"""

import json
import os
import re
import sys
from collections import Counter

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


def msg_names(msgs):
    return {m.group(0) for x in msgs for m in [MSG_RE.search(x)] if m}


def load(path):
    if not os.path.exists(path):
        return {}
    return {r["i"]: r for r in map(json.loads, open(path))}


def verdict(w1, w2, m):
    v, why = verdict1(w1, w2, m)
    if v in ("wrong", "msg", "error") and m.get("replayed_after_restart") is False:
        # Some definitions of earlier cells could not be redone after a restart.
        why = (why + " after-restart").strip()
    return v, why


def verdict1(w1, w2, m):
    if "Information[" in m["in"]:
        return "skip", ""
    if m["in"].startswith("PARSEFAIL:"):
        # The notebook cell could not be turned into an input expression.
        return "skip", "parse-fail"
    if w1 is None or w1["status"] in ("crash", "timeout"):
        return "wma-bad", ""
    if m["status"] == "crash" and m["secs"] >= 0.98 * m.get("tmo", 120):
        # The per-cell alarm interrupted a step: a timeout, not a crash.
        return "error", "timeout"
    if m["status"] in ("crash", "hang", "timeout", "aborted"):
        return "error", m["status"]
    random = w2 is not None and w1["out"] != w2["out"]
    timed = bool(TIMING_RE.search(m["in"]))
    same = (shape if timed else norm)(w1["out"]) == (shape if timed else norm)(m["out"])
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
        for i, m in sorted(ms.items()):
            v, why = verdict(w1.get(i), w2.get(i), m)
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
