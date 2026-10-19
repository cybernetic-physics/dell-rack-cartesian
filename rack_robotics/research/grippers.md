# Gripper research and selection

This file preserves discovery and implementation checkpoints. For current
tested versions use the [recommendation](current_design_comparison.md); for
the latest primary-source checks see [source review001](source_review001.md).

Research checkpoint: 2026-10-16. The A prototype has passed individual full-rack
cycles on robot A and B; reliability is not established. Vendor force conventions differ; distinguish per-jaw force,
summed gripping force, drive torque and axial extraction force.

## Commercial alternatives and second-order adaptations

| Candidate | Verified facts and simulation assets | RJ45 adaptation / disposition |
|---|---|---|
| [SCHUNK EGP 25-N-N-B, 310900](https://schunk.com/de/en/gripping-systems/parallel-gripper/egp/egp-25-n-n-b/p/000000000000310900) | 26.5×18×72.7 mm; 0.11 kg; 3 mm stroke per jaw; 20–40 N total gripping force; 0.02 mm grip repeatability; finger length ≤32 mm, mass ≤20 g each; 24 V digital I/O. CAD offered; price requires login. | Selected A reference: narrow precision parallel jaws with custom tips and independent latch tongue. The 6 mm aperture change suffices if tips are pre-spaced around the housing. Do not extrapolate rated force to arbitrarily long fingers. |
| [SCHUNK official ROS description](https://github.com/SCHUNK-SE-Co-KG/schunk_description) | GPL-3.0 repository downloaded. EGP DAE meshes and prismatic/mimic URDF exist, but inspected file has 0.23519 kg base, ±20/30 mm joint limits and generic naming; optional finger file references unrelated `urdf_pzv_64` meshes. | This is not verified EGP25 CAD. Do not scale it and claim manufacturer fidelity. Use a dimensioned EGP25 envelope unless exact licensed 25 geometry is obtained. Keep this negative asset audit. |
| [Festo EHPS-16-A, 8070832](https://media.festo.com/media/204394_documentation.pdf) | 26×53.8×99.5 mm, 296 g, 10 mm per jaw, ≤0.03 mm repeatability in 2025 catalog; total force 154 N at specified reference conditions, varies with lever arm/orientation. M4 mounting, centering sleeves, 24 V; IO-Link and RA50 flange variants. CAD offered; price/reuse license not verified. | More stroke but bulkier than EGP25. Custom narrow tips and remote latch tool remain necessary. Older 2019 brochure's 50 N summary must not be mixed with current lever-arm curves. Derate by actual finger geometry; avoid housing crush. |
| [OnRobot RG2](https://onrobot.com/sites/default/files/documents/Datasheet_RG2_v1.0_EN.pdf) | Indexed manufacturer datasheet: 0–110 mm stroke, 3–40 N, 0.78 kg, 213×149×36 mm. Direct URL now redirects to homepage; retained evidence is indexed document plus downloaded official USD. [Official Isaac assets](https://github.com/OnRobot/onrobot-isaacsim) include RG2/6 and 2FG7/14, BSD-3-Clause. | Selected B: genuine articulated linkage asset, custom narrow terminal shoes, independent latch tongue. Large body stays behind cable fan-out; near-closed linkage clearance must be tested. Do not reduce its scale to fit. |
| [Robotiq Hand-E](https://robotiq.com/hubfs/Hand-E_Adaptive_Gripper_ProductSheet_EN_2024-11_WEB.pdf) | 50 mm stroke; 1 kg; 20–185 N per finger in 2024 sheet. [Official Isaac assets](https://github.com/robotiq/isaacsim_assets) contain Hand-E, 2F-85/140 with PhysX/Newton and fingertip variants, BSD plus specified NVIDIA CC-BY portions. | Hand-E inside fingertip mounts and narrow/bin-picking extensions are a plausible adaptation, but force floor and body mass are poor fits for this light connector. 2F-85 adds useful adaptation at greater linkage bulk. Preserve as alternatives, not a smaller rescaled gripper. |
| [SMC LEHZ10](https://www.smcworld.com/products/pickup/en-sg/electric_actuator/gripper_prod_lehz.html) | 4 mm total stroke; 6–14 N basic / 2–6 N compact motor. Manufacturer CADENAS export available; [catalog](https://www.smcworld.com/newproducts/en/pdf/leh.pdf) offers alternate tapped/flat fingers. | Lower force and compact variant attractive; narrow opening requires exact offset tips. Same missing latch function. Candidate if EGP force or footprint fails. No official Isaac asset or redistribution license verified. |
| [Reis RJ45-specific tool](rj45_mechanisms.md) | Paper's actual mechanism and limitations documented separately. | Selected C inspiration, not licensed CAD reproduction: one fixed and one guided sliding form-fit jaw, independent tongue and bounded compliance. |

## Asset/control inspection

OnRobot RG2 entry point is `assets/rg2/onrobot_rg2.usda`. It references local
geometry/material/physics layers. The default PhysX linkage uses a driven
`finger_joint` and mimic joints; fixed root must be replaced by a real connection
to our carriage. USD angular targets are degrees, not Isaac API radians. The
inspected drive has 4.5 N·m maximum torque and 0–70.06° limits: those defaults
are simulation settings, not a calibrated 3–40 N fingertip controller. Calibrate
aperture and force using measured finger geometry. Do not command mimic joints
independently or inherit collision filtering without auditing relevant surfaces.

Robotiq's repository offers compliant and parallel-grip physics alternatives;
changing variants changes mechanism response. Any trial must identify the
selected variant. Neither vendor asset supplies RJ45 release as a built-in skill.

## Shared latch tooling and custom actuator candidates

[Actuonix PQ12](https://www.actuonix.com/assets/images/datasheets/ActuonixPQ12Datasheet.pdf)
offers 20 mm travel, ±0.1 mm repeatability, 0.25 mm backlash and 20% maximum duty
cycle; the 30:1 version is rated up to 18 N and 28 mm/s no-load. A
[STEP download is offered](https://www.actuonix.com/datasheets), but redistribution
permission is not established. For our tongue, a lever/spring can reduce force
and bound travel. Do not use the 100:1 actuator's 50 N rating for the 30:1 version.
Duty cycle may require cooling dwell in repeated demonstrations.

[Hitec HS-422](https://hitecrcd.com/hs-422-deluxe-standard-servo/) has a
40.6×19.8×36.6 mm envelope. It is an accessible rack-and-pinion actuator candidate
for C. Servo stall torque is not sustained gripping force. Current limiting,
mechanical compliance and hard travel stops remain required. Costs for complete
custom tips, sensing, adapters and machining are unverified, not zero.

Follow-up source check: the HS-422 manufacturer page currently lists 45.5 g and
USD 20.99 for the servo alone (not a complete tool). Its 3.3–4.1 kg·cm maximum
torque is not a continuous rating. For the custom rack-driven jaw, a 6 mm pitch
radius and a 0.06 N·m simulated torque cap correspond ideally to 10 N; losses,
backlash and actual sustained thermal capability remain uncalibrated.
The PQ12 drawing on page 3 was visually inspected: its main body is 36.5 mm long,
21.5 mm wide and 15 mm thick at the widest cross-section. P/S variants weigh
19 g and R weighs 21 g. These are alternatives, not interchangeable geometries.

## Six required capabilities, by selected design

| Capability | A: EGP25-style precision tool | B: RG2 linkage tool | C: connector-specific tool |
|---|---|---|---|
| Housing grasp | Opposed 2 mm-class narrow pads, actual contact | Custom terminal shoes; use actual aperture geometry | Fixed datum jaw and moving pocket jaw |
| Latch access | Independent overhead tongue | Tongue mounted to tool frame, clear of linkage | Dedicated spring-limited central tongue |
| Maintain grip during release | Independent jaw/tongue commands | Verify linkage does not slide plug during tongue actuation | Support shoulders resist axial slip; tongue independent |
| Withdraw safely | Axial Y trajectory, force/slip limits | Same, with mass/linkage-deflection checks | Same, with pocket disengagement check |
| Realign/reinsert | Measured residual correction, bounded compliance | Account for depth shift during closing | Floating guided wrist with bounded lateral/angular compliance |
| Neighboring cables | Verify tip and 26.5 mm body swept volumes at 25 mm pitch | Body kept rearward; open-linkage sweep is highest risk | Narrow approach profile; cable escape channel required |

The table describes intended capabilities, not proof of all six. A has full-rack
feasibility passes on robots A/B; C currently has only a passing transmission
probe, and B is not yet integrated. The shared adapter
must physically attach each tool, preserve full-size geometry and expose a
calibrated TCP. Test failures with actual neighboring connector/cable geometry;
empty adjacent sockets alone do not establish dense-rack compatibility.

## Specialized tool implementation checkpoint

The first C model preserves a true fixed datum jaw and servo-driven sliding jaw.
Its 4 mm rack travel is coupled to a 6 mm pitch-radius pinion, with a 0.06 N·m
torque ceiling. A 20 N·m/rad pitch spring and 10,000 N/m vertical spring have
bounded ±3°/±0.8 mm travel. These are design assumptions, not measured servo,
flexure or plastic-finger properties. Angular constants are converted from SI
per-radian units to USD per-degree units. Full-size actuator envelopes are used;
the model is original geometry, not vendor CAD or the paper's complete design.

The installed PhysX schema supports a rack-and-pinion constraint between
articulation joints when the coupling itself is excluded from the articulation.
The [PhysX joint reference](https://nvidia-omniverse.github.io/PhysX/physx/5.2.1/_build/physx/latest/class_px_rack_and_pinion_joint.html)
also documents signed ratios for differently oriented joint frames. Our first
sign choice locked the jaw against its open limit. A negative ratio correctly
couples positive Z rotation to negative X rack travel. In physical probe 002,
38.1971° turned into approximately 4 mm travel; worst sampled constraint residual
was 0.00434 mm. Disconnecting only the coupling let the servo turn but left the
jaw open. No independent linear jaw drive is present. This is an ideal gearbox
constraint, not simulated individual tooth contacts, backlash or wear.

Connector trials exposed two actual integration problems: rack-stop envelopes
interfered with the insertion-stage rails, and a straight axial approach pushed
the fixed shoe into the taller cable boot. Moving the drive cluster down 7 mm
and allowing a small lateral approach/release offset addresses those geometric
problems without changing the plug. Compliant-TCP startup/control testing is
still in progress; no complete C manipulation result is claimed yet.

The long custom finger arms were thickened outward to 4.5 mm while retaining
2 mm contact tips and the same inner clearance. A simple cantilever estimate
with assumed steel E=200 GPa, 70 mm length, 6 mm height and a 10 N lateral end
load gives about 0.13 mm deflection for a 4.5 mm root versus 1.4 mm for a 2 mm
root. This is a preliminary stiffness screen, not FEA or a measured assembly
accuracy. The simulated fingers remain rigid; compliance/tolerance validation
and detailed mounting fasteners are still required.

Contact reports from C attempt 009 showed open-shoe interference during approach
and roughly 30 N peak contact impulse/dt estimates during abrupt closure, then
the 2.5 mm wrist deflection guard aborted. The next revision increases travel
to 5.7 mm (54.43° pinion rotation), keeps both shoes outside the housing during
a 2.5 mm lateral-offset approach, and limits the servo to 180°/s and tongue to
20 mm/s. The passive pitch spring is increased to an assumed 80 N·m/rad with
0.3 N·m·s/rad damping; this is an explicit design revision, not a measured
manufacturer specification. The ±3°/±0.8 mm hard bounds and 0.06 N·m torque cap
remain. These changes still require physical validation.

## Updated checkpoint: C feasibility and RG2 characterization

The preceding entries are development history. C now has full-rack feasibility
and fresh saved-scene reload passes on A/C v002, B/C v003 and C/C v001. The
latest closure limit is **60°/s**, with a 1.4 s grasp interval and 5 N transverse
drive allocation during datum/grasp/latch contact. These are isolated
development/reload successes, not randomized reliability or dense-cable proof.

For B, the complete unscaled OnRobot RG2 asset has 14 rigid bodies, 14 mesh
collision shapes and **0.7168111 kg** of authored rigid-body mass. That is the
asset's mass sum, not a new claim about the physical product's catalog weight.
Its authored visual envelope is approximately 152.62 × 74.88 × 208.36 mm;
the quick-changer/base contributes to that envelope. Existing internal pair
filters suppress contacts among vendor links. They must not be extended to
the connector, rack, custom fingers or adapter to obtain an artificial pass.
The isolated sweep preserves those vendor filters and explicitly records them.

The official [accessory catalog](https://onrobot.com/en/accessories) offers
50 and 100 mm RG2 fingertip extensions and explicitly notes the associated
loss of gripping force. The [50 mm extension drawing](https://onrobot.com/storage/technical_drawings/rg2-fingertip-extension-50-mm.pdf)
was downloaded and visually inspected: 74.20 mm total length, 16 mm base
width, 7/9 mm thickness dimensions, a 50 mm extension dimension, and the
specified Ø3.30/M4 mounting features. It does not supply a force rating for
our proposed offset adapter or certify custom dogleg-finger stiffness.
The drawing is retained for technical reference; no redistribution license
for that PDF has been established. The simulation asset remains BSD-3-Clause.

`scripts/probe_rg2.py` measures the vendor linkage at 240 or 480 Hz, driving
only `finger_joint`. It saves the original asset/license, initial scene,
source hashes, joint coordinates, both tip frames and axial motion. The
world attachment is an actual fixed joint, with the gripper oriented toward
the rack insertion axis. No connector is present: this characterization
cannot establish grasping, latch access, force calibration or rack feasibility.
The first launch failed before physics because the vendor asset was missing
on the VM; that failed launch is preserved separately from the next attempt.

Physical sweeps `rg2_sweep240_002` and `rg2_sweep480_001` passed five checks
each. The 10.8–14° narrow-angle sweep with a 1 N·m angular-drive cap also
passed (`rg2_narrow240_001`). The analytical model derived from the vendor
joint anchors agrees with all 2,175 recorded samples to 4.07 µm in tip-origin
spacing and 1.81 µm in axial extension; preserved source/asset hashes match.
See `experiments/rg2_geometry_verification001.json`. These are **unloaded**
checks, not loaded timestep sensitivity or a calibrated grip-force result.

The first mounted A/B trial stopped at initialization. A preliminary
bounding-box check suggested shoe-riser/base interference, but moving those
risers inward did not resolve the failure. Startup contact reports in attempt
002 identified the stronger cause: the central drop plate intersected the
RG2 housing/proximal links, producing extremely large solver impulses. The
failed contact force estimates are collision diagnostics, not hardware loads.
Attempt 003's side-routed cradle removed those contacts, allowing partial
closure, but its wide-open shoe guides then contacted the insertion rails.
It also exposed startup overshoot contacts at the rack upright/top bracket.
No connector manipulation success is claimed for these attempts.

The next revision uses a recorded physical setup sequence: lower/extend the
tool, narrow the jaws while clear of the depth rails, then return smoothly to
park. It commands actual joints only; the timed autonomous cycle still begins
with the plug retained and all baseline hand/press actuators inactive. The
expanded aluminum cradle/support assembly is estimated at 0.58 kg, and each
65.3 mm steel shoe assembly at 33 g. Earlier trials used underweight provisional
masses and remain preserved; their results must not establish final dynamics.
The 1 N·m drive cap corresponds to approximately 9.2 N per jaw by ideal virtual
work near the working angle, **not** a measured pad force or vendor rating.
Rigid custom shoes, mount fastening detail, force calibration and dense cable
clearance remain unfinished engineering work.
