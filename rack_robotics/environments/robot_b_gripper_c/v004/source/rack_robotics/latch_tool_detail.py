"""Precision-tool neck clearance correction; connector/boot collisions unchanged."""
from pxr import Gf, UsdGeom

REVISION='precision_forward_latch_neck_v1'


def forward_latch_neck(stage,gripper):
    if gripper!='A':raise ValueError('Forward latch neck revision is for precision tool A')
    root=stage.GetPrimAtPath('/World/Robot')
    if root.GetCustomDataByKey('latch_tool_revision'):raise ValueError('Latch tool already revised')
    path='/World/Robot/LatchTongue/Neck';prim=stage.GetPrimAtPath(path)
    if not prim or not prim.IsA(UsdGeom.Cube):raise ValueError('Missing precision latch neck')
    attr=prim.GetAttribute('xformOp:translate');old=attr.Get()
    if (old-Gf.Vec3d(0,.002,.003)).GetLength()>1e-8:
        raise ValueError('Unexpected neck geometry; requires a new clearance design')
    new=Gf.Vec3d(0,.0005,.003)
    attr.Set(new);root.SetCustomDataByKey('latch_tool_revision',REVISION)
    return {'revision':REVISION,'path':path,'old_local_position_m':list(old),
            'new_local_position_m':list(new),'mass_delta_kg':0.,
            'scope':'Move only the tool neck 1.5 mm toward the socket; unchanged tip, raised arm, drive, joint travel and connector',
            'reason':'480 Hz contact evidence: neck/boot peaks at3.90 N while tip/latch reports zero positive impulse; boot contact blocks depression.',
            'limitations':['Original rigid tool shape, not vendor-qualified tooling or strength analysis.',
                'Nominal neck/arm overlap is0.5 mm; stiffness and fatigue remain unmodeled.',
                'Actual force, retention, pitch/friction variation and repeated-cycle tests still required.']}
