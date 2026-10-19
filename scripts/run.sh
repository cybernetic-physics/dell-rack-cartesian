#!/usr/bin/env bash
# Inside the simulation container. Snapshot code so edits cannot alter a live run.
set -euo pipefail
cd /workspace
run_dir=$(mktemp -d /workspace/run-XXXXXX)
cp -R rack_sim demo.py "$run_dir/"
printf 'Run source snapshot: %s\n' "$run_dir"
exec /isaac-sim/python.sh -u "$run_dir/demo.py" --allow-root "$@"
