"""Joint-target Cartesian interface for the reference screw gantry."""
from rack_robotics.mechanics import ROOT, TOOL_OFFSET, pose
from rack_robotics.kinematics import joint_coordinates, compliant_joint_coordinates, DeflectionFilter


class CartesianRobot:
    def __init__(self,stage,drives,architecture='A',gripper='A'):
        self.stage=stage; self.drives=drives
        self.architecture=architecture
        self.park=(-.19,.55,1.80) if architecture=='B' else (.15,.55,1.80)
        self.compliant_tool=gripper=='C'
        self.deflection_filter=DeflectionFilter()
        if self.compliant_tool: self.park=(self.park[0],self.park[1],1.795)
        self.target=self.park

    def command(self,tcp):
        x,y,z=map(float,tcp)
        commanded=(x,y,z)
        if self.compliant_tool:
            # Measured flange-to-tool deflection compensates static spring sag
            # through joint targets only. No tool/connector transforms are set.
            mount=pose(self.stage,ROOT+'/ToolMount')
            actual=self.tcp()
            nominal=(mount[0],mount[1]-TOOL_OFFSET,mount[2])
            offset=self.deflection_filter.update(nominal,actual,1/240)
            filtered=tuple(a-b for a,b in zip(nominal,offset))
            coordinates=compliant_joint_coordinates(self.architecture,commanded,
                nominal,filtered,TOOL_OFFSET)
        else: coordinates=joint_coordinates(self.architecture,commanded,TOOL_OFFSET)
        for name,value in coordinates.items():
            self.drives[name].GetTargetPositionAttr().Set(value)
        self.target=(x,y,z)

    def tcp(self):
        if self.compliant_tool:
            from pxr import UsdGeom, Gf
            xf=UsdGeom.Xformable(self.stage.GetPrimAtPath(ROOT+'/ToolFrame')).ComputeLocalToWorldTransform(0)
            return tuple(xf.Transform(Gf.Vec3d(0,-TOOL_OFFSET,0)))
        p=pose(self.stage,ROOT+'/ToolMount')
        return (p[0],p[1]-TOOL_OFFSET,p[2])

    def error(self):
        return max(abs(a-b) for a,b in zip(self.tcp(),self.target))
