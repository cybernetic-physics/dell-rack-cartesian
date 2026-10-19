"""Inspect reusable USD assets without dumping mesh arrays."""
import sys
from pxr import Usd, UsdGeom
for filename in sys.argv[1:]:
    s = Usd.Stage.Open(filename)
    cache = UsdGeom.BBoxCache(0, ["default", "render"], useExtentsHint=False)
    print("FILE", filename, "units", UsdGeom.GetStageMetersPerUnit(s), "up", UsdGeom.GetStageUpAxis(s))
    for p in s.Traverse():
        if p.GetTypeName() in ("Xform", "Mesh") and ("plug" in str(p.GetPath()).lower() or "socket" in str(p.GetPath()).lower()):
            b = cache.ComputeWorldBound(p).ComputeAlignedRange()
            print(p.GetPath(), p.GetTypeName(), "bounds", b.GetMin(), b.GetMax())
