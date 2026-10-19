"""Small native USD authoring helpers; no external geometry framework."""
import math
from pxr import UsdGeom, UsdShade, Sdf, Gf, UsdPhysics, PhysxSchema

def xform(stage, path, pos=(0,0,0)):
    p = UsdGeom.Xform.Define(stage, path)
    p.AddTranslateOp().Set(Gf.Vec3d(*pos))
    return p

def material(stage, name, color, metallic=0, roughness=.4, emission=None):
    m = UsdShade.Material.Define(stage, '/World/Materials/' + name)
    s = UsdShade.Shader.Define(stage, str(m.GetPath()) + '/Surface')
    s.CreateIdAttr('UsdPreviewSurface')
    for key, value, typ in [('diffuseColor',Gf.Vec3f(*color),Sdf.ValueTypeNames.Color3f),
                            ('metallic',metallic,Sdf.ValueTypeNames.Float),
                            ('roughness',roughness,Sdf.ValueTypeNames.Float)]:
        s.CreateInput(key, typ).Set(value)
    if emission:
        s.CreateInput('emissiveColor', Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*emission))
    m.CreateSurfaceOutput().ConnectToSource(s.ConnectableAPI(), 'surface')
    return m

def bind(prim, mat):
    UsdShade.MaterialBindingAPI.Apply(prim).Bind(mat)

def collision(prim, offset=.00005):
    UsdPhysics.CollisionAPI.Apply(prim)
    api = PhysxSchema.PhysxCollisionAPI.Apply(prim)
    api.CreateContactOffsetAttr(offset)
    api.CreateRestOffsetAttr(0)

def box(stage, path, pos, size, mat=None, collide=False):
    p = UsdGeom.Cube.Define(stage, path)
    p.CreateSizeAttr(1)
    p.AddTranslateOp().Set(Gf.Vec3d(*pos))
    p.AddScaleOp().Set(Gf.Vec3f(*size))
    if mat: bind(p.GetPrim(), mat)
    if collide: collision(p.GetPrim())
    return p

def cylinder(stage, path, pos, radius, height, mat, axis='Y'):
    p = UsdGeom.Cylinder.Define(stage, path)
    p.CreateRadiusAttr(radius)
    p.CreateHeightAttr(height)
    p.CreateAxisAttr(axis)
    p.AddTranslateOp().Set(Gf.Vec3d(*pos))
    bind(p.GetPrim(), mat)
    return p

def curve(stage, path, points, radius, mat):
    if len(points)==4:
        control=[Gf.Vec3d(*p) for p in points]
        points=[]
        for i in range(33):
            t=i/32; s=1-t
            points.append(control[0]*s**3+control[1]*3*s*s*t+control[2]*3*s*t*t+control[3]*t**3)
    c = UsdGeom.BasisCurves.Define(stage, path)
    c.CreateTypeAttr('linear')
    c.CreateCurveVertexCountsAttr([len(points)])
    c.CreatePointsAttr([Gf.Vec3f(*p) for p in points])
    c.CreateWidthsAttr([2*radius])
    c.SetWidthsInterpolation('constant')
    bind(c.GetPrim(), mat)
    return c

def rigid(prim, mass):
    UsdPhysics.RigidBodyAPI.Apply(prim)
    m = UsdPhysics.MassAPI.Apply(prim)
    m.CreateMassAttr(mass)
    p = PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
    p.CreateSolverPositionIterationCountAttr(128)
    p.CreateSolverVelocityIterationCountAttr(8)
    p.CreateEnableCCDAttr(True)
    p.CreateLinearDampingAttr(.15)
    p.CreateAngularDampingAttr(.15)
    return p

def grille(stage, path, center, width, height, nx, nz, mat, depth=.002):
    """Open lattice with real holes, grouped as a single mesh."""
    points, counts, indices = [], [], []
    cx, cy, cz = center
    # Surface bars have thickness, so their holes remain visible at oblique angles.
    specs = [(cx-width/2+i*width/nx, cy, cz, .0012, depth, height) for i in range(nx+1)]
    specs += [(cx, cy, cz-height/2+i*height/nz, width, depth, .0012) for i in range(nz+1)]
    for x,y,z,w,d,h in specs:
        base = len(points)
        points += [(x+a*w/2,y+b*d/2,z+c*h/2) for a,b,c in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
            counts.append(4); indices.extend(base+i for i in f)
    mesh = UsdGeom.Mesh.Define(stage,path)
    mesh.CreatePointsAttr(points); mesh.CreateFaceVertexCountsAttr(counts); mesh.CreateFaceVertexIndicesAttr(indices)
    mesh.CreateSubdivisionSchemeAttr('none'); bind(mesh.GetPrim(),mat)
    return mesh
