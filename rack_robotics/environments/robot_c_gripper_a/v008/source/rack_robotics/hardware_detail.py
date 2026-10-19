"""Add dimensioned drive connections BEFORE physics, never during a trial.

Custom manufactured interfaces, not vendor CAD or thread/bearing dynamics.
Existing prismatic joints remain the guide/lead-screw transmission abstraction.
New brackets have collision geometry; bores are visibly open. Additive masses
use aluminum2700/steel7850 kg/m3, excluding fastener threads and bearing races.
"""
import math
from pxr import Gf, Sdf, UsdGeom, UsdPhysics, UsdShade

ROOT = '/World/Robot'


class Hardware:
    def __init__(self, stage):
        self.stage = stage; self.parts = []; self.added_mass = {}

    def record(self, path, volume, density, collide, reference_mass=None):
        parent = str(Sdf.Path(path).GetParentPath())
        while parent != '/' and not self.stage.GetPrimAtPath(parent).HasAPI(UsdPhysics.RigidBodyAPI):
            parent = str(Sdf.Path(parent).GetParentPath())
        if parent == '/': raise ValueError('Part lacks rigid parent: '+path)
        mass = volume*density if reference_mass is None else reference_mass
        self.added_mass[parent] = self.added_mass.get(parent, 0.)+mass
        self.parts.append({'path': path, 'rigid_parent': parent, 'volume_m3': volume,
                           'density_kg_m3': density if reference_mass is None else None,
                           'mass_basis': 'geometric_volume' if reference_mass is None else 'MGN12H catalog block mass',
                           'estimated_mass_kg': mass, 'collision': collide})

    def bind(self, prim):
        mat = UsdShade.Material.Get(self.stage, '/World/Materials/RobotSteel')
        if not mat: raise ValueError('Missing robot steel material')
        UsdShade.MaterialBindingAPI.Apply(prim).Bind(mat)

    def box(self, path, center, size, density=2700., collide=True, reference_mass=None):
        if self.stage.GetPrimAtPath(path): raise ValueError('Hardware already exists: '+path)
        prim = UsdGeom.Cube.Define(self.stage, path)
        prim.CreateSizeAttr(1); prim.AddTranslateOp().Set(Gf.Vec3d(*center))
        prim.AddScaleOp().Set(Gf.Vec3f(*size)); self.bind(prim.GetPrim())
        if collide:
            UsdPhysics.CollisionAPI.Apply(prim.GetPrim())
            # Raw schema names permit file-only tests without Isaac's plugin;
            # Isaac resolves this registered API when the scene is opened.
            prim.GetPrim().AddAppliedSchema('PhysxCollisionAPI')
            prim.GetPrim().CreateAttribute('physxCollision:contactOffset',Sdf.ValueTypeNames.Float).Set(.00005)
            prim.GetPrim().CreateAttribute('physxCollision:restOffset',Sdf.ValueTypeNames.Float).Set(0.)
        self.record(path, math.prod(size), density, collide, reference_mass)

    def sleeve(self, path, center, outer, bore, length, axis='Z', density=7850.):
        """Open annular mesh; visual bearing/thread proxy, not a solid shaft collider."""
        if not 0 < bore < outer or length <= 0: raise ValueError('Invalid sleeve dimensions')
        if self.stage.GetPrimAtPath(path): raise ValueError('Hardware already exists: '+path)
        points = []; axis_index = 'XYZ'.index(axis)
        cross = [i for i in range(3) if i != axis_index]; count = 32
        for axial in (-length/2, length/2):
            for radius in (outer, bore):
                for i in range(count):
                    point = list(center); angle = 2*math.pi*i/count
                    point[axis_index] += axial
                    point[cross[0]] += radius*math.cos(angle); point[cross[1]] += radius*math.sin(angle)
                    points.append(Gf.Vec3f(*point))
        faces = []
        for i in range(count):
            j = (i+1)%count
            faces += [(i,j,2*count+j,2*count+i),
                      (count+j,count+i,3*count+i,3*count+j),
                      (j,i,count+i,count+j),
                      (2*count+i,2*count+j,3*count+j,3*count+i)]
        mesh = UsdGeom.Mesh.Define(self.stage, path)
        mesh.CreatePointsAttr(points); mesh.CreateFaceVertexCountsAttr([4]*len(faces))
        mesh.CreateFaceVertexIndicesAttr([index for face in faces for index in face])
        mesh.CreateSubdivisionSchemeAttr('none'); mesh.CreateDoubleSidedAttr(True)
        self.bind(mesh.GetPrim())
        self.record(path, math.pi*(outer**2-bore**2)*length, density, False)

    def plate(self, path, center, size, axis, hole):
        """Four solid rails leave a real central square clearance opening."""
        axial = 'XYZ'.index(axis); u,v = [i for i in range(3) if i != axial]
        if min(size[u],size[v]) <= hole: raise ValueError('Opening too large')
        for direction in (-1,1):
            c=list(center); s=list(size)
            s[u]=(size[u]-hole)/2; c[u]+=direction*(hole/2+s[u]/2)
            self.box(path+f'/U{direction+1}',c,s)
            c=list(center); s=list(size)
            s[u]=hole; s[v]=(size[v]-hole)/2; c[v]+=direction*(hole/2+s[v]/2)
            self.box(path+f'/V{direction+1}',c,s)

    def bolt(self, path, center, axis='Y', radius=.002, length=.008):
        cylinder = UsdGeom.Cylinder.Define(self.stage, path)
        cylinder.CreateAxisAttr(axis); cylinder.CreateRadiusAttr(radius); cylinder.CreateHeightAttr(length)
        cylinder.AddTranslateOp().Set(Gf.Vec3d(*center)); self.bind(cylinder.GetPrim())
        self.record(path, math.pi*radius**2*length, 7850., False)

    def finish(self, architecture):
        for path, mass in self.added_mass.items():
            attr = UsdPhysics.MassAPI(self.stage.GetPrimAtPath(path)).GetMassAttr()
            if not attr.Get() or attr.Get() <= 0: raise ValueError('Missing authored mass: '+path)
            attr.Set(attr.Get()+mass)
        self.stage.GetPrimAtPath(ROOT).SetCustomDataByKey('hardware_revision', 'drive_connections_v4')
        return {'revision': 'drive_connections_v4', 'architecture': architecture, 'parts': self.parts,
                'added_mass_kg_by_body': self.added_mass,
                'scope': 'Dimensioned motor/guide/screw connections with additive geometric mass estimates; prismatic joint drive abstraction unchanged',
                'remaining': ['Thread contact, bearing races, screw rotation and motor torque-speed dynamics unmodeled',
                              'No certified fastener/rack ratings', 'Cable carriers and powered-off brakes not yet implemented']}


def complete_drive_connections(stage, architecture):
    if architecture not in ('A','B','C'): raise ValueError('Unknown architecture')
    root = stage.GetPrimAtPath(ROOT)
    if not root or root.GetCustomDataByKey('hardware_revision'): raise ValueError('Missing or already revised robot')
    h=Hardware(stage); base=ROOT+'/Frame'; bridge=ROOT+'/Bridge'; carriage=ROOT+'/Carriage'; mount=ROOT+'/ToolMount'
    if architecture == 'A':
        for side,x in enumerate((-.26,.26)):
            # Coaxial lift motor, coupler and original8 mm screw; raised mount
            # connects to the existing upright instead of floating above it.
            stage.GetPrimAtPath(base+f'/Motor{side}').GetAttribute('xformOp:translate').Set(Gf.Vec3d(x+.018,.704,1.9145))
            h.box(base+f'/DriveUprightExtension{side}',(x,.735,1.878),(.04,.04,.016))
            h.plate(base+f'/LiftMotorPlate{side}',(x+.018,.704,1.889),(.065,.065,.006),'Z',.012)
            h.sleeve(base+f'/LiftCoupler{side}',(x+.018,.704,1.866),.007,.0041,.052)
            for k,z in enumerate((1.012,1.836)):
                h.sleeve(base+f'/LiftBearing{side}_{k}',(x+.018,.704,z),.012,.0042,.014)
                h.box(base+f'/LiftBearingSupport{side}_{k}',(x+.018,.725,z),(.026,.022,.016))
            h.sleeve(bridge+f'/LiftNut{side}',(x+.018,-.016,0),.008,.0041,.016)
            h.box(bridge+f'/LiftNutBracket{side}',(x+.009,-.008,0),(.020,.016,.018))
            for i,dx in enumerate((-.0155,.0155)):
                for j,dy in enumerate((-.0155,.0155)):
                    h.bolt(base+f'/LiftMotorBolt{side}_{i}_{j}',(x+.018+dx,.704+dy,1.889),'Z',.0015,.010)
        stage.GetPrimAtPath(bridge+'/XMotor').GetAttribute('xformOp:translate').Set(Gf.Vec3d(.29,-.023,.018))
        h.plate(bridge+'/TraverseMotorPlate',(.2645,-.023,.018),(.006,.060,.055),'X',.012)
        h.sleeve(bridge+'/TraverseCoupler',(.252,-.023,.018),.007,.0041,.025,'X')
        for side,x in enumerate((-.234,.234)):
            h.sleeve(bridge+f'/TraverseBearing{side}',(x,-.023,.018),.011,.0042,.012,'X')
            h.box(bridge+f'/TraverseBearingSupport{side}',(x,-.011,.018),(.016,.018,.025))
        h.sleeve(carriage+'/TraverseNut',(0,.017,.018),.008,.0041,.018,'X')
        h.box(carriage+'/TraverseNutBracket',(0,.009,.018),(.025,.018,.016))
    if architecture in ('A','C'):
        # Two spaced guide blocks now physically connect the traverse plate.
        # Available420 mm stroke +95.4 mm block envelope needs >=515.4 mm rail.
        stage.GetPrimAtPath(bridge+'/XGuide').GetAttribute('xformOp:scale').Set(Gf.Vec3f(.52,.008,.012))
        for index,x in enumerate((-.025,.025)):
            h.box(carriage+f'/TraverseBlock{index}',(x,.0125,0),(.0454,.013,.027),reference_mass=.054)
        h.box(carriage+'/TraverseBackPlate',(0,.006,0),(.100,.010,.028))
    # Common short insertion slide:125 mm stroke plus45.4 mm block length.
    for index,x in enumerate((-.022,.022)):
        rail=stage.GetPrimAtPath(carriage+f'/DepthRail{index}')
        rail.GetAttribute('xformOp:translate').Set(Gf.Vec3d(x,-.070,0))
        rail.GetAttribute('xformOp:scale').Set(Gf.Vec3f(.012,.180,.008))
        h.box(mount+f'/DepthBlock{index}',(x,-.010,.0105),(.027,.0454,.013),reference_mass=.054)
    h.box(mount+'/DepthBearingPlate',(0,-.010,.0205),(.074,.048,.009))
    h.sleeve(mount+'/DepthNut',(0,0,.014),.007,.0031,.012,'Y')
    h.plate(carriage+'/DepthMotorPlate',(0,.0165,.014),(.040,.006,.040),'Y',.009)
    h.sleeve(carriage+'/DepthCoupler',(0,.016,.014),.005,.0031,.016,'Y')
    h.sleeve(carriage+'/DepthSupportBearing',(0,-.132,.014),.007,.0031,.008,'Y')
    # An overhead bearing hanger leaves the full finger/tongue swept channel
    # open. The v2 full plate physically blocked withdrawal through this plane.
    h.box(carriage+'/DepthFrontBearingHanger',(0,-.135,.028),(.018,.008,.014))
    h.box(carriage+'/DepthFrontBearingCrossbar',(0,-.135,.038),(.068,.005,.006))
    for index,x in enumerate((-.031,.031)):
        h.box(carriage+f'/DepthFrontBearingPost{index}',(x,-.135,.0175),(.006,.008,.035))
        h.bolt(carriage+f'/DepthFrontBearingBolt{index}',(x,-.140,.009),'Y',.0015,.012)
    return h.finish(architecture)
