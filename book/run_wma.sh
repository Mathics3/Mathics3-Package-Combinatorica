#!/bin/bash
# Run the book's notebook examples under WMA (wolframscript), with two seeds.
# usage: run_wma.sh OUTDIR TIMEOUT [NOTEBOOK...]
out=$1; tmo=$2; shift 2; here=$(cd "$(dirname "$0")" && pwd)
nbs=${*:-Chapter3 Chapter4 Chapter5 newFeatures tutorial}
mkdir -p "$out"
for n in $nbs; do
  for seed in 1 2; do
    python3 "$here/drive_wma.py" "$here/cells/$n.json" "$out/$n.s$seed.jsonl" $seed "$tmo" > "$out/$n.s$seed.summary" 2>&1
  done
done
cat "$out"/*.summary
