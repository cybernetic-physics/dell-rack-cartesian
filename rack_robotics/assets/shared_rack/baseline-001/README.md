# Dell GPU rack / RJ45 interaction in Isaac Sim

## 16-port cable-transfer demo — contact-driven latch

The management switch now has a row of 16 independently addressable RJ45 sockets (01–16, left to right). Use `--port-row` to run this scene. Each socket has open collision geometry, measured seating detection, retention and an independent connection LED. The same dynamic plug/cable is released, withdrawn clear of the panel, translated sideways and inserted into another socket. The automatic demo sweeps along the row and reverses at each end; it does not teleport the plug or reconnect it by changing a label.

The old scripted retention joint has been removed. A separate dynamic clip has a passive spring-loaded revolute hinge, an insertion ramp and a retaining shoulder. The socket lip physically depresses it on entry and catches the shoulder on withdrawal. **Press clip** drives a 4 N-limited orange pad against the free end; it does not move the clip directly or disable a retention joint. State/LED labels observe measured hook position only. The automatic controller waits for measured hook clearance before extraction.

This follows the rigid-latch/spring-hinge approach in [Newton's RJ45 example](https://github.com/newton-physics/newton/blob/main/newton/examples/contacts/example_contacts_rj45_plug.py), implemented in the existing PhysX scene. It is not a Newton backend migration or an FEM/material-stress simulation. The return spring is 0.15 N·m/rad with an 8° rest angle; damping, dimensions and the -6°/12° limits are tunable approximations, not manufacturer calibration.

Validated 2026-10-14 PDT: **13 isolated latch checks + 121 full-rack checks passed**. The isolated regression covers insertion-induced deflection (7.84° → 1.43°), spring return, 5 N retention (0.195 mm displacement), physical depression/release, re-latching without removal, repeated insertion, and causal negative controls. With zero press force, the release command alone cannot unlock it; with the socket lip disabled, an unpressed plug pulls out. All 16 rack ports held 5 N with 0.232–0.236 mm movement; maximum cable-joint gap was 0.054 mm. Actual noVNC press/re-latch, port 01 → 02 transfer and automatic continuation passed. The repeating demo is running. Earlier hybrid-latch reports remain unchanged under `artifacts/port-row/`.

- [Open live controls](http://127.0.0.1:16080/vnc.html?autoconnect=1&resize=scale)
- [Watch the port 01 → 02 recording](http://127.0.0.1:18080/latch-row/demo.mp4) — 7.13 s, 1280×800, 30 fps.
- [All-port physics report](artifacts/latch-row/validation.json), [GUI acceptance](artifacts/latch-row/remote-transfer.json), [delivery/source checks](artifacts/latch-row/delivery-smoke.json).
- [Isolated latch regression](artifacts/latch-probe-2.json), including measured angle/depth traces and negative controls.
- [Clip raised](artifacts/latch-row/latch-unpressed.png) / [clip physically pressed](artifacts/latch-row/latch-pressed.png); [USD component archive](artifacts/latch-row/usd-scene.tar.gz). The plug export includes its latch, hinge and pressing-pad bodies/joints.

```bash
# Close any previous simulation first; this replaces the single-port GUI session.
bash scripts/remote.sh 'sudo docker exec -d dell-rack-sim bash -lc "bash /workspace/scripts/run.sh --port-row --auto > /workspace/artifacts/logs/port-row.log 2>&1"'

# Validate every port and a reverse transfer, then leave the GUI running.
bash scripts/remote.sh 'sudo docker exec -d dell-rack-sim bash -lc "bash /workspace/scripts/run.sh --port-row --validate --keep-open --auto > /workspace/artifacts/logs/port-row-validation.log 2>&1"'

# Headless validation and artifact/source-hash checks.
bash scripts/remote.sh 'sudo docker exec dell-rack-sim bash /workspace/scripts/run.sh --port-row --headless --validate'
bash scripts/remote.sh 'sudo docker exec dell-rack-sim python3 /workspace/scripts/check_delivery.py --port-row'
```

In the GUI, **01–16** request a physical transfer to that socket. **Run repeated cycle** resumes the automatic sweep; **Manual control** stops its controller. **row** shows the full bank, **handoff** shows the first pair, and **Latch close** inspects the clip at the current port. The status line displays measured clip angle. Manual XYZ offsets are relative to the selected destination in row mode. Pause freezes a transfer; Stop/Resume resets it. A blocked movement times out visibly rather than falsely announcing success.

**Keep 3D perspective** is enabled by default: accidental Right/Top/Front camera switches automatically return to perspective without resetting orbit or zoom. This prevents the two-rectangle side view. Uncheck it only if you intentionally want orthographic views. **row** restores full-row framing. Telemetry records the active camera and automatic recovery count. `connect.sh` now detects a healthy existing tunnel and prints “Already connected” instead of trying to bind the ports again; unknown/unhealthy listeners are reported without killing them.

Current row outputs are in `artifacts/latch-row/` and `assets/latch-row/`; single-port mode uses `latch-single/`. Earlier hybrid row/single-port evidence remains separate. See `rack_sim/latch.py` for mechanical geometry, `scripts/latch_probe.py` for the isolated regression, and `rack_sim/row_demo.py` for the controller and all-port test. Local guard tests: `.venv/bin/python -m unittest discover -s tests -v`. After validation finishes, `.venv/bin/python scripts/check_row_interaction.py` tests the actual destination buttons through noVNC with the default desktop layout.

“Functional” here means mechanical connection/retention, not simulated Ethernet traffic. The neighbouring QSFP switch is not converted to RJ45.

## Historical single-port baseline (hybrid latch)

Deployed and validated on the existing GCP VM. The reference-based Dell rack, physical RJ45/cable interaction, private remote GUI, automated tests and recordings are operational. See the physical/visual approximations below; this is not manufacturer CAD or a calibrated snap-fit model.

Validated 2026-10-14 PDT: all 16 physical checks passed across three cycles; maximum cable-joint gap 0.611 mm; retention drift below 0.63 micrometres at 5 N. Actual Mac noVNC input passed camera navigation, pause, stop/reset, manual insertion, retained pulling, clip release, removal and automatic repetition. The live demo was left running.

## View from the MacBook

From this directory:

```bash
bash scripts/connect.sh
```

Keep that terminal open. Visit:

- Desktop: <http://127.0.0.1:16080/vnc.html?autoconnect=1&resize=scale>
- Live RTX preview and artifacts: <http://127.0.0.1:18080/>
- Execution logs: <http://127.0.0.1:18080/logs/>

The tunnel uses the configured `gcloud` identity. Both VM services bind to host loopback; no public unauthenticated desktop ports are opened. x11vnc itself only listens inside the container on localhost. Closing the tunnel does not stop the simulation.

The `Dell rack controls` window has camera presets, manual plug target offsets/orientation, clip release and repeated-cycle controls. Drag the hand target in millimetres. Positive Y extracts, negative Y inserts. Press the clip before extraction. Pause/Resume preserves the current pose; Stop/reset followed by Resume restarts the scene and latch state. Inspect objects in the Stage tree. The automatically refreshed browser preview supplies a fallback if a VNC client omits the native Vulkan viewport.

## Start and test

Persistent VM workspace: `/mnt/stateful_partition/home/hadjiyiannis_3_gmail_com/dell-rack`, mounted as `/workspace`. Container: `dell-rack-sim`. Do not use lifecycle commands that replace or delete the VM.

```bash
# Upload source/configuration (does not delete remote files).
bash scripts/sync.sh

# Build and start the desktop on the existing VM.
bash scripts/remote.sh 'bash /mnt/stateful_partition/home/hadjiyiannis_3_gmail_com/dell-rack/infra/start.sh'

# Interactive simulation; use a unique log filename for each launch.
bash scripts/remote.sh 'sudo docker exec -d dell-rack-sim bash -lc "bash /workspace/scripts/run.sh --auto > /workspace/artifacts/logs/demo.log 2>&1"'

# Automated physical acceptance run. Do not run two GUI instances together.
bash scripts/remote.sh 'sudo docker exec dell-rack-sim bash /workspace/scripts/run.sh --headless --validate --cycles 3'

# Alternatively, validate with the GUI and leave a repeating demo open on success.
bash scripts/remote.sh 'sudo docker exec -d dell-rack-sim bash -lc "bash /workspace/scripts/run.sh --validate --keep-open --auto > /workspace/artifacts/logs/delivery.log 2>&1"'
```

Use File → Exit to close a GUI instance before starting another. Each launch snapshots Python source into a unique VM run directory, so editing source during a run does not change its imports. Validation returns failure if any measured check fails and writes `validation.json`, state-transition events, inspection screenshots and `demo.mp4` under `artifacts/latch-row/` or `artifacts/latch-single/`. A successful script launch is not a passing physical test.

After validation, run `bash scripts/remote.sh 'sudo docker exec dell-rack-sim python3 /workspace/scripts/check_delivery.py'` to check the report, 1920×1200 inspection images, H.264 video, component assets and source hashes against the tested snapshot. On the Mac, `.venv/bin/python scripts/check_viewer.py` checks the noVNC framebuffer. `.venv/bin/python scripts/check_interaction.py` performs actual GUI acceptance against live physics telemetry; use it only after validation finishes and with the default desktop layout. Both use installed Google Chrome. Optional tools setup: `python3 -m venv .venv`, then `.venv/bin/pip install -r requirements-tools.txt`. Initial renderer/material compilation can take several minutes; wait for `DELL_RACK_READY` in the launch log.

When the Dockerfile changes, close the simulation and use `infra/start.sh --recreate` on the VM. It stops and renames only this project's old container as a timestamped backup, then starts the updated image. Workspace and cache bind mounts remain persistent. The container health check covers desktop/artifact availability, not physical acceptance.

## Dependencies and setup

- Existing host: COS 129, Docker 27.4.1, NVIDIA runtime, driver 580.95.05, two RTX PRO 6000 Blackwell Server Edition GPUs (96 GiB class).
- Exact installed Isaac Sim: `6.0.1-rc.7+release.42383.32955d8d.gl`, pinned image digest in `infra/Dockerfile`. This is the pre-existing 6.0.1 release-candidate image, not an assertion of a final 6.0.1 package.
- Uses `isaacsim.simulation_app`, `isaacsim.core.api`, `isaacsim.core.utils`, `omni.physx`, `omni.usd`, `omni.kit.viewport.utility`, `omni.ui`, OpenUSD and PhysxSchema included in that image.
- Native Ubuntu noVNC, x11vnc, websockify, Xvfb and Fluxbox; ffmpeg for recording. Pillow is available in the Isaac runtime.
- Install/recover the NVIDIA datacenter assets with `bash scripts/remote.sh 'sudo docker exec dell-rack-sim bash /workspace/scripts/fetch_assets.sh'`. The script resumes interrupted downloads, verifies the expected size and SHA-256, and extracts the pack. Expected SHA-256: `4972d1a9726b36279d7c26531b4d0a084156b7d512f5340b6e1063a9cf458fd4`. Preserve its folder structure and license notices.
- `assets/connectors/socket_cad.usdc` is self-contained and includes its upstream license. Regenerate with `scripts/import_socket.py` and the named research repository under `vendor/`.
- IsaacAutomator is cloned on the explicit `devcontainer` branch. Its tool image uses the repository Dockerfile (`WITH_PACKER=0`, since no VM is being provisioned). Its Ubuntu host installer is incompatible with COS; the simulation container is the documented adaptation.

IsaacAutomator revision: `1a708c60dc6f2eb6c00c774f729c109827fe80bd`. Rebuild its CLI with `sudo docker build --build-arg WITH_PACKER=0 -t isaac_automator:latest vendor/IsaacAutomator` from the VM project directory. This does not provision a VM. No Isaac Lab/robot arm is needed by this demo.

## Modify

| Component | Source |
|---|---|
| Hardware dimensions, contact tolerances, solver timing | `rack_sim/config.py` |
| Rack, Dell servers, network panels | `rack_sim/hardware.py` |
| Native USD geometry and materials | `rack_sim/geometry.py`, `rack_sim/labels.py` |
| Plug, open socket, measured connection state | `rack_sim/connector.py` |
| Spring-hinge latch, retaining lip, physical pressing pad | `rack_sim/latch.py` |
| PhysX flexible cable | `rack_sim/cable.py` |
| Scene assembly, imported assets, lighting, cameras | `rack_sim/scene.py` |
| Interactive controls and RTX preview | `rack_sim/visualization.py` |
| Measured acceptance sequence | `rack_sim/validation.py` |
| Runnable entry point | `demo.py` |

The current scene is saved to `assets/latch-row/dell_rack.usda` (or `assets/latch-single/dell_rack.usda`) before simulation. Paths target the persistent VM `/workspace` mount. `RESEARCH.md` records sources and limits; this is not a calibrated mechanical or electrical digital twin.

## Historical hybrid-model evidence and assets

- `artifacts/validation.json`: measured physical checks and state transitions from `/workspace/run-cyjudn`.
- `artifacts/delivery-smoke.json`: passing image/video/asset checks and matching source hashes.
- `artifacts/remote-interaction.json`, `remote-viewer.png`, `remote-front.png`: actual browser input and framebuffer evidence.
- `artifacts/front.png`, `rear.png`, `rear_detail.png`, `connector.png`: 1920×1200 inspection renders.
- `artifacts/demo.mp4`: 244-frame, 30 fps, 1280×800 H.264 insertion/retention/release/removal recording (8.13 s).
- `assets/dell_rack.usda`, `rack.usda`, `servers.usda`, `rj45_socket.usda`, `rj45_plug.usda`, `cable.usda`: reusable authored scene/components. The cable component's first joint targets `/World/Plug`; load those components together.
- `artifacts/usd-scene.tar.gz`: component USDs, labels and connector mesh/license. The external NVIDIA datacenter pack remains a separate dependency, already installed on the VM.
- VM log: `artifacts/logs/delivery-final.log`; persistent checkpoints: `PROGRESS.md`.

Local copies of the USDs and evidence are included. USD references retain the `/workspace/assets` layout used by the container; mount this project at `/workspace` and install the NVIDIA pack to resolve all dependencies. Opening USD alone does not install the Python latch controller—use `demo.py` for interaction.

Known non-fatal startup warnings: unused/legacy NVIDIA MDL annotations, unavailable OmniHub/audio services, and the TGS velocity-iteration behavior notice. The final run had no error-level log entries. External cloud asset browsing is not needed after the local pack is installed.

## Physical model and limits

In single-port mode, the active port is the third server's iDRAC RJ45 management interface. In `--port-row` mode, the 16 management-switch RJ45 ports are active instead; the QSFP/OSFP sockets remain passive. The plug is an 8 g dynamic compound body; independent socket-wall colliders leave an actual cavity. Force-limited 5 N spring drives represent a hand. The latch is a separate 0.6 g body connected to the plug by a passive spring hinge; an independent 2 g force-driven pressing pad releases it by contact. The latch/socket-lip contact is frictionless so retention cannot be attributed to friction alone. There is no plug-to-world/socket fixed retention joint. Arbitrary destructive loads, plastic deformation, fatigue, fracture and electrical connectivity are not modeled.

The 0.54 m, 36-link flexible cable uses capsule colliders and angularly compliant D6 joints; its visible jacket follows simulated endpoints. PhysX uses CPU TGS at 240 Hz with CCD and 128 position iterations for millimetre-scale contact. RTX rendering uses a GPU; multi-GPU rendering and GPU dynamics are intentionally disabled. This does not require both GPUs to be busy.

Dell panels are reference-based procedural reconstructions, not manufacturer CAD or a photogrammetric replica. Reused NVIDIA racks/switch/cable tray provide the surrounding environment; a licensed CAD-derived socket supplies passive port visuals. Fine grille, internal electronics, clear-plastic optics and elastic clip details remain simplified. The scene is suitable for interaction prototyping, not production mechanical-clearance certification.
