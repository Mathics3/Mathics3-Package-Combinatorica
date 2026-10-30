#!/bin/bash
# Run the book's notebook examples under Mathics3.
# usage: run.sh OUTDIR TIMEOUT [NOTEBOOK...]   (default: all five, in parallel)
out=$1; tmo=$2; shift 2; here=$(cd "$(dirname "$0")" && pwd)
nbs=${*:-Chapter3 Chapter4 Chapter5 newFeatures tutorial}
mkdir -p "$out"
for n in $nbs; do
  python "$here/drive_mathics.py" "$here/../Combinatorica/CombinatoricaV201.m" "$here/cells/$n.json" "$out/$n.jsonl" "$tmo" > "$out/$n.summary" 2>&1 &
done
wait
cat "$out"/*.summary
