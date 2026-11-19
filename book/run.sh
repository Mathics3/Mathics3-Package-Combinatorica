#!/bin/bash
# Run the book's notebook examples under Mathics3.
# usage: run.sh OUTDIR TIMEOUT [NOTEBOOK...]   (default: all five, in parallel)
# PKG=path/to/CombinatoricaV201.wl loads another copy of the package than this repo's.
out=$1; tmo=$2; shift 2; here=$(cd "$(dirname "$0")" && pwd)
nbs=${*:-Chapter3 Chapter4 Chapter5 newFeatures tutorial}
pkg=${PKG:-$here/../Combinatorica/CombinatoricaV201.wl}
mkdir -p "$out"
for n in $nbs; do
  python "$here/drive_mathics.py" "$pkg" "$here/cells/$n.json" "$out/$n.jsonl" "$tmo" > "$out/$n.summary" 2>&1 &
done
wait
cat "$out"/*.summary
