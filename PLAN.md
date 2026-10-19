# Task: Build a photorealistic Dell GPU rack simulation in NVIDIA Isaac Sim

You are an autonomous engineering agent. Your objective is to deploy a fully functional NVIDIA Isaac Sim environment on my existing GCP VM, construct a highly realistic Dell GPU server rack, and implement physically plausible RJ45 Ethernet cable insertion and removal.

**Execute the task end-to-end. Do not stop at planning, installation, or generating static assets.** Research existing solutions before developing custom implementations. Verify functionality through actual simulation runs.

## 1. Infrastructure and setup

Use my existing GCP VM with 2× NVIDIA RTX PRO 6000 GPUs.

Connect using:

```bash
gcloud compute ssh \
  --zone "us-central1-b" \
  "isaac-g4-rtxpro6000x2-flex" \
  --project "project-512201fe-6308-4879-83c"
```

Repository:

https://github.com/boredengineering/IsaacAutomator/tree/devcontainer

Requirements:

1. Connect to the existing VM and inspect its OS, GPU drivers, CUDA compatibility, storage, Docker configuration, and any existing Isaac Sim installations.
2. Clone the repository and use the `devcontainer` branch explicitly. Verify its instructions, dependencies, and compatibility before installing.
3. Install and configure IsaacAutomator, Isaac Sim, and any additional dependencies necessary.
4. Reuse the existing VM. Do not provision replacement instances.
5. Ensure GPU acceleration, RTX rendering, and PhysX simulation are working.
6. Keep all source code, USD assets, scripts, and configuration persistent across sessions.
7. Prefer the repository's established workflows and existing tooling over building infrastructure from scratch.

If the specified branch or repository is inaccessible, report that explicitly rather than silently substituting another implementation.

## 2. Remote visualization — HIGH PRIORITY

I am working on a MacBook and need to observe the simulation remotely.

**Set up remote visualization early, before constructing the main scene.**

Investigate the remote desktop capabilities provided by IsaacAutomator, including its existing noVNC implementation. Also evaluate Isaac Sim's supported streaming options.

Implement the most practical reliable solution.

Requirements:

- View the live Isaac Sim GUI from my MacBook.
- Interact with the viewport, move cameras, inspect objects, and start/stop simulation.
- Observe progress while the scene is being developed.
- Access logs, screenshots, and rendered previews without manually copying files.
- Provide straightforward connection instructions, including any SSH tunneling or port forwarding necessary.
- Keep access private and secure; avoid publicly exposing unauthenticated VNC, streaming, or development endpoints.

Verify that remote viewing actually works, not just that a server process starts.

If interactive streaming is unavailable, provide an operational fallback using remote desktop access and automatically generated preview renders.

## 3. Research realistic Dell rack hardware

Create a photorealistic datacenter environment centered around a Dell GPU compute rack.

**Research real hardware before modeling anything.**

Use publicly available photographs, Dell technical manuals, reference diagrams, CAD models, and 3D assets.

Suggested reference hardware:

- Dell PowerEdge XE9680 GPU servers.
- Dell rack enclosures and mounting hardware.
- Realistic network switches, PDUs, power cabling, and management Ethernet connections.

Start with these sources:

- https://www.dell.com/support/manuals/en-us/poweredge-xe9680/xe9680_ism_pub/system-configurations-rear-view-for-poweredge-xe9680?guid=guid-05770ad0-8d47-4fb2-b91e-6963d3411995&lang=en-us
- https://docs.isaacsim.omniverse.nvidia.com/latest/assets/usd_assets_overview.html

Search for reusable 3D assets across Isaac Sim/Omniverse asset libraries, public CAD repositories, manufacturer resources, GitHub, and other appropriate sources.

Prefer accurate existing meshes and CAD models to approximate procedural geometry.

### Scene requirements

Construct a full-scale datacenter rack featuring:

- A realistic rack enclosure with appropriate dimensions and mounting rails.
- Dell GPU compute servers based on real reference hardware.
- Accurate front and rear panels, ventilation, drive bays, PSUs, and network interfaces.
- Network switches and management Ethernet ports.
- Physically plausible cable routing and cable management.
- Realistic materials, metal finishes, plastic connectors, labels, and fine geometric details.
- Datacenter lighting and a convincing surrounding environment.

Prioritize high-fidelity rear-panel geometry because Ethernet connector manipulation is the primary task.

Use real-world scale, appropriate collision meshes, and PhysX-compatible assets.

**Do not invent RJ45 ports on hardware interfaces that actually use QSFP, OSFP, or other connector types.** Model the correct interfaces and place the RJ45 interaction on an appropriate management or Ethernet port.

## 4. RJ45 insertion and removal simulation — CRITICAL

The environment must support realistic interaction between a physical RJ45 Ethernet plug and a compatible female socket.

This is not merely a visual animation.

### Research first

Before implementing anything, search thoroughly for:

- Existing Isaac Sim RJ45 insertion/unplugging environments.
- Open-source robotic connector insertion simulations.
- CAD/3D models of RJ45 male plugs and female sockets.
- PhysX-based insertion, contact, and latching implementations.
- Robotic cable manipulation environments.
- Reusable examples involving snap-fit connectors, deformable cables, and mechanical constraints.

Evaluate the available implementations and reuse the best compatible components whenever possible.

Document your findings and explain which existing assets or techniques you selected.

### Physical requirements

Implement:

**RJ45 plug**
- Realistic geometry and scale.
- Correct insertion orientation.
- Connector body and retention clip.
- Collision geometry.
- Appropriate physical properties.

**RJ45 socket**
- Correct internal geometry and dimensions.
- Realistic entry tolerances and alignment.
- Collision handling.
- Proper insertion depth.

**Plugging behavior**
- Free manipulation of the plug.
- Alignment with the port.
- Contact and collision during insertion.
- Resistance to incorrect alignment.
- Stable insertion along the appropriate axis.
- A detectable fully seated state.
- Retention behavior after successful insertion.

**Unplugging behavior**
- The connector should not simply detach when arbitrary pulling force is applied.
- Model retention-clip release and the subsequent extraction.
- Allow repeated insertion/removal without resetting the entire environment.
- Correctly update the connection state.

**Cable behavior**
- Attach a visible Ethernet cable to the plug.
- Represent cable motion and routing realistically.
- Investigate existing flexible-cable simulations before implementing a custom solution.
- Avoid obvious stretching, clipping, or rigid-body artifacts.

Prefer genuine geometry, collision, contact, and constraint-based behavior.

Where detailed physical modeling is impractical, use a well-defined hybrid physical/state-machine implementation. Clearly distinguish physically simulated effects from approximated effects.

Do not claim full physical accuracy if some behavior is scripted.

## 5. Interactive demonstration

Create an executable demonstration supporting the full insertion/removal cycle.

At minimum:

1. Initialize the Dell rack scene.
2. Position an unplugged RJ45 cable near a suitable server port.
3. Move and orient the connector toward the port.
4. Insert the connector.
5. Detect and visualize successful connection.
6. Demonstrate that the connector remains seated.
7. Release the retention mechanism.
8. Unplug the connector.
9. Repeat the sequence.

Provide a controllable demonstration, ideally with interactive manipulation through Isaac Sim.

Also implement an automated scripted demonstration for reproducibility.

Do not make a full robotic manipulator implementation a prerequisite unless useful existing components make it straightforward. The primary objective is a physically meaningful connector interaction environment that can later be used for robotics research.

## 6. Implementation structure

Keep the implementation modular and reusable.

Organize the project so that the following can be independently inspected and modified:

- Rack and server USD assets.
- RJ45 male/female connector assets.
- Cable model.
- Connector interaction logic.
- Physics configuration.
- Scene assembly.
- Interactive demo.
- Automated validation scripts.
- Camera and visualization configuration.

Prefer Python scripting and native Isaac Sim/OpenUSD/PhysX functionality.

Record the exact Isaac Sim version, required extensions, asset dependencies, and setup commands.

Avoid unnecessary custom frameworks.

## 7. Validation and acceptance criteria

The task is complete only when the following have been verified:

**Infrastructure**
- Isaac Sim launches successfully on the existing GCP VM.
- Hardware-accelerated rendering works.
- The scene loads without critical errors.

**Visual quality**
- The rack closely resembles actual Dell datacenter hardware.
- Server layout and major interfaces correspond to real references.
- There are high-quality inspection views of the front, rear, and RJ45 connector area.

**Physical interaction**
- Plug insertion works.
- Plug removal works.
- Incorrectly aligned insertion does not succeed.
- Connector state transitions are detected reliably.
- The connector remains retained until the release condition is satisfied.
- Repeated plug/unplug cycles work.
- The simulated cable does not visibly break or detach.

**Remote access**
- I can view the simulation from my MacBook.
- I can observe the interaction demo.
- I can access progress logs and artifacts.

Implement automated smoke tests and a repeatable validation sequence. Capture screenshots and at least one video of the completed insertion/removal cycle.

## 8. Execution workflow

Work in the following order:

**Phase A — Infrastructure**
- Connect to the VM.
- Inspect the existing environment.
- Install/configure IsaacAutomator and Isaac Sim.
- Verify remote desktop/streaming access.

**Phase B — Asset and implementation research**
- Research Dell hardware and reference photographs.
- Find and evaluate existing rack/server models.
- Find existing RJ45 and cable physics implementations.
- Record sources, licenses, and compatibility.

**Phase C — Scene construction**
- Build the rack and datacenter environment.
- Import or construct server assets.
- Add detailed networking interfaces.
- Configure rendering, lighting, and physics.

**Phase D — RJ45 interaction**
- Implement the plug/socket assembly.
- Implement insertion and retention mechanics.
- Implement release/extraction mechanics.
- Implement cable behavior.

**Phase E — Testing and delivery**
- Run functional tests.
- Fix identified issues.
- Capture demonstration renders and videos.
- Verify remote visualization and provide connection instructions.

At each major phase, save a persistent checkpoint and update a progress document with:

- What was completed.
- What was actually tested.
- Relevant file paths.
- Any unresolved blockers.
- Next steps.

Keep execution logs accessible on the VM.

## 9. Final deliverables

Provide:

1. A working Isaac Sim installation on the existing VM.
2. A high-fidelity, reusable Dell GPU rack USD scene.
3. Realistic RJ45 connector and socket assets.
4. A functional plug/unplug physics and interaction system.
5. An executable demonstration script.
6. Automated validation scripts.
7. Screenshots and a rendered demonstration video.
8. A documented MacBook remote viewing workflow.
9. A README with exact commands to start, view, test, and modify the environment.
10. A research summary with asset sources, implementation references, licenses, and documented approximations.

## Important operating instructions

- **Execute autonomously.** Make reasonable engineering decisions without repeatedly requesting confirmation.
- Prioritize a working, physically meaningful simulation over unnecessary decorative details, but do not sacrifice the requested visual realism.
- Search for and reuse existing assets and implementations before creating new ones.
- Do not stop after generating code; actually run and debug it.
- Make incremental progress and preserve working checkpoints.
- Do not modify or destroy unrelated cloud resources.
- Do not recreate the existing VM.
- Do not expose credentials or unauthenticated services.
- If a requirement cannot be implemented completely, provide the best functional approximation and identify the limitation explicitly.
- Continue through validation and final delivery rather than ending after the first successful scene render.

**End goal:** I should be able to open my MacBook, connect to the running Isaac Sim environment, inspect a photorealistic Dell GPU rack, and observe a convincing, repeatable RJ45 Ethernet cable insertion and removal simulation.
