# RJ45 manipulation mechanisms

Research checkpoint: 2026-10-16. Statements about proposed designs are engineering
hypotheses until the corresponding contact simulation passes.

## Reis et al., 2021 — actual mechanism inspected

Read the [publisher's full PDF](https://www.mi-research.net/en/article/pdf/preview/10.1007/s11633-021-1300-5.pdf),
particularly §§2.4, 3.2–3.3 and Figure 3 (printed p.649). Local research copy:
`sources/reis2021.pdf`.

The final PLA gripper has one fixed finger and one sliding finger, an HS-422
servo, rack-and-pinion transmission and dovetail guide. Thin fingers terminate
in form-fitting jaws exploiting a connector gap; small brackets resist rotation.
The authors report 90 supervised automatic unplug/replug cycles without failure.
Their setup requires an initially seated connector and a cable tipped aside to
avoid a rear approach collision. The novice teleoperation experiment tests
removal, not insertion; it is distinct from the automatic-cycle experiment.
The drawings illustrate jaw shaping but do not supply a complete dimensioned
latch-tool blueprint or force calibration. No downloadable author CAD or CAD
license was found in the paper. Do not infer universal connector compatibility
or a separately actuated latch from this source.

## Proposed adaptation, not a replica

Our connector model has a spring-hinged clip and a retaining socket lip. It does
not expose every molded recess shown in the paper. Therefore a literal jaw-gap
interlock cannot be assumed to exist. Design C will use a pocket around the
accessible housing/boot transition, one sliding jaw, anti-rotation shoulders,
and a separate gripper-mounted spring-limited tongue. Verify all engagement by
contact and measured pose. Do not add a fictional socket/connector grip feature
merely to make the tool succeed.

For commercial designs, use housing pads with shallow axial support shoulders
where the existing geometry allows. Keep the latch tongue independently
retractable so that the clip springs back before the jaws release. A passive
lateral/angular compliance stage may help alignment, but its actual displacement
must be measured and bounded; compliance is not permission to teleport the plug.

## Constrained industrial cabling

[Jaya, Michalak, Radke and Haninger, 2024](https://arxiv.org/html/2404.10829v1)
studies FASTON and a different industrial connector, not RJ45 release. Narrow
form-fit fingers reduce slipping. A passive two-pillar fixture corrects FASTON
orientation, with stated limitations. For a different cable arrangement,
a Scott–Russell linkage redirects jaw force; the fixed anchor also serves as
the opposing jaw. The paper explicitly identifies a routing operation made
impossible by nearby geometry. These are useful mechanisms and failure examples,
not evidence that a generic parallel gripper can release an RJ45 tab.

Our application implication: test the entire approach and withdrawal swept volume,
not just the fingertip at the final pose. Keep cable shape and adjacent-port
occupancy in the experiments. Preserve collision failures as results.

## In-hand connector manipulation, 2026

[Gu, Zhang and Jiang, IEEE RA-L](https://ieeexplore.ieee.org/abstract/document/11397151)
proposes parallel gripping with embedded in-hand manipulation for hanging cables
and subsequent force-controlled insertion. Publication metadata and abstract
were verified; the full mechanism drawings were not accessible in this research
pass. No dimensions, CAD, force limits or RJ45 latch capability are inferred.
The [authors' laboratory publication list](https://vbase.hitsz.edu.cn/publications.htm)
also lists the work. This is a possible later extension for free cable pickup,
not a prerequisite for the specified initially seated connector task.

## Baseline physics and non-negotiable changes for robotic trials

The frozen `rack_sim` implements a rigid-body spring hinge, tooth/lip contact,
36-link cable and a measured-state observer. It is not FEM and has no calibrated
plastic material failure model. Its old demo moves the plug with `/World/HandDrive`
and depresses the clip using a plug-attached `/World/ClipPress`.

The robotics layer must remove those two actuation mechanisms before task start.
It must keep the connector/latch/socket/cable colliders. It may use a documented
physical pre-seating initialization, outside the timed trial, then disable/remove
the initialization actuator and verify continued retention. During the trial,
only the robot/gripper's joints may be commanded. The observer may read the plug
pose but cannot retain it or press its clip.

Required causal controls: pulling before release must not extract; a disabled
latch actuator must not unlock; an open or ineffective grasp must not transport
the connector; jaws open after seating must leave the connector retained.
Record these separately from benchmark trials.
