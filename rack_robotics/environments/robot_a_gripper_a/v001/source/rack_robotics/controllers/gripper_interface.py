"""Independent housing grasp and latch actuation; no connector commands."""
from rack_robotics.mechanics import ROOT, pose


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
