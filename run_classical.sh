#!/usr/bin/env bash
# run classical baseline and plot
# args exp1 exp2 or all and stage 1 2 or all
# defaults exp1 all

set -euo pipefail

EXP="${1:-exp1}"
STAGE="${2:-all}"

# cd to repo root so python -m works
SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$SCRIPT_DIR"

run_one() {
  local e="$1"
  python -m verification_experiments.classical.search --exp "$e" --stage "$STAGE"
}

if [[ "$EXP" == "all" ]]; then
  for e in exp1 exp2; do
    run_one "$e"
  done
else
  run_one "$EXP"
fi

python -m verification_experiments.classical.plot
