# Execution checkpoints

## Recurrent flat viewport — perspective protection, 2026-10-14 PDT

- User again saw two rectangles; live telemetry confirmed `/OmniverseKit_Right`. Restored the live row view directly and verified the browser screenshot. The initiating input is not established; the camera selection itself is confirmed.
- Added default-on **Keep 3D perspective** protection: switching to an orthographic/other camera restores the existing perspective camera without rewriting its transform. The checkbox allows intentional opt-out. Telemetry records recovery count and last rejected camera.
- Restarted only the application into `/workspace/run-GzKr1z`, log `artifacts/logs/camera-guard.log`. Physics/controller source is unchanged from the 121-check latch validation; only viewer code changed and `camera_guard.py` was added. The earlier source-hash report remains historical evidence for its snapshot.
- Eleven local tests pass (including three camera-guard and three idempotent-connection tests). Actual browser input has confirmed automatic Right, Top and Front recovery; no manual camera-preset rescue was used.
- Final GUI regression passed all three automatic recoveries, scroll zoom, restored row framing and continued physical transfers. Evidence: `artifacts/latch-row/camera-guard.json` and `camera-guard.png`. The native menu sometimes consumes a focus click; the test now verifies its rendered menu before selecting a camera. An attempted right-drag automation did not acknowledge a pose change in this session; zoom was separately verified rather than claiming that drag test passed.

## Contact-driven latch implementation — delivered 2026-10-14 PDT

- Inspected the user-linked Newton `example_contacts_rj45_plug.py`: it uses a dynamic rigid latch, revolute return spring and contact geometry, not deformable FEM. Applied the same mechanical principle within PhysX; no backend migration or source/mesh copying.
- Removed `/World/Retention` and all software enable/disable retention logic. Added a 0.6 g dynamic ramp/shoulder latch, passive 0.15 N·m/rad spring hinge, socket lip, and independent 4 N-limited pressing pad. State changes only observe measured hook pose; automatic transfer waits for hook clearance.
- Isolated `/workspace/latch-probe-1` passed 11 actual physics tests, including 7.84° → 1.43° insertion deflection, spring return, 5 N retention with 0.195 mm displacement, physical press/release, reinsertion, no-force release-command rejection, and removal without pressing when lip collision is disabled. Report `artifacts/latch-probe-1.json` includes traces; log `artifacts/logs/latch-probe-1.log`.
- Added measured re-engagement when the pressing pad retracts without cable removal. `/workspace/latch-probe-2` passed all 13 isolated checks with this final observer, including re-latch/re-press. Probe and full-rack model source match byte-for-byte.
- Five local controller tests pass, including the measured-hook-clearance guard. First full-rack run `/workspace/run-KphDJB` passed 121 checks. Final source `/workspace/run-xQihlV`, log `artifacts/logs/latch-row-2.log`, also passed all 121 checks with the updated observer: every socket seated/engaged/retained/released, 16 transfers including reversal, and cable gap below 1.5 mm. Measured retention movement 0.232–0.236 mm at 5 N; maximum cable-joint gap 0.05376 mm.
- Actual noVNC tests passed physical pressing (clip about 6.3° → -1.5°), spring-driven re-latch in the same socket, destination 01 → 02, and automatic continuation. Screenshots visually reviewed; zero browser errors. Evidence: `artifacts/latch-row/remote-transfer.json`, `latch-unpressed.png`, `latch-pressed.png`, `remote-row.png`.
- Delivery checks passed: 1920×1200 inspection renders, 214-frame/7.133 s H.264 transfer video, six component exports, hinge/pad included in plug USD, no fixed retention joint. Both VM and local runtime source hashes match the tested snapshot. Isolated mechanical source also matches its probe snapshot.
- Current outputs use `artifacts/latch-row/` and `assets/latch-row/` (single-port: `latch-single/`). Prior hybrid evidence remains untouched. Added latch-angle telemetry and a close-up camera. Hinge/pad are included in plug component USD exports.
- Copied evidence and USD archive locally; automatic physical-latch row demo left running. This is contact-driven rigid-link compliance, not calibrated FEM, fatigue or fracture simulation.

## Camera recovery / requested restart — 2026-10-14 PDT

- Reproduced the user's two-rectangle viewport: native camera selector was **Right**, not Perspective. Physics continued normally; this was a side-on orthographic view.
- Stopped only the project simulation process and restarted `--port-row --auto` as `/workspace/run-JYZuwX`; log `artifacts/logs/port-row-restart-camera.log`. Startup took approximately four minutes; the existing healthy SSH tunnel and VM were preserved.
- Camera presets now explicitly select `/OmniverseKit_Persp` before positioning it. Telemetry now reports the actual active camera and its transform, rather than always reporting the perspective prim.
- Actual noVNC regression passed: select Right, observe `/OmniverseKit_Right`, click row, observe restored Perspective, then observe another completed cable removal. Screenshot and report: `artifacts/port-row/camera-restored.png`, `camera-recovery.json`. Test script: `scripts/check_camera_recovery.py` (focus native application before opening its camera menu).
- Local compile and four controller tests pass. The previous 104-check physics report/source hashes remain evidence for the pre-camera-fix snapshot; no physics/controller code changed in this restart. Automatic row transfer remains running.

## RJ45 row extension — delivered 2026-10-14 PDT

- Requested change: a row of mechanically functional RJ45 ports and one cable transferred between sockets.
- Replaced the management switch's passive row with 16 numbered, independently collidable open sockets. Kept the neighbouring QSFP switch and Dell server interfaces unchanged.
- Generalized measured-pose port association, per-port LEDs/connection attributes and retention ownership. The fixed hand-drive origin is not moved during port selection.
- Added a clearance-gated handoff controller, adjacent-port automatic sweep with reversal, and GUI destination buttons. No body teleporting or scripted latch success.
- Four local controller-guard tests pass. Snapshot `/workspace/run-BgZWxS`, log `artifacts/logs/port-row-1.log`: all 104 PhysX checks passed across all 16 ports and 16 removals/transfers including reversal. Maximum cable-joint gap 0.05375 mm (limit 1.5 mm); 5 N retention passed at every socket.
- Delivery checks passed: 1920×1200 rear/row/handoff views, 199-frame H.264 transfer video (1280×800, 30 fps, 6.633 s), six USD exports and matching tested/delivered source hashes. Inspected full-row rendering, live desktop and recorded transfer frames.
- Actual noVNC buttons passed destination 01, complete physical 01 → 02 transfer (including observed disconnected state), and automatic continuation to 03. No browser JavaScript errors. Evidence in `artifacts/port-row/remote-transfer.json` and `remote-row.png`.
- Initial scene startup took several minutes with sustained CPU activity; it progressed without a simulation restart. Native-stack diagnostic logs are retained, but no specific root cause is claimed.
- Automatic adjacent-port sweep is running in the live GUI. Mechanical contact/cable physics and the hybrid clip are simulated, not Ethernet packet traffic.
- New outputs are isolated under `artifacts/port-row/` and `assets/port-row/`, preserving earlier single-port evidence.

## 2026-10-14 — Phase A in progress

- Existing VM confirmed RUNNING; COS 129, 400 GB persistent disk (~190 GB free).
- Two RTX PRO 6000 Blackwell GPUs, 97,887 MiB each; driver 580.95.05, CUDA 13.0.
- Docker 27.4.1 with NVIDIA runtime. Existing unrelated containers left untouched.
- IsaacAutomator `devcontainer` cloned at `1a708c60dc6f2eb6c00c774f729c109827fe80bd`.
- Inspected repository operator instructions, container workflow, noVNC role, connection and troubleshooting skills.
- Existing Isaac Sim image reports `6.0.1-rc.7+release.42383.32955d8d.gl`, pinned by digest in `infra/Dockerfile`.
- COS cannot run the repository's Ubuntu host installer directly. Use its container workflow and noVNC components in an isolated Ubuntu application container.
- Private loopback-only Docker ports and SSH tunnel scripts prepared; desktop viewport still to be tested.
- Persistent remote workspace: `/mnt/stateful_partition/home/hadjiyiannis_3_gmail_com/dell-rack`.
- Next: launch and verify actual rendered viewport; research hardware/assets; implement scene and interaction; run acceptance checks.

## Phase A checkpoint — installed and smoke-tested

- Built isolated `dell-rack-sim:6.0.1` container and upstream `isaac_automator:latest` image on the existing VM.
- Verified RTX Vulkan renderer selects RTX PRO 6000; PhysX cube settles at z=0.149998 m for a 0.3 m cube.
- Browser noVNC client received a 1600x1000 framebuffer through the Mac SSH tunnel, with no JavaScript errors. Actual screenshots are in local `artifacts/remote-viewer.png` and `remote-input.png`.
- Initial viewport capture was black; native RTX capture succeeded. Adding native readback/preview subsequently produced a visible native viewport and preview in noVNC. Keep the explicit RTX readback fallback.
- Private desktop and HTTP artifacts accessible at local ports 16080/18080 while `scripts/connect.sh` runs.
- Host, old containers and unrelated cloud resources preserved. No new instance or public service port.

## Phases B–D implementation checkpoint

- Dell technical guide downloaded and its front/rear figures inspected before hardware modeling.
- NVIDIA 9.8 GB datacenter pack downloaded/extracted on VM; reuse rack, switch and cable tray geometry.
- MIT RJ45 insertion repository inspected; socket visual extracted and units corrected. Source license preserved.
- PhysX cable examples, open-source connector tasks, KiCad alternatives and Cosserat-rod work evaluated; decisions in `RESEARCH.md`.
- Modular scene, reference-based server panels, plug/socket geometry, hybrid latch, D6 cable, manual GUI controls and measured validation sequence implemented.
- Local Python compile check passed.
- First scene run loaded materials and initialized PhysX, but failed before acceptance tests because an in-place source update changed the validation function signature during startup. No passing result claimed.
- Added `scripts/run.sh` to snapshot source for each run. Second headless acceptance run now uses its own immutable source copy.
- Next: debug actual acceptance results; inspect rack renders and cable behavior; capture video; verify interactive rack controls; complete delivery audit.

Physical, final visual and completed-scene remote acceptance remain unproven until the final run evidence is recorded.

## Physical validation checkpoint — first complete run

- Run 2 passed all 15 connector checks: lateral/inverted rejection and three insertion, 5 N retention, clip-release, removal cycles. Retention drift was approximately 2 micrometres.
- Cable acceptance failed: worst joint separation 12.73 mm against the 1.5 mm limit. The report is preserved locally as `artifacts/validation-2.json`; this is not a passing delivery.
- Inspection found imported rack origins were not centered, obscuring the main rack. Corrected units/origin normalization and added inspection lighting.
- Run 3 increases solver iterations and records the worst cable joint. Currently loading/compiling the corrected scene, with native rendering on the Python main stack and CPU compilation activity.
- Separated single physics ticks from rendering in the next source revision, to keep dwell timing and 30 fps recording accurate.
- Added manual orientation, clip/LED visualization and GUI pause/resume controls. These newest edits still require their own test run.

## Corrected timing / cable checkpoint

- Run 3 passed 16 checks after increasing solver iterations. Run 4, with exact single-tick control timing, caught a 5.57 mm startup gap at the free end of the initially horizontal cable; all connector checks still passed. Both reports are preserved.
- Routed the initial cable with coincident joints and slack: out beyond the fan cage, then down. This avoids dropping an entire horizontally suspended cable at startup; subsequent motion remains fully dynamic.
- Run 5 passed all 16 checks using the corrected timing and slack routing. Maximum cable-joint gap: 0.6109 mm (limit 1.5 mm). Retention drift: 0.54–0.63 micrometres at the 5 N drive limit. Three complete cycles succeeded.
- Rebuilt only the project application container with the correct health check; old container preserved as backup. New container healthy, ports still bound to 127.0.0.1. NVIDIA pack checksum verified.
- Final GUI build adds stop/reset state synchronization and real-time pacing. Running validation in that build, then leaving it open for remote-control acceptance.

## Final delivery — 2026-10-14 PDT / 2026-10-15 UTC

- Final source snapshot `/workspace/run-cyjudn`, log `artifacts/logs/delivery-final.log`: all 16 physical checks passed, three complete cycles, 0.6109 mm maximum cable gap, 0.54–0.63 micrometre retention drift at 5 N. No error-level log entries found.
- Delivery smoke test passed: four 1920×1200 views, 244-frame H.264 video (1280×800, 30 fps, 8.133 s), all six USD exports. Tested snapshot hashes match both VM source and local delivered source.
- Actual noVNC browser input passed pause/frozen physics, camera presets, right-drag viewport navigation (verified camera-transform change), stop/resume reset, manual insertion, retained pull, clip release/removal, and another automated cycle. Evidence: `artifacts/remote-interaction.json`, `remote-viewer.png`, `remote-front.png`.
- Removed a stale duplicate in-app image window; the native viewport is visible in noVNC and the independent HTTP live preview remains operational. Browser test now waits for control acknowledgements.
- Front, rear and connector inspection images reviewed against the reference layout. Geometry is a detailed reference-based reconstruction with the explicit visual/physical simplifications in README/RESEARCH, not exact CAD or calibrated material mechanics.
- Source, exported USDs, labels, connector license, reports, images and video are persistent on the VM; generated deliverables also copied locally. NVIDIA pack remains on the VM and can be re-downloaded with a verified checksum.
- During artifact collection the Mac SSH connection dropped. Reconnected successfully; VM still RUNNING, simulation still playing after 145 completed cycles. No restart or cloud replacement was needed.
- Final handoff: live repeated demo remains running; use `scripts/connect.sh` and the URLs in README. No known functional blocker remains within the documented hybrid model.
