"""Independent housing grasp and latch actuation; no connector commands."""
from rack_robotics.mechanics import ROOT, pose
from rack_robotics.tool_parameters import APPROACH_OFFSET_X


class ParallelGripper:
    def __init__(self,stage,drives):
        self.stage=stage; self.drives=drives

    def grasp(self,closed):
        q=.00635 if closed else .0093
        self.drives['left'].GetTargetPositionAttr().Set(-q)
        self.drives['right'].GetTargetPositionAttr().Set(q)

    def press_latch(self,pressed):
        self.drives['latch'].GetTargetPositionAttr().Set(-.005 if pressed else 0.)

    def aperture(self):
        return pose(self.stage,ROOT+'/RightJaw')[0]-pose(self.stage,ROOT+'/LeftJaw')[0]-.002


class RackJawGripper(ParallelGripper):
    """Only the pinion servo is driven; the rack jaw is mechanically coupled."""
    # The fixed form-fit shoe must pass beside the taller cable boot before
    # moving laterally onto the narrower housing. Reverse this on release.
    approach_offset=(APPROACH_OFFSET_X,0.,0.)
    grasp_duration=1.4

    def grasp(self,closed):
        from rack_robotics.tool_parameters import rack_servo_target
        self.drives['servo'].GetTargetPositionAttr().Set(rack_servo_target(closed))

    def aperture(self):
        from pxr import UsdGeom
        from rack_robotics.tool_parameters import PAD_THICKNESS
        transform=UsdGeom.Xformable(self.stage.GetPrimAtPath(ROOT+'/ToolFrame')).ComputeLocalToWorldTransform(0)
        left=transform.GetInverse().Transform(pose(self.stage,ROOT+'/LeftJaw'))
        right=transform.GetInverse().Transform(pose(self.stage,ROOT+'/RightJaw'))
        return right[0]-left[0]-PAD_THICKNESS
