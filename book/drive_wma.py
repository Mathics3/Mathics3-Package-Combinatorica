"""Drive run_wma.wls over one notebook's cells, restarting after a kernel crash.

usage: drive_wma.py cells.json out.jsonl seed timeout
"""

import json
import os
import subprocess
import sys
from collections import Counter

inf, outf, seed, tmo = sys.argv[1:5]
cells = json.load(open(inf))
n = len(cells)
if os.path.exists(outf):
    os.remove(outf)
here = os.path.dirname(os.path.abspath(__file__))
start = 1
while start <= n:
    p = subprocess.run(
        ["wolframscript", "-file", os.path.join(here, "run_wma.wls"),
         inf, outf, seed, tmo, str(start)],
        capture_output=True, text=True,
    )
    done = [json.loads(l)["i"] for l in open(outf)] if os.path.exists(outf) else []
    if max(done, default=0) >= n:
        break
    started = [int(l.split()[1]) for l in p.stdout.splitlines() if l.startswith("start ")]
    bad = max(started) if started else start
    with open(outf, "a") as f:
        f.write(json.dumps({
            "i": bad, "sec": cells[bad - 1]["sec"], "in": cells[bad - 1]["in"],
            "out": "", "msgs": [], "secs": None, "status": "crash",
            "error": (p.stdout + p.stderr)[-1500:],
        }) + "\n")
    print("crash at", bad, file=sys.stderr)
    start = bad + 1
recs = [json.loads(l) for l in open(outf)]
print(inf, dict(Counter(r["status"] for r in recs)))
