#!/usr/bin/env bash
# Run INSIDE the existing simulation container. No renderer or new service.
set -euo pipefail
tools_dir=/opt/rack-usd-tools
if [[ ! -e "$tools_dir" ]]; then
  python3 -m venv --without-pip "$tools_dir"
fi
# The persistent /workspace mount is noexec: compiled USD libraries must live
# on the container filesystem. Source/output USD files remain in /workspace.
/isaac-sim/python.sh -m pip --python "$tools_dir/bin/python3" install usd-core==26.8
"$tools_dir/bin/python3" -c 'from pxr import Usd; print("USD-only tooling:", Usd.GetVersion())'
