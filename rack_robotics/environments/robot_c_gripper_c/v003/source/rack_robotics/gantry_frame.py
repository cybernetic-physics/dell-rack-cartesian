"""CoreXZ guide cross-sections and structural clearances, authored before physics.

No joint, TCP, collision filter or connector changes. The simple U-section is
an explicit raceway abstraction, not HIWIN ball-return geometry or bearing FEA.
"""
import math
from pxr import Gf, UsdGeom, UsdPhysics
from rack_robotics.hardware_detail import Hardware, ROOT

REVISION = 'corexz_open_guide_frame_v2'
GUIDE_SOURCE = 'https://www.hiwin.de/en/Products/Linear-guideways/Blocks/Miniature-guides/MGN-HIRES-series/c/4500'


def open_mgn12h(hardware, path, base, travel_axis, outward_axis, sign):
    """Dimensioned 27x45.4 block, H=13, H1=3 above rail mounting plane.

    A 12.2 mm channel over the 12x8 rail has 0.1 mm nominal clearance.
    The prismatic joint carries the bearing load; collisions remain on all
    three solid pieces. Existing rigid-body bearing mass is retained.
    """
    if travel_axis == outward_axis or sign not in (-1, 1):
        raise ValueError('Invalid guide orientation')
    width_axis = ({0, 1, 2} - {travel_axis, outward_axis}).pop()
    before = dict(hardware.added_mass)
    volume = .0454 * (.027 * .0049 + 2 * .0074 * .0051)
    for name, lateral, height, width, thickness in (
            ('Crown', 0., .01055, .027, .0049),
            ('Side0', -.0098, .00555, .0074, .0051),
            ('Side1', .0098, .00555, .0074, .0051)):
        center = list(base); size = [0., 0., 0.]
        center[outward_axis] += sign * height
        center[width_axis] += lateral
        size[travel_axis] = .0454
        size[outward_axis] = thickness; size[width_axis] = width
        hardware.box(path+'/'+name, center, size,
                     reference_mass=.054 * math.prod(size)/volume)
    # Replacement, not three additional bearings. Preserve already allocated
    # bearing/lumped-body mass; these records expose the nominal distribution.
    hardware.added_mass = before


def complete_gantry_frame(stage, architecture):
    robot = stage.GetPrimAtPath(ROOT)
    if architecture != 'C':
        raise ValueError('This frame revision is specific to CoreXZ architecture C')
    if not robot or not robot.GetCustomDataByKey('insertion_revision'):
        raise ValueError('Open insertion stage required')
    if robot.GetCustomDataByKey('service_carrier_revision'):
        raise ValueError('Old carrier brackets require compatible routing first')
    if robot.GetCustomDataByKey('gantry_frame_revision'):
        raise ValueError('Gantry frame already revised')
    h = Hardware(stage); changes = []; delta = {}
    frame = ROOT+'/Frame'; bridge = ROOT+'/Bridge'; carriage = ROOT+'/Carriage'

    def resize(path, center, size, density=2700.):
        prim = stage.GetPrimAtPath(path)
        if not prim or not prim.IsA(UsdGeom.Cube):
            raise ValueError('Expected frame cube: '+path)
        old_size = [v*UsdGeom.Cube(prim).GetSizeAttr().Get()
                    for v in prim.GetAttribute('xformOp:scale').Get()]
        owner = prim.GetParent()
        while not owner.HasAPI(UsdPhysics.RigidBodyAPI): owner = owner.GetParent()
        mass = (math.prod(size)-math.prod(old_size))*density
        key = str(owner.GetPath()); delta[key] = delta.get(key, 0.)+mass
        prim.GetAttribute('xformOp:translate').Set(Gf.Vec3d(*center))
        UsdGeom.Cube(prim).GetSizeAttr().Set(1.)
        prim.GetAttribute('xformOp:scale').Set(Gf.Vec3f(*size))
        changes.append({'path':path,'old_size_m':old_size,'new_size_m':list(size),
                        'mass_delta_kg':mass,'density_kg_m3':density})

    def shift(path, dz):
        prim = stage.GetPrimAtPath(path)
        if not prim or not prim.IsA(UsdGeom.Xformable):
            raise ValueError('Missing transformable frame part: '+path)
        attr = prim.GetAttribute('xformOp:translate')
        attr.Set(attr.Get()+Gf.Vec3d(0, 0, dz))
        changes.append({'path':path,'translation_delta_m':[0,0,dz]})

    # Rear beam ends before the uprights. Raising the lift blocks 50 mm above
    # the beam leaves their actual M3 mounting pattern accessible, outside the
    # traverse block sweep. A continuous stepped bracket reaches each block.
    resize(bridge+'/Beam', (0,0,0), (.470,.032,.040))
    h.box(bridge+'/GuideInterfaces/TraverseRailShim',(0,-.0165,0),(.470,.001,.012))
    for index, x in enumerate((-.26,.26)):
        old = stage.GetPrimAtPath(bridge+f'/GuideBlock{index}')
        if not old or not old.IsA(UsdGeom.Cube): raise ValueError('Missing lift block')
        old.SetActive(False)
        open_mgn12h(h, bridge+f'/GuideInterfaces/LiftBlock{index}',
                   (x,-.006,.050), 2, 1, -1)
        h.box(bridge+f'/GuideInterfaces/LowerArm{index}',
              ((-1,1)[index]*.24675,-.0185,.0305),(.0535,.007,.006))
        h.box(bridge+f'/GuideInterfaces/ArmRiser{index}',
              ((-1,1)[index]*.2305,-.0135,.0175),(.009,.005,.035))
        h.box(bridge+f'/GuideInterfaces/BlockPlate{index}',
              (x,-.022,.050),(.027,.006,.0454))
        for row,dz in enumerate((-.010,.010)):
            for col,dx in enumerate((-.010,.010)):
                h.bolt(bridge+f'/GuideInterfaces/BlockBolt{index}_{row}_{col}',
                       (x+dx,-.02025,.050+dz),'Y',.0015,.0095)
        h.box(frame+f'/GuideInterfaces/RailShim{index}',
              (x,.7145,1.45),(.012,.001,.92))
        # At the unchanged software limits the blocks have 1 mm travel margin
        # to each physical stop; the original lower stop overlapped the block.
        for k,z in enumerate((1.1223,1.8777)):
            resize(frame+f'/Stop{index}_{k}',(x,.709,z),(.023,.010,.008))
        # Move the COMPLETE upper rack attachment to the top crossmember,
        # outside the raised insertion stage's swept volume.
        for path in (frame+f'/Standoff{index}_1',frame+f'/PostClamp{index}_1',
                     frame+f'/RackBolt{index}_1_0',frame+f'/RackBolt{index}_1_1'):
            shift(path,.025)
    for index,x in enumerate((-.025,.025)):
        old = stage.GetPrimAtPath(carriage+f'/TraverseBlock{index}')
        if not old or not old.IsA(UsdGeom.Cube): raise ValueError('Missing traverse block')
        old.SetActive(False)
        open_mgn12h(h,carriage+f'/GuideInterfaces/TraverseBlock{index}',
                   (x,.023,0),0,1,-1)
    for owner,mass in h.added_mass.items(): delta[owner] = delta.get(owner,0.)+mass
    for owner,mass in delta.items():
        attr = UsdPhysics.MassAPI(stage.GetPrimAtPath(owner)).GetMassAttr()
        if attr.Get()+mass <= 0: raise ValueError('Nonpositive revised body mass')
        attr.Set(attr.Get()+mass)
    robot.SetCustomDataByKey('gantry_frame_revision',REVISION)
    return {'revision':REVISION,'architecture':architecture,'changes':changes,
            'parts':h.parts,'mass_delta_kg_by_body':delta,'guide_dimensions_source':GUIDE_SOURCE,
            'scope':'CoreXZ lift/traverse guide and beam interfaces; unchanged kinematics/controller/connector',
            'limitations':['U channels abstract recirculating balls/races; prismatic joints carry bearing loads.',
                '0.1 mm channel clearance is a modeling assumption, not manufacturer bearing clearance.',
                'Replacement block mass remains allocated in original rigid-body mass; beam delta uses aluminum volume proxy.',
                'Not full-rack, non-box, carrier, belt-wrap, stiffness or fastener qualification.']}
