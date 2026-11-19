"""Run notebook input cells under Mathics3 with a Combinatorica package loaded,
appending one JSON line per cell.

usage: run_mathics.py package.wl cells.json out.jsonl timeout start

Each cell is evaluated with the session's own timeout, which stops it
between evaluation steps (status "timeout"); SIGALRM, 30 s later, is only
a backstop for code that never checks it. An evaluation aborted for
another reason, such as $RecursionLimit, is "aborted". A Python exception
escaping the evaluation is "crash", except when it comes as the time limit
runs out: the interrupt then hit in the middle of a step, and the cell is
"timeout" with "crash_at_timeout". Before each cell "start i" goes to
stdout so a watchdog can tell where a hang is.

A cell is evaluated as in a notebook, the same way run_wma.wls does it:

- A cell holding several expressions (HoldComplete[e1, e2, ...]) is one
  CompoundExpression[e1, e2, ...]; its value is the last one's.
- Cell i is evaluated with $Line = i, and Out[i] is then set to its value
  (not to the canonical string the harness prints), so % and %% refer to
  the earlier cells' values.

When the run starts after cell 1 (the watchdog restarted it after a hang
or crash), the state the earlier cells left is rebuilt first: every
earlier cell that finished ("ok" or "msg") and assigns something is
evaluated again, whatever its time, and so is every other one that took
at most REPLAY_SECS (for its side effects and its Out). A replayed cell
that does not finish again is listed in "replay_lost" of each later cell;
compare.py does not count a failure of a cell that uses what such a cell
assigns ("skip-after-hang").
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_tests import symbols  # noqa: E402

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


def run_cell(i: int, text: str, limit: float) -> dict:
    """Evaluate cell i (text is "HoldComplete[...]") as notebook input i.
    Gives status, out, msgs, secs and, on an exception, error."""
    session.evaluate(f"Clear[H`res]; $Line = {i};")
    t = time.time()
    signal.alarm(int(limit) + 30)
    try:
        res = session.evaluate_as_in_cli(
            f"H`canon[H`res = CompoundExpression @@ {text}]", timeout=limit
        )
        signal.alarm(0)
        out = res.result
        rec = {
            "out": out[1:-1] if isinstance(out, str) and out.startswith('"') else str(out),
            "msgs": [
                f"{m.symbol}::{m.tag}: {m.text}" if getattr(m, "is_message", False) else m.text
                for m in res.out
            ],
        }
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
        rec = {"out": "", "msgs": [], "error": "".join(traceback.format_exception(exc))[-3000:]}
        if isinstance(exc, TimeoutInterrupt):
            rec["status"] = "timeout"
        elif time.time() - t >= 0.98 * limit:
            # The time limit interrupted a step and left it broken.
            rec["status"] = "timeout"
            rec["crash_at_timeout"] = True
        else:
            rec["status"] = "crash"
    rec["secs"] = round(time.time() - t, 3)
    # Out[i] is the cell's value; keep only the last two, as % and %% need.
    try:
        session.evaluate(
            f"Unprotect[Out]; Out[{i}] = If[ValueQ[H`res], H`res, $Aborted]; "
            f"Quiet[Out[{i - 2}] =.]; Protect[Out]; Clear[H`res];"
        )
    except Exception:
        pass
    return rec


cells = json.load(open(inf))

# Re-create the state the earlier cells left, after a restart.
REPLAY_SECS = float(os.environ.get("REPLAY_SECS", "20"))
lost = []
if start > 1 and os.path.exists(outf):
    done = {r["i"]: r for r in map(json.loads, open(outf))}
    for j in range(1, start):
        r = done.get(j)
        if r is None or r["status"] not in ("ok", "msg"):
            continue  # it failed in the first run too: nothing to restore
        assigns = bool(symbols(r["in"])[0])
        if not assigns and r["secs"] > REPLAY_SECS:
            continue
        print("replay", j, flush=True)
        rr = run_cell(j, r["in"], tmo)
        print("replayed", j, rr["status"], rr["secs"], flush=True)
        if rr["status"] not in ("ok", "msg") and assigns:
            lost.append(j)

with open(outf, "a") as out_file:
    for i in range(start, len(cells) + 1):
        c = cells[i - 1]
        print("start", i, c["in"][:100], flush=True)
        rec = {"i": i, "sec": c["sec"], "in": c["in"]}
        rec.update(run_cell(i, c["in"], tmo))
        rec["tmo"] = tmo
        if start > 1:
            rec["restarted_at"] = start
            rec["replay_lost"] = lost
        rec["maxrss_mb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024
        out_file.write(json.dumps(rec) + "\n")
        out_file.flush()
        print("done", i, rec["status"], rec["secs"], flush=True)
