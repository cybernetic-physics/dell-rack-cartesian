"""Joint-target Cartesian interface for the reference screw gantry."""
from rack_robotics.mechanics import ROOT, TOOL_OFFSET, pose


class CartesianRobot:
    def __init__(self,stage,drives):
        self.stage=stage; self.drives=drives
        self.target=(.15,.55,1.80)

    def command(self,tcp):
        x,y,z=map(float,tcp)
        coordinates={'x':x,'y':y+TOOL_OFFSET-.68,'z':z-1.80}
        if not (-.21<=x<=.21 and -.125<=coordinates['y']<=.000001 and -.70<=coordinates['z']<=.000001):
            raise ValueError(f'TCP outside reference joint limits: {tcp}')
        for name,value in coordinates.items():
            self.drives[name].GetTargetPositionAttr().Set(value)
        self.target=(x,y,z)

    def tcp(self):
        p=pose(self.stage,ROOT+'/ToolMount')
        return (p[0],p[1]-TOOL_OFFSET,p[2])

    def error(self):
        return max(abs(a-b) for a,b in zip(self.tcp(),self.target))
