"""Physical plug/socket/latch contact; state labels only observe measured motion."""
import math
from pxr import UsdGeom, UsdPhysics, PhysxSchema, Gf, Sdf
from .geometry import xform, box, cylinder, collision, rigid, bind
from .config import CFG
from .latch import create_lip,create_latch,measured_latch

def create_socket(stage, mouth, mats, root='/World/Socket'):
    xform(stage,root,mouth)
    w,h,d=CFG.socket_width,CFG.socket_height,CFG.socket_depth
    # Four independent wall colliders preserve the open cavity (never a convex hull).
    for name,pos,size in [
        ('Left',(-w/2-.001,-d/2,0),(.002,d,h+.004)),
        ('Right',(w/2+.001,-d/2,0),(.002,d,h+.004)),
        ('Floor',(0,-d/2,-h/2-.001),(w,d,.002)),
        ('Ceiling',(0,-d/2,.0078),(w,d,.002)),
        ('Back',(0,-d-.001,0),(w+.004,.002,h+.004))]:
        box(stage,root+'/'+name,pos,size,mats['steel'],True)
    # Collar rails and keyed slot. Male key is on top, so an inverted plug collides.
    for sign in (-1,1):
        box(stage,root+f'/KeyShoulder{sign}'.replace('-','n'),(sign*.0044,-.006,.0040),(.0034,.012,.001),mats['dark'],True)
    create_lip(stage,root,mats)
    for i in range(8):
        box(stage,root+f'/Contact{i}',((i-3.5)*.00102,-.007,-.0037),(.00045,.008,.00025),mats['gold'])
    led=box(stage,root+'/LinkLED',(-.0069,.0005,.0060),(.0015,.001,.001),mats['green'])
    led.CreateVisibilityAttr('invisible')
    return root

def create_plug(stage, pos, mats):
    root='/World/Plug'
    p=xform(stage,root,pos)
    rigid(p.GetPrim(),CFG.mass)
    # The lower shell is 7.2 mm high; the centered key/clip fits the top relief.
    box(stage,root+'/Body',(0,0,-.0005),(CFG.width,CFG.length,.0072),mats['plug'],True)
    box(stage,root+'/Key',(0,-.003,.0035),(.004,.014,.0014),mats['plug'],True)
    box(stage,root+'/Boot',(0,.014,0),(.010,.010,.009),mats['blue'],True)
    for i in range(5):
        box(stage,root+f'/BootRib{i}',(0,.011+i*.0017,0),(.0108,.0007,.0096),mats['blue'])
    for i in range(8):
        box(stage,root+f'/GoldContact{i}',((i-3.5)*.00102,-.006,-.0041),(.0005,.008,.0002),mats['gold'])
        box(stage,root+f'/Wire{i}',((i-3.5)*.0009,.003,-.002),(.00065,.011,.00065),mats['gold'] if i%2 else mats['blue'])
    create_latch(stage,pos,mats)
    return root

class Interaction:
    def __init__(self,stage,mouth,ports=None):
        self.stage=stage; self.origin=Gf.Vec3d(*mouth)
        self.ports=ports or [('/World/Socket',mouth)]
        self.port_index=0; self.mouth=Gf.Vec3d(*mouth)
        self.visited_ports=set()
        self.state='unplugged'; self.clip_pressed=False; self.dwell=0.; self.cycles=0
        self.events=[]; self.time=0.; self.last_position=None
        self.press_drive=UsdPhysics.DriveAPI(stage.GetPrimAtPath('/World/ClipPressSlide'),'linear')
        self.joint=UsdPhysics.Joint.Define(stage,'/World/HandDrive')
        self.joint.CreateBody1Rel().SetTargets(['/World/Plug'])
        self.joint.CreateLocalPos0Attr(Gf.Vec3f(*mouth))
        self.drives={}
        for axis in ('transX','transY','transZ','rotX','rotY','rotZ'):
            d=UsdPhysics.DriveAPI.Apply(self.joint.GetPrim(),axis)
            d.CreateTypeAttr('force'); d.CreateTargetPositionAttr(0)
            linear=axis.startswith('trans')
            d.CreateStiffnessAttr(CFG.drive_stiffness if linear else .15)
            d.CreateDampingAttr(CFG.drive_damping if linear else .01)
            d.CreateMaxForceAttr(CFG.drive_max_force if linear else .08)
            self.drives[axis]=d
        self.target=[0,.05,0]
        self.set_target(self.target)

    @property
    def connected_port(self):
        return self.port_index if self.state=='retained' else None

    def port_target(self,index,clearance=.05):
        """Drive target relative to a fixed world anchor, never a body teleport."""
        delta=Gf.Vec3d(*self.ports[index][1])-self.origin
        return [delta[0],delta[1]+clearance,delta[2]]

    def update_indicators(self):
        for index,(path,_) in enumerate(self.ports):
            connected=index==self.connected_port
            self.stage.GetPrimAtPath(path+'/LinkLED').GetAttribute('visibility').Set('inherited' if connected else 'invisible')
            self.stage.GetPrimAtPath(path).CreateAttribute('connector:connected',Sdf.ValueTypeNames.Bool).Set(connected)
        plug=self.stage.GetPrimAtPath('/World/Plug')
        plug.CreateAttribute('connector:port',Sdf.ValueTypeNames.Int).Set(self.connected_port if self.connected_port is not None else -1)

    def set_target(self,offset,angles=(0,0,0)):
        self.target=list(offset)
        for axis,value in zip(('transX','transY','transZ','rotX','rotY','rotZ'),[*offset,*angles]):
            self.drives[axis].GetTargetPositionAttr().Set(float(value))

    def set_grasp(self,enabled):
        self.joint.GetJointEnabledAttr().Set(bool(enabled))

    def reset(self):
        """Reset software state alongside a user-requested timeline reset."""
        self.release(False); self.set_grasp(True); self.set_target((0,.05,0))
        self.transition('unplugged')
        self.time=0.; self.cycles=0; self.dwell=0.; self.last_position=None
        self.events=[]
        self.port_index=0; self.mouth=Gf.Vec3d(*self.ports[0][1])
        self.visited_ports=set(); self.update_indicators()

    def release(self,pressed=True):
        self.clip_pressed=pressed
        self.press_drive.GetTargetPositionAttr().Set(-.005 if pressed else 0.)

    def transition(self,state):
        if state!=self.state:
            self.events.append({'time':round(self.time,4),'from':self.state,'to':state,'port':self.port_index+1})
            print('CONNECTOR',self.events[-1],flush=True)
            self.state=state
            if state=='retained': self.visited_ports.add(self.port_index)
            self.update_indicators()
            self.stage.GetPrimAtPath('/World/Plug').CreateAttribute('connector:state',Sdf.ValueTypeNames.String).Set(state)

    def pose(self):
        m=UsdGeom.Xformable(self.stage.GetPrimAtPath('/World/Plug')).ComputeLocalToWorldTransform(0)
        return m.ExtractTranslation(),m.ExtractRotationQuat()

    def update(self,dt):
        self.time+=dt
        p,q=self.pose()
        # Association comes from measured pose, not the requested destination.
        # Keep the originating port while retained/released until fully extracted.
        if self.state not in ('retained','released'):
            nearest=min(range(len(self.ports)),key=lambda i:
                (p[0]-self.ports[i][1][0])**2+(p[2]-self.ports[i][1][2])**2)
            if nearest!=self.port_index: self.dwell=0.
            self.port_index=nearest
            self.mouth=Gf.Vec3d(*self.ports[nearest][1])
        off=p-self.mouth
        angle=math.degrees(2*math.acos(min(1.,abs(float(q.GetReal())))))
        depth=CFG.length/2-off[1]
        speed=(p-self.last_position).GetLength()/dt if self.last_position is not None else 0.
        self.last_position=p
        self.metrics={'depth_m':depth,'lateral_m':math.hypot(off[0],off[2]),'angle_deg':angle,'speed_m_s':speed,'port':self.port_index+1}
        matrix=UsdGeom.Xformable(self.stage.GetPrimAtPath('/World/Plug')).ComputeLocalToWorldTransform(0)
        self.metrics.update(measured_latch(self.stage,matrix,self.mouth))
        if self.state=='retained':
            # Labels cannot retain anything. A depressed or escaped hook loses retention.
            if self.metrics['hook_clear'] or depth<.009 or self.metrics['lateral_m']>.001:
                self.transition('released')
            else: return
        if depth<-.002:
            if self.state=='released': self.cycles+=1
            self.transition('unplugged'); self.dwell=0
        else:
            # Hysteresis prevents numerical contact jitter from chattering states.
            if self.state!='released':
                if depth>.0003: self.transition('inserting')
                elif depth<-.0003: self.transition('aligned')
            seated=(depth>=CFG.seat_depth and depth<=CFG.socket_depth+.0001
                    and abs(off[0])<CFG.lateral_tolerance and abs(off[2])<CFG.lateral_tolerance
                    and angle<CFG.angular_tolerance_deg and speed<.015 and self.metrics['hook_behind_lip'])
            self.dwell=self.dwell+dt if seated else 0.
            if self.dwell>=CFG.seat_dwell:
                self.transition('retained')
