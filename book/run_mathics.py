"""Run notebook input cells under Mathics3 with a Combinatorica package loaded,
appending one JSON line per cell.

usage: run_mathics.py package.m cells.json out.jsonl timeout start

Each cell is evaluated with the session's own timeout, which stops it
between evaluation steps (status "timeout"); SIGALRM, 30 s later, is only
a backstop for code that never checks it. An evaluation aborted for
another reason, such as $RecursionLimit, is "aborted". A Python exception
escaping the evaluation is "crash". Before each cell "start i" goes to
stdout so a watchdog can tell where a hang is.

A cell may hold several expressions (HoldComplete[e1, e2, ...]): all are
evaluated, in order, and the last one is the result, as in run_wma.wls.

When the run starts after cell 1 (the watchdog restarted it after a hang
or crash), the cells before it that finished cleanly in under REPLAY_SECS
are evaluated again first, so that their definitions are back.
"""

import json
import os
import re
import resource
import signal
import sys
import time
import traceback

from mathics.core.interrupt import TimeoutInterrupt
from mathics.core.load_builtin import import_and_load_builtins
from mathics.session import MathicsSession

pkg, inf, outf, tmo, start = sys.argv[1:6]
tmo, start = int(tmo), int(start)

# A cell that runs away with memory fails alone (MemoryError, recorded as a
# crash) instead of getting the whole job killed.
mem_gb = float(os.environ.get("CELL_MEM_GB", "4"))
try:
    resource.setrlimit(resource.RLIMIT_AS, (int(mem_gb * 2**30),) * 2)
except (ValueError, OSError):  # macOS does not support it
    pass

t0 = time.time()
import_and_load_builtins()
session = MathicsSession(character_encoding="ASCII")
builtins_secs = time.time() - t0
t0 = time.time()
session.evaluate(f'Get["{pkg}"]')
load_secs = time.time() - t0
print(f"builtins {builtins_secs:.2f}s package {load_secs:.2f}s", flush=True)

session.evaluate(
    r"""H`canon[r_] := Which[
   MatchQ[r, _Graphics | _Graphics3D | _GraphicsArray | _Image], "<" <> SymbolName[Head[r]] <> ">",
   True, Module[{s = ToString[FullForm[r /. x_Real :> Round[10^5 x]]]},
     If[StringLength[s] > 4000, StringTake[s, 4000] <> "...", s]]]"""
)

MSG_RE = re.compile(r"^(\S+::\S+):")


def on_alarm(signum, frame):
    raise TimeoutInterrupt()


signal.signal(signal.SIGALRM, on_alarm)

cells = json.load(open(inf))

# Re-create the state the earlier cells left, after a restart.
REPLAY_SECS = float(os.environ.get("REPLAY_SECS", "20"))
replayed_ok = True
if start > 1 and os.path.exists(outf):
    done = {r["i"]: r for r in map(json.loads, open(outf))}
    for j in range(1, start):
        r = done.get(j)
        if r is None or r["status"] not in ("ok", "msg") or r["secs"] > REPLAY_SECS:
            if r is not None and "=" in r["in"]:
                replayed_ok = False  # an assignment we could not redo
            continue
        print("replay", j, flush=True)
        signal.alarm(int(REPLAY_SECS) + 30)
        try:
            session.evaluate_as_in_cli(f"List @@ {r['in']};", timeout=REPLAY_SECS)
        except BaseException:
            replayed_ok = False
        signal.alarm(0)

with open(outf, "a") as out_file:
    for i in range(start, len(cells) + 1):
        c = cells[i - 1]
        print("start", i, c["in"][:100], flush=True)
        rec = {"i": i, "sec": c["sec"], "in": c["in"]}
        t = time.time()
        signal.alarm(tmo + 30)
        try:
            res = session.evaluate_as_in_cli(
                f"H`canon[Last[List @@ {c['in']}]]", timeout=tmo
            )
            signal.alarm(0)
            out = res.result
            rec["out"] = out[1:-1] if isinstance(out, str) and out.startswith('"') else str(out)
            rec["msgs"] = [
                f"{m.symbol}::{m.tag}: {m.text}" if getattr(m, "is_message", False) else m.text
                for m in res.out
            ]
            if session.evaluation.timeout:
                rec["status"] = "timeout"
            elif rec["out"] == "$Aborted":
                rec["status"] = "aborted"
            elif any(MSG_RE.match(m) for m in rec["msgs"]):
                rec["status"] = "msg"
            else:
                rec["status"] = "ok"
        except BaseException as exc:
            signal.alarm(0)
            if isinstance(exc, KeyboardInterrupt):
                raise
            rec.update(
                status="timeout" if isinstance(exc, TimeoutInterrupt) else "crash",
                out="",
                msgs=[],
                error="".join(traceback.format_exception(exc))[-3000:],
            )
        rec["secs"] = round(time.time() - t, 3)
        rec["tmo"] = tmo
        if start > 1:
            rec["replayed_after_restart"] = replayed_ok
        rec["maxrss_mb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024
        out_file.write(json.dumps(rec) + "\n")
        out_file.flush()
        print("done", i, rec["status"], rec["secs"], flush=True)
