# Repository contents and recovery boundaries

This Git repository preserves the application source, tests, infrastructure
scripts, authored rack/connector assets, all 83 saved robot environments, and
research and delivery documentation. It is not a complete VM backup or a tested
fresh-machine installer. Historical delivery audits describe the full workspace,
not only the files in a Git clone.

## Clone

```bash
git clone --recurse-submodules https://github.com/cybernetic-physics/dell-rack-cartesian.git
cd dell-rack-cartesian
git submodule foreach --recursive 'git lfs pull'
```

Install Git LFS before restoring the submodules; some upstream assets use it.
The parent repository stores its saved environments directly in Git, including
their manifests, frozen source, scene layers, diagnostic images and trajectories.
Their byte hashes must remain unchanged. Upstream repositories are pinned to
the revisions used during development, with their own licenses intact.

The original development workspace has local, uncommitted agent-memory notes
inside `vendor/IsaacAutomator`. Those notes are not part of this repository or
the pinned upstream dependency; they were left untouched.

## Included and excluded

| Included in Git | Separate recovery or archive required |
|---|---|
| `demo.py`, `rack_sim/`, active `rack_robotics/` modules and scripts, `tests/` | Python virtual environments, container runtime and GPU drivers |
| `infra/`, `scripts/`, pinned third-party submodules | Host provisioning, cloud credentials and NVIDIA container image |
| `assets/` authored scene/components and `rack_robotics/assets/shared_rack/` | `assets/vendor/` NVIDIA datacenter pack |
| All `rack_robotics/environments/` versions and frozen source | Raw run directories under `rack_robotics/experiments/`, including additional per-run frozen source |
| Top-level experiment JSON/CSV audit summaries and `dependency-inventory002/` | Full benchmark/diagnostic traces, render frames and videos |
| Research notes, source links, provenance and delivery reports | Downloaded papers/catalogs, screenshots and generated `artifacts/` galleries |

Links in historical documentation to excluded experiment directories, galleries,
or media require the separate archive. Do not interpret their absence in a clone
as a new failed simulation, or the retained summaries as a complete evidence set.

## Restoring simulation capability

See [REPRODUCE.md](rack_robotics/REPRODUCE.md#runtime-and-files) for the pinned
Isaac Sim runtime, saved-environment launch commands and dependency checks.

1. Prepare a compatible NVIDIA GPU host with its driver and Docker GPU runtime.
2. Adapt the existing VM/project/zone and host paths in `scripts/remote.sh`,
   `scripts/sync.sh`, `scripts/connect.sh` and `infra/start.sh`. They currently
   target the original GCP VM; they are not generic provisioning scripts.
3. Preserve the container layouts `/workspace` and `/isaac-sim`, and build the
   pinned image in `infra/Dockerfile`. Availability of that upstream image is an
   external dependency. The repository does not include an image archive.
4. Inside the container, run `bash scripts/fetch_assets.sh` to retrieve and
   checksum the approximately 9.84 GB NVIDIA archive. Extraction requires
   additional disk space. Retain the asset license notices.
5. Run `bash rack_robotics/scripts/setup_usd_tools.sh` for the separate USD tools,
   then perform the dependency check and a fresh simulation smoke test described
   in the reproduction guide. No clean-VM restoration has yet been validated.

The October 18, 2026 local audit matched all 6,687 locally available project
files in `dependency-inventory002/inventory.json`; its only missing project
dependencies were 1,822 NVIDIA datacenter files (10,239,092,578 bytes).
The remaining indexed runtime file belongs to the Isaac container.
That inventory is an index of hashes and paths, not an archive of file contents.

For full historical evidence recovery, separately back up the VM workspace and
its container/runtime configuration before deleting the VM or its disk. Git
does not replace that backup. The existing sync script excludes `vendor/` and
`artifacts/`; it is not a complete clone deployment or backup command.

## Local tests

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-tools.txt
.venv/bin/python -m unittest discover -s tests
```

These tests include file-only USD checks, not live GPU simulation acceptance.
The initial import passed all 398 tests both in the development workspace and
in a clean local clone using the existing Python tool environment. All seven
pinned submodules checked out from their upstream repositories. The clean clone
also matched all 6,687 locally available dependency-inventory files, with no
unexpected missing files or hash changes. This does not validate a fresh GPU VM.
