"""Joint-target Cartesian interface for the reference screw gantry."""
from rack_robotics.mechanics import ROOT, TOOL_OFFSET, pose
from rack_robotics.kinematics import joint_coordinates, compliant_joint_coordinates, DeflectionFilter


class CartesianRobot:
    def __init__(self,stage,drives,architecture='A',gripper='A',control_dt=1/240):
        self.stage=stage; self.drives=drives
        self.architecture=architecture
        self.control_dt=control_dt
        self.park=(-.19,.55,1.80) if architecture=='B' else (.15,.55,1.80)
        if architecture=='B' and gripper=='B':
            from rack_robotics.rg2_parameters import TELESCOPING_PARK_X
            self.park=(TELESCOPING_PARK_X,.55,1.80)
        self.compliant_tool=gripper=='C'
        self.linkage_tool=gripper=='B'
        self.lift_gravity_bias=0.
        if self.linkage_tool and architecture in ('A','B'):
            from pxr import UsdPhysics
            from rack_robotics.kinematics import gravity_position_bias
            # All robot bodies except the fixed frame move with these lift
            # joints. This feedforward uses model mass, not measured contact
            # deflection, and never increases the physical drive force cap.
            moving_mass=sum(UsdPhysics.MassAPI(p).GetMassAttr().Get() for p in stage.Traverse()
                if str(p.GetPath()).startswith(ROOT+'/') and str(p.GetPath())!=ROOT+'/Frame'
                and p.HasAPI(UsdPhysics.MassAPI))
            gravity=UsdPhysics.Scene(stage.GetPrimAtPath('/World/Physics')).GetGravityMagnitudeAttr().Get()
            self.lift_gravity_bias=gravity_position_bias(moving_mass,
                drives['z'].GetStiffnessAttr().Get(),drives['z'].GetMaxForceAttr().Get(),gravity)
            lift=UsdPhysics.PrismaticJoint(drives['z'].GetPrim())
            self.lift_limits=(lift.GetLowerLimitAttr().Get(),lift.GetUpperLimitAttr().Get())
        self.deflection_filter=DeflectionFilter()
        if self.compliant_tool: self.park=(self.park[0],self.park[1],1.795)
        self.target=self.park
        self.phase='initialize'
        self.transverse_force_limit=None
        self.x_force_limits={name:drive.GetMaxForceAttr().Get()
                             for name,drive in drives.items() if name in ('x','x_outer','x_inner')}

    def set_task_phase(self,phase):
        self.phase=phase
        self.transverse_force_limit=(5. if self.compliant_tool and phase in
            ('align_datum','grasp','release_latch','recover_latch_reset') else None)
        # Serial telescoping axes transmit the same axial load; this is a
        # per-axis drive cap, not a claimed bound on contact impulse peaks.
        for name,limit in self.x_force_limits.items():
            self.drives[name].GetMaxForceAttr().Set(
                min(limit,self.transverse_force_limit) if self.transverse_force_limit is not None else limit)

    def command(self,tcp):
        x,y,z=map(float,tcp)
        commanded=(x,y,z)
        if self.compliant_tool:
            # Measured flange-to-tool deflection compensates static spring sag
            # through joint targets only. No tool/connector transforms are set.
            mount=pose(self.stage,ROOT+'/ToolMount')
            actual=self.tcp()
            nominal=(mount[0],mount[1]-TOOL_OFFSET,mount[2])
            # Learn gravity sag only in free space. During manipulation retain
            # that equilibrium so compensation does not wind up against contact
            # and cancel the deliberately passive wrist. Raw guard stays live.
            offset=self.deflection_filter.update(nominal,actual,self.control_dt,
                adapt=self.phase in ('initialize','approach','park'))
            filtered=tuple(a-b for a,b in zip(nominal,offset))
            coordinates=compliant_joint_coordinates(self.architecture,commanded,
                nominal,filtered,TOOL_OFFSET)
        elif self.linkage_tool:
            # Compensate the measured finger-linkage axial movement through the
            # actual insertion joint. Never set tool or connector body poses.
            mount=pose(self.stage,ROOT+'/ToolMount')
            nominal=(mount[0],mount[1]-TOOL_OFFSET,mount[2])
            actual=self.tcp()
            if max(abs(a-b) for a,b in zip(nominal,actual))>.0025:
                raise RuntimeError(f'RG2 shoe displacement exceeded the calibrated narrow-angle range: nominal={nominal}, measured={actual}')
            coordinates=compliant_joint_coordinates(self.architecture,commanded,nominal,actual,TOOL_OFFSET)
        else: coordinates=joint_coordinates(self.architecture,commanded,TOOL_OFFSET)
        if self.lift_gravity_bias:
            lo,hi=self.lift_limits
            coordinates['z']=max(lo,min(hi,coordinates['z']+self.lift_gravity_bias))
        for name,value in coordinates.items():
            self.drives[name].GetTargetPositionAttr().Set(value)
        self.target=(x,y,z)

    def tcp(self):
        if self.linkage_tool:
            left=pose(self.stage,ROOT+'/LeftJaw'); right=pose(self.stage,ROOT+'/RightJaw')
            return tuple((a+b)/2 for a,b in zip(left,right))
        if self.compliant_tool:
            from pxr import UsdGeom, Gf
            xf=UsdGeom.Xformable(self.stage.GetPrimAtPath(ROOT+'/ToolFrame')).ComputeLocalToWorldTransform(0)
            return tuple(xf.Transform(Gf.Vec3d(0,-TOOL_OFFSET,0)))
        p=pose(self.stage,ROOT+'/ToolMount')
        return (p[0],p[1]-TOOL_OFFSET,p[2])

    def error(self):
        return max(abs(a-b) for a,b in zip(self.tcp(),self.target))
