"""Extract the MIT-licensed RJ45 socket visual, correcting its mm mesh coordinates."""
from pathlib import Path
import shutil
from pxr import Usd, UsdGeom, Gf

repo = Path('vendor/RJ45-Newton-Insertion')
source = repo / 'assets/socket/rj51_socket_usda/rj51_socket/rj51_socket.usda'
stage = Usd.Stage.Open(str(source))
mesh = next(UsdGeom.Mesh(p) for p in stage.Traverse() if p.GetTypeName() == 'Mesh' and '/visuals/' in str(p.GetPath()))
dest = Path('assets/connectors/socket_cad.usdc')
dest.parent.mkdir(parents=True, exist_ok=True)
out = Usd.Stage.CreateNew(str(dest))
root = UsdGeom.Xform.Define(out, '/SocketCAD')
out.SetDefaultPrim(root.GetPrim())
UsdGeom.SetStageMetersPerUnit(out, 1)
UsdGeom.SetStageUpAxis(out, 'Z')
m = UsdGeom.Mesh.Define(out, '/SocketCAD/Shell')
# Source mesh opening is at y=0. Reorient to face +Y, with bore centered on z=0.
m.CreatePointsAttr([Gf.Vec3f((7.65-p[0])*.001, -p[1]*.001, (p[2]-9.35)*.001) for p in mesh.GetPointsAttr().Get()])
m.CreateFaceVertexCountsAttr(mesh.GetFaceVertexCountsAttr().Get())
m.CreateFaceVertexIndicesAttr(mesh.GetFaceVertexIndicesAttr().Get())
m.CreateSubdivisionSchemeAttr('none')
m.CreateDisplayColorAttr([(.5, .52, .55)])
out.GetRootLayer().Save()
shutil.copyfile(repo / 'LICENSE', dest.parent / 'RJ45-Newton-Insertion-LICENSE.txt')
print(dest)
