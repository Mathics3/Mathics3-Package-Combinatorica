"""Drive run_mathics.py over one notebook's cells with a watchdog.

usage: drive_mathics.py package.m cells.json out.jsonl timeout

If a cell runs longer than 2*timeout+30 s (the in-process alarm did not
stop it) the process is killed, the cell is recorded as "hang", and the
run restarts at the next cell in a fresh session. A process that dies
on its own is recorded as "crash" for the cell it was in.
"""

import json
import os
import queue
import subprocess
import threading
import sys
import time
from collections import Counter

pkg, inf, outf, tmo = sys.argv[1:5]
cells = json.load(open(inf))
n = len(cells)
if os.path.exists(outf):
    os.remove(outf)
here = os.path.dirname(os.path.abspath(__file__))
log = open(outf + ".log", "w")
limit = 2 * int(tmo) + 30
start = 1
while start <= n:
    p = subprocess.Popen(
        [sys.executable, os.path.join(here, "run_mathics.py"), pkg, inf, outf, tmo, str(start)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    )
    lines = queue.Queue()
    reader = threading.Thread(target=lambda: [lines.put(l) for l in p.stdout], daemon=True)
    reader.start()
    current, since, tail, killed = start, time.time(), "", False

    def drain():
        global tail, current, since
        while True:
            try:
                line = lines.get_nowait()
            except queue.Empty:
                log.flush()
                return
            log.write(line)
            tail = (tail + line)[-3000:]
            if line.startswith("start "):
                current, since = int(line.split()[1]), time.time()
            elif line.startswith("replay "):
                # Replaying earlier cells after a restart is progress too:
                # the time limit applies to each of them, not to them all.
                since = time.time()
        log.flush()

    while p.poll() is None:
        drain()
        if time.time() - since > limit:
            p.kill()
            killed = True
            break
        time.sleep(0.5)
    p.wait()
    reader.join(timeout=5)
    drain()
    log.flush()
    done = [json.loads(l)["i"] for l in open(outf)] if os.path.exists(outf) else []
    if not killed and max(done, default=0) >= n:
        break
    bad = current
    with open(outf, "a") as f:
        f.write(json.dumps({
            "i": bad, "sec": cells[bad - 1]["sec"], "in": cells[bad - 1]["in"],
            "out": "", "msgs": [], "secs": round(time.time() - since, 1),
            "status": "hang" if killed else "crash", "error": tail,
        }) + "\n")
    print(("hang" if killed else "crash"), "at", bad, file=sys.stderr, flush=True)
    start = bad + 1
recs = [json.loads(l) for l in open(outf)]
print(inf, dict(Counter(r["status"] for r in recs)))
