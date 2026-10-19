# /goal — Rack-Mounted Cartesian Robot and RJ45 Manipulation Design Exploration

## Mission

Extend the existing photorealistic Dell GPU rack simulation in NVIDIA Isaac Sim into a **robotic hardware design exploration and benchmarking system**.

Research, model, integrate, and evaluate multiple physically plausible **rack-mounted Cartesian robots and compact grippers** capable of autonomously unplugging and reconnecting RJ45 Ethernet cables on the existing server rack.

The goal is not to produce a single robot demonstration.

The goal is to discover and compare viable mechanical designs, test them in simulation, generate beautiful photorealistic demonstrations of every feasible combination, and preserve every configuration as a reusable Isaac Sim environment.

**Execute autonomously, iteratively, and end-to-end. Do not stop at research, planning, CAD generation, or a single successful demonstration.**

## 1. Existing infrastructure and environment

Use the existing GCP VM:

```bash
gcloud compute ssh \
  --zone "us-central1-b" \
  "isaac-g4-rtxpro6000x2-flex" \
  --project "project-512201fe-6308-4879-83c"
```

Hardware: 2× NVIDIA RTX PRO 6000.

The previous task established:

- NVIDIA Isaac Sim and IsaacAutomator.
- A detailed Dell GPU rack environment.
- A physically meaningful RJ45 plug/unplug simulation.
- Remote access and visualization from my MacBook.
- Existing simulation assets and demonstration scripts.

Relevant repository:

https://github.com/boredengineering/IsaacAutomator/tree/devcontainer

First inspect the existing environment, locate the actual completed rack scene and RJ45 implementation, identify the installed Isaac Sim version, and run a baseline test.

**Do not rebuild the infrastructure or replace the existing rack.**

Preserve the original environment as an immutable baseline. Build this project as a separate, modular extension.

Reuse the existing RJ45 physics and cable implementation unless a particular limitation must be fixed to support robot manipulation.

## 2. Primary engineering objective

Design robot configurations that can be physically mounted onto the Dell server rack itself.

The resulting machine should look like a plausible real-world robotic maintenance system, not an industrial arm floating in the scene.

It must:

1. Attach mechanically to the rack structure.
2. Move within a practical workspace near the rack's rear server interfaces.
3. Reach RJ45 connectors without colliding with adjacent hardware.
4. Grasp the Ethernet connector securely.
5. Depress or otherwise release the RJ45 retention latch.
6. Withdraw the connector along the insertion axis.
7. Maintain control of the connector and cable.
8. Align the connector with the original socket.
9. Insert it successfully.
10. Release the connector and retract.

The robot should support repeated autonomous unplug/replug cycles.

Favor designs that could realistically be manufactured using available components.

Keep the robot compact, mechanically plausible, and visually polished.

## 3. DEEP RESEARCH — second-order hardware search

This is an essential part of the project.

**Do not settle on the first Cartesian robot or gripper found online.**

Perform a two-level research process for both robotic mechanisms and grippers.

### Level 1 — Broad architecture discovery

Investigate existing commercial products, research prototypes, open-source projects, CAD assemblies, robotics papers, and Isaac Sim implementations.

Find candidates in several categories.

**Cartesian mechanisms**

- Compact XYZ gantry robots.
- Rack-mounted XY gantries with a short insertion axis.
- Vertical linear stages with horizontal/telescoping axes.
- H-bot/CoreXY-based Cartesian mechanisms.
- Miniature industrial Cartesian manipulators.
- Modular linear-actuator systems.
- Custom rack-frame-mounted gantry assemblies.

Consider commercial, open-source, and hybrid designs.

**Grippers and end effectors**

- Miniature electric parallel-jaw grippers.
- Adaptive two-finger grippers.
- Narrow-profile precision grippers.
- Cable/connector-specific grippers.
- Custom RJ45 grippers with integrated latch-release mechanisms.
- Passive-compliance and self-aligning gripper designs.
- Mechanisms that combine connector grasping with latch actuation.

### Level 2 — Detailed investigation of promising candidates

For each promising architecture or product:

1. Find manufacturer documentation and dimensional drawings.
2. Locate downloadable CAD/STEP/STL/URDF/USD assets.
3. Search GitHub and Isaac Sim examples for an existing implementation.
4. Inspect how the mechanism is articulated and controlled.
5. Research compatible motors, linear rails, gearboxes, mounts, and controllers.
6. Identify alternative products and derivative designs.
7. Find compatible gripper mounting interfaces.
8. Investigate real-world applications involving similar small-connector manipulation.
9. Verify physical dimensions, workspace, positional accuracy, travel, payload, and gripping forces.
10. Investigate feasibility of installing it on the Dell rack.

For any candidate that initially looks unsuitable, investigate whether an available variant, adapter, or simple modification makes it practical.

Likewise, when discovering a good gripper, investigate the research behind its mechanisms, compatible fingertips, alternate sizes, and specialized end-effector attachments.

This second-level search should produce genuinely better choices than a shallow hardware catalog.

### Important starting references

**Cartesian mechanisms**

- igus XYZ gantry: https://www.igus.com/product/dle-rg-0001?artnr=DLE-RG-0001
- Festo EXCM planar gantry: https://www.festo.com/media/catalog/204451_documentation.pdf
- OpenBuilds parametric mechanical components: https://github.com/matthew-yates/openbuildsParts

**Grippers**

- SCHUNK EGP miniature parallel grippers: https://schunk.com/us/en/gripping-systems/parallel-gripper/egp/c/PGR_1593
- Festo EHPS grippers: https://www.festo.com/media/catalog/204394_documentation.pdf
- OnRobot Isaac Sim assets: https://github.com/OnRobot/onrobot-isaacsim
- Robotiq Isaac Sim assets: https://github.com/robotiq/isaacsim_assets

**Critical RJ45 and cable manipulation research**

- *Gripper Design for Radio Base Station Autonomous Maintenance System*: https://doi.org/10.1007/s11633-021-1300-5
- *Industrial Cabling in Constrained Environments*: https://arxiv.org/abs/2404.10829
- *In-Hand Manipulation of the Connector for Cable Installation*: https://doi.org/10.1109/LRA.2026.3665078

The first paper is particularly important because it specifically investigates robotic RJ45 manipulation. Study the actual mechanical design and determine whether its gripper concepts can be adapted or recreated.

These are research starting points, not a fixed shortlist.

Find additional candidates independently.

### Research output

Create a hardware research report with:

- Candidate mechanism/gripper names.
- Manufacturer and product links.
- Technical specifications.
- CAD/asset availability and licenses.
- Simulation support.
- Estimated physical cost, when verifiable.
- Design advantages and disadvantages.
- Mechanical integration requirements.
- Feasibility for RJ45 manipulation.

Explicitly identify assumptions and missing information.

Do not invent CAD availability, specifications, or prices.

## 4. Design exploration — multiple robot architectures

Implement **at least three substantially different Cartesian mounting architectures**, where mechanically feasible.

Good initial candidates:

### Architecture A — Rear rack-mounted XYZ gantry

A compact gantry attached to the rear rack frame or mounting rails.

- Horizontal motion across the rack.
- Vertical motion across a useful range of server ports.
- Short depth-axis movement for plugging/unplugging.
- Gripper mounted on the end of the insertion stage.

### Architecture B — Vertical rail with telescoping carriage

A rack-mounted vertical rail with an articulated Cartesian carriage.

- Vertical travel alongside the servers.
- Horizontal extension toward selected ports.
- Controlled depth movement.
- Compact parked position.

### Architecture C — Compact H-gantry or modular linear-stage system

An alternative mechanism built from real linear-motion hardware.

- Rack-compatible mounting frame.
- Mechanically distinct drive architecture.
- Compact carriage/end-effector.
- Physical dimensions based on actual components.

These are suggestions, not mandatory products.

Select architectures based on actual research findings.

### Mechanical realism

For each robot, model:

- Linear guides and rails.
- Carriages.
- Motors and drive assemblies.
- Mounting brackets and fasteners.
- End stops and joint limits.
- Cable carriers where appropriate.
- Mechanical connection to the rack.
- Payload, masses, and inertia.
- Appropriate collision geometry.

Use real product CAD when available and licensed for use.

Otherwise construct a mechanically dimensioned parametric model.

**Do not simulate the robot using an unconstrained floating end-effector or direct world-position teleportation.**

Use actual articulated prismatic joints, realistic limits, and controller commands.

Any compact wrist or additional rotational DOF required for connector alignment is permitted, but the core robot architecture should remain Cartesian.

### Rack integration constraints

Evaluate:

- Attachment to rack rails or frame.
- Interference with existing servers.
- Rear-door clearance.
- Neighboring cable clearance.
- Airflow and service access.
- Reachability of the target ports.
- Robot parking and retraction.
- Mechanical load on the rack.
- Whether a physical version could actually be assembled.

Prefer designs with plausible mounting hardware.

Reject designs that only work by intersecting existing server geometry.

## 5. Gripper exploration — multiple alternatives

Implement **at least three different end-effector designs**.

Suggested categories:

### Gripper A — Commercial precision parallel gripper

Use a small commercial electric gripper, preferably with an available CAD model.

Explore custom fingertip geometry that can securely grasp the RJ45 connector housing.

### Gripper B — Alternative compact/adaptive gripper

Use a different gripper mechanism or mechanical architecture.

Evaluate its ability to grasp and manipulate a small Ethernet connector in a crowded rack.

### Gripper C — Specialized RJ45 end effector

Design a compact RJ45-specific mechanism inspired by the research literature.

It should combine:

- Secure grasp of the connector housing.
- Retention-tab depression.
- Controlled axial pulling/pushing.
- Alignment or passive compliance.
- Reliable release after insertion.

This can use a dedicated miniature latch actuator, a shaped finger, an integrated cam, or another researched design.

Investigate whether a commercially available gripper with custom fingertips can achieve the same functionality before creating a completely custom mechanism.

### Critical distinction: latch release

A standard parallel gripper may hold a cable or connector, but this does not imply it can unplug an RJ45 connector.

For every end effector, explicitly evaluate:

1. Can it grasp the connector body?
2. Can it access and release the retention latch?
3. Can it maintain its grip while the latch is released?
4. Can it safely withdraw the connector?
5. Can it realign and reinsert it?
6. Can it fit between neighboring Ethernet cables?

If it cannot perform the complete task, document why.

Do not disable the RJ45 latch or remove collision geometry merely to manufacture a successful demo.

## 6. Robot–gripper combination exploration

Create a modular interface so that each gripper can be attached to compatible robot architectures.

Build an initial comparison matrix of the three selected robots and three selected grippers: **up to nine robot–gripper combinations**.

Test all mechanically compatible combinations.

If a combination is impossible because of geometry, load limits, inaccessible latch orientation, or mounting incompatibility, explain and document that incompatibility instead of artificially forcing it to work.

For each viable combination:

- Assemble the complete simulation.
- Attach the robot to the rack.
- Configure joints and controllers.
- Mount the gripper using a realistic mechanical adapter.
- Configure the appropriate collision/contact settings.
- Plan a full unplug/replug motion sequence.
- Run actual simulation tests.
- Save the assembled environment.
- Capture demonstration videos.

Do not treat visually different versions of the same robot as substantially different architectures.

## 7. Autonomous unplug/replug controller

Build a reusable task-level controller that works across combinations through a shared robot/gripper interface.

Implement the following sequence:

1. **Initialize:** Connector starts fully inserted and latched into its original RJ45 port.
2. **Approach:** Robot moves from its parked pose toward the connector.
3. **Align:** Robot positions the gripper around the connector housing.
4. **Grasp:** Gripper securely grasps the RJ45 connector.
5. **Release latch:** Actuate the latch-release mechanism.
6. **Withdraw:** Retract the connector along the correct insertion axis.
7. **Separate:** Move the unplugged connector to a visible, safe position.
8. **Realign:** Move back toward the original socket and correct residual alignment error.
9. **Insert:** Push the connector into the socket.
10. **Seat and latch:** Detect successful seating and retention.
11. **Release gripper:** Open the jaws and disengage any latch-release tooling.
12. **Retract:** Return the robot to a safe parked position.

Use controlled Cartesian trajectories, joint control, force/contact feedback where practical, and collision checks.

Include fault detection and recovery for unsuccessful grasps, misalignment, failed insertion, and failed latch release.

The controller should work through interchangeable interfaces rather than containing a separate hardcoded animation for every scene.

### Physics integrity

The actual robot must move the connector.

Do not fake success by teleporting the plug, turning collisions off, or directly overriding its pose.

If the existing RJ45 simulation uses a hybrid latch state machine, preserve its real interaction conditions and expose the limitations in the results.

Separate actual physical simulation behavior from any state-assisted approximation.

## 8. Simulation experiments and scoring

Evaluate every compatible combination using the same experimental conditions.

Run an initial feasibility test followed by repeated full-cycle trials.

For combinations that pass basic feasibility, execute at least 10 randomized trials. Run at least 20 trials for the most promising configurations.

Include variation in:

- Initial positioning errors.
- Connector alignment.
- Cable resting configuration.
- Gripper approach trajectory.
- Small variations in contact/friction assumptions.
- Different target ports, where feasible.

Measure:

- Unplug success rate.
- Replug success rate.
- Complete-cycle success rate.
- Task completion time.
- Positional accuracy.
- Peak insertion/extraction forces where measurable.
- Contact/collision failures.
- Cable displacement and excessive tension.
- Latch-release reliability.
- Reachability and rack coverage.
- Simulation stability.
- Mechanical complexity and buildability.

Maintain a machine-readable results file for every experiment.

Rank the configurations using a documented scoring methodology prioritizing **reliability, rack compatibility, compactness, mechanical feasibility, and physical realism**.

Include visual quality as a secondary criterion.

A beautiful demonstration of a robot that cannot reliably manipulate the connector is not a successful design.

## 9. Photorealistic demonstrations — MAJOR DELIVERABLE

Every implemented and tested combination must produce visual artifacts.

For working configurations, create **high-quality photorealistic demonstration videos showing the complete unplug/replug cycle**.

For failed configurations, preserve diagnostic footage and clearly label the failure.

### Required camera views

Create at least four viewpoints per working combination:

**Camera 1 — Wide datacenter view**

Shows the full Dell rack and installed robot, clearly communicating the mounting architecture and physical scale.

**Camera 2 — Rear rack close-up**

Shows the robot approaching the rear server connections and manipulating the Ethernet connector.

**Camera 3 — RJ45 macro close-up**

A detailed view of the end effector, connector housing, retention latch, and socket.

This view should clearly show the actual latch-release, unplugging, and replugging mechanics.

**Camera 4 — Side or isometric engineering view**

Shows the robot's linear stages and the physical motion of the gripper relative to the rack.

Optionally add an end-effector-mounted camera if it improves the demonstration.

### Rendering quality

- Use the installed Isaac Sim RTX renderer.
- Use realistic metal/plastic/rubber materials.
- Maintain accurate lighting and shadows.
- Show believable cable deformation.
- Use high-quality camera composition.
- Avoid cluttered or overly distant views.
- Avoid clipping, flickering, excessive noise, and obstructed camera angles.
- Render at 1920×1080 or better, aiming for 30 FPS.
- Produce MP4/H.264 or another broadly Mac-compatible format.

Use a fast rendering mode during development, then high-quality RTX/path-traced rendering for final demonstrations when supported.

### Video outputs

For every successful combination, save:

1. A wide-angle full-cycle video.
2. A detailed RJ45 close-up video.
3. A side/isometric mechanism video.
4. A multi-angle edited or synchronized demonstration video.

Produce a polished, higher-resolution showcase video for the best-performing configuration.

The final videos must originate from the actual tested simulation trajectories. Do not substitute hand-authored animations that bypass the robot or connector physics.

For offline rendering, record the simulation state and trajectory first, then render consistent replay frames from multiple cameras.

The videos should make it easy to visually compare different robot–gripper configurations.

## 10. Save every environment for future reuse

**This requirement is essential.**

Every implemented combination must be preserved as an independent, reloadable Isaac Sim environment, including failed designs that may be useful for future research.

Do not overwrite previous configurations while exploring new ones.

Use a structure similar to:

```text
rack_robotics/
├── README.md
├── research/
│   ├── cartesian_robots.md
│   ├── grippers.md
│   ├── rj45_mechanisms.md
│   ├── candidate_matrix.csv
│   └── sources_and_licenses.md
├── assets/
│   ├── shared_rack/
│   ├── robots/
│   ├── grippers/
│   ├── adapters/
│   └── cables/
├── controllers/
│   ├── cartesian_interface.py
│   ├── gripper_interface.py
│   ├── rj45_task.py
│   └── trajectories/
├── environments/
│   ├── robot_a_gripper_a/
│   │   ├── scene.usd
│   │   ├── config.yaml
│   │   ├── manifest.json
│   │   ├── demo.py
│   │   ├── cameras.usd
│   │   ├── results.json
│   │   ├── videos/
│   │   │   ├── wide.mp4
│   │   │   ├── closeup.mp4
│   │   │   ├── side.mp4
│   │   │   └── multi_angle.mp4
│   │   └── screenshots/
│   ├── robot_a_gripper_b/
│   ├── robot_b_gripper_a/
│   └── ...
├── experiments/
│   ├── trial_logs/
│   └── summary.csv
├── scripts/
│   ├── run_environment.py
│   ├── evaluate_all.py
│   ├── render_demos.py
│   └── validate_assets.py
└── gallery/
    └── index.html
```

Adjust this structure to fit the existing project.

### Environment requirements

Each saved environment must include:

- The robot assembly.
- The selected gripper.
- Its attachment to the original rack.
- The RJ45 cable and socket.
- Working physics and controller configuration.
- Camera positions.
- Robot/gripper parameters.
- Reproducible initial conditions.
- Demonstration scripts.
- Test results.

Use USD composition, references, and variants to share common assets without duplicating the entire Dell rack for every configuration.

Verify that saved scenes can be reopened in a fresh Isaac Sim session.

Store all required dependencies locally or document their exact recoverable sources. Avoid broken references to temporary files.

## 11. Comparison gallery and remote access

Reuse the existing IsaacAutomator remote visualization infrastructure.

In addition, create a lightweight local web gallery that can be accessed securely from my MacBook.

For every combination, the gallery should show:

- Robot architecture and gripper name.
- A representative screenshot.
- Physical hardware references.
- A brief design description.
- Success/failure status.
- Performance statistics.
- Links to the multi-angle videos.
- Links or paths to the corresponding USD environment.

Allow me to easily compare different demonstrations without manually navigating the VM filesystem.

Provide SSH-tunneled access or another secure method compatible with the existing infrastructure.

Do not expose unauthenticated web services publicly.

All videos must also be available as downloadable files for local viewing.

## 12. Execution strategy

Work incrementally.

### Phase 1 — Existing environment verification

- Inspect the current Isaac Sim setup.
- Load and test the existing rack scene.
- Verify RJ45 insertion/extraction physics.
- Preserve a baseline copy or versioned reference.
- Confirm available GPU/storage resources.

### Phase 2 — Deep hardware research

- Search Cartesian robot architectures.
- Search compatible miniature grippers.
- Study specialized RJ45 manipulation research.
- Locate CAD assets.
- Investigate integration and mounting options.
- Build a ranked hardware candidate matrix.

Save the research before implementation, but continue executing automatically.

### Phase 3 — First successful robotic cycle

Choose the most promising robot/gripper combination.

- Build a physically plausible rack-mounted robot.
- Attach the gripper.
- Implement the controller.
- Execute a full autonomous unplug/replug cycle.
- Validate the result.
- Save the first reusable environment.

This establishes a reference implementation for the remaining combinations.

### Phase 4 — Design-space exploration

- Implement the alternative Cartesian architectures.
- Implement the alternative grippers.
- Assemble feasible combinations.
- Reuse the common controller.
- Fix combination-specific mechanical issues.
- Save each environment independently.

### Phase 5 — Automated benchmarking

- Run repeated trials.
- Record metrics and failure modes.
- Compare designs.
- Identify the strongest configurations.

### Phase 6 — Cinematic rendering

- Set up multiple cameras.
- Replay successful simulation trajectories.
- Capture full-resolution videos.
- Produce multi-angle presentations.
- Generate representative screenshots.

### Phase 7 — Final delivery

- Generate the comparison report.
- Finish the gallery.
- Verify environment reloads.
- Verify video playback.
- Verify MacBook access.
- Provide exact commands to run each configuration.

At the end of each phase, persist the current work, progress notes, and any unresolved problems.

Do not abandon the goal after the first success.

## 13. Final deliverables

The task is complete when the following exist:

1. A comprehensive research report on rack-mounted Cartesian robots and RJ45-capable grippers.
2. At least three investigated and implemented robot architectures, where feasible.
3. At least three implemented end-effector designs.
4. A comparative set of compatible robot/gripper configurations.
5. At least one demonstrably functional autonomous RJ45 unplug/replug system, with additional successful configurations wherever mechanically achievable.
6. An automated benchmarking framework with reliability metrics.
7. Independently saved, reloadable USD environments for all implemented configurations.
8. Photorealistic multi-angle video demonstrations and diagnostic captures.
9. A polished showcase video of the best configuration.
10. A remotely accessible comparison gallery.
11. A ranked final recommendation with hardware dimensions, estimated physical cost, part references, and explanation of the tradeoffs.
12. Complete documentation and scripts to reproduce, modify, and extend the work.

## Operating instructions

- Continue autonomously through research, implementation, testing, and rendering.
- Reuse existing open-source implementations and CAD assets wherever practical.
- Do not invent hardware specifications or unsupported capabilities.
- Prefer commercially reproducible mechanisms over aesthetically pleasing but implausible models.
- Use proper mechanical mounting, articulated joints, and real contact physics.
- Never fake connector manipulation through direct plug teleportation.
- Preserve all successful and unsuccessful designs.
- Maintain logs and checkpoints so interrupted work can resume.
- Optimize development with low-cost simulation and fast renders; reserve high-quality rendering for validated demos.
- Keep the VM and the original environment intact.
- Do not purchase hardware or provision additional cloud infrastructure.
- Document unresolved limitations instead of claiming incomplete simulations are successful.
- Do not stop merely because one design works. Compare alternatives.

**Ultimate objective:** A reusable digital laboratory for evaluating physically buildable, rack-mounted robotic maintenance systems, with multiple Cartesian robot/gripper combinations autonomously unplugging and reconnecting Ethernet cables on a photorealistic Dell GPU rack, each preserved as a complete simulation environment with beautiful multi-angle demonstrations.
