"""Joint-target Cartesian interface for the reference screw gantry."""
from rack_robotics.mechanics import ROOT, TOOL_OFFSET, pose
from rack_robotics.kinematics import joint_coordinates


class CartesianRobot:
    def __init__(self,stage,drives,architecture='A'):
        self.stage=stage; self.drives=drives
        self.architecture=architecture
        self.park=(-.19,.55,1.80) if architecture=='B' else (.15,.55,1.80)
        self.target=self.park

    def command(self,tcp):
        x,y,z=map(float,tcp)
        coordinates=joint_coordinates(self.architecture,(x,y,z),TOOL_OFFSET)
        for name,value in coordinates.items():
            self.drives[name].GetTargetPositionAttr().Set(value)
        self.target=(x,y,z)

    def tcp(self):
        p=pose(self.stage,ROOT+'/ToolMount')
        return (p[0],p[1]-TOOL_OFFSET,p[2])

    def error(self):
        return max(abs(a-b) for a,b in zip(self.tcp(),self.target))
