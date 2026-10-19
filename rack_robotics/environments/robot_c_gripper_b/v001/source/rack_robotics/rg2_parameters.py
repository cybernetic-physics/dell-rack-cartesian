"""Original RG2 adapter design parameters in SI units, not vendor ratings."""
from rack_robotics.rg2_kinematics import tip_geometry

OPEN_ANGLE = 14.
CLOSED_ANGLE = 10.8
REFERENCE_ANGLE = 11.3
BASE_OFFSET = (.00005, .100, -.075)
SHOE_INWARD = .004
SHOE_RISE = -BASE_OFFSET[2] + .0003
SHOE_FORWARD = .230 - tip_geometry(REFERENCE_ANGLE)[1]
MOUNT_MASS = .480
SHOE_MASS = .036
CRADLE_WIDTH = .094
SIDE_DROP_X = .040
REAR_FLANGE_Z = -.085
REAR_FLANGE_HEIGHT = .080
SHOULDER_OFFSET_X = .0015
SHOULDER_WIDTH = .006


def clearance_screens():
    """Nominal static bounds only; cooked hulls/dynamics still need PhysX tests.

    Robot dimensions here are the current A/C frame/bridge/carriage geometry.
    The base envelope is measured from original vendor visual/mesh vertices.
    This is NOT a full swept-volume audit or a compatibility result.
    """
    shoe_center_open = tip_geometry(OPEN_ANGLE)[0]/2 - SHOE_INWARD
    return {
        'rightmost_port_cradle_to_frame_m': .240 - (.1875 + CRADLE_WIDTH/2),
        'side_drop_to_rg2_housing_m': SIDE_DROP_X - .006/2 - .03305,
        'open_shoulder_to_depth_rail_m': .016 - (shoe_center_open + SHOULDER_OFFSET_X + SHOULDER_WIDTH/2),
        'base_visual_top_to_carriage_m': -.030 - (BASE_OFFSET[2] + .0355),
        'rear_flange_to_carriage_m': -.030 - (REAR_FLANGE_Z + REAR_FLANGE_HEIGHT/2),
        'rear_flange_to_bridge_m': -.020 - (REAR_FLANGE_Z + REAR_FLANGE_HEIGHT/2),
    }
