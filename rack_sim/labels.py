"""Rasterized equipment labels, rendered on correctly scaled USD planes."""
from pathlib import Path
import hashlib
from PIL import Image, ImageDraw, ImageFont
from pxr import UsdGeom, UsdShade, Sdf, Gf
from .geometry import bind

def label(stage, path, text, pos, width, height, front=False):
    folder = Path('/workspace/assets/labels')
    folder.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(text.encode()).hexdigest()[:16]
    file = folder / (digest + '.png')
    if not file.exists():
        im = Image.new('RGB', (256 if len(text)<=3 else 1024, 128), (24,27,31))
        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 64)
        draw.text((22, 22), text, font=font, fill=(218,224,230))
        im.save(file)
    x,y,z=pos
    # Facing toward rear (+Y), or front (-Y).
    w=width/2; h=height/2
    m = UsdGeom.Mesh.Define(stage,path)
    pts=[(x-w,y,z-h),(x+w,y,z-h),(x+w,y,z+h),(x-w,y,z+h)]
    m.CreatePointsAttr(pts); m.CreateFaceVertexCountsAttr([4]); m.CreateFaceVertexIndicesAttr([0,1,2,3])
    m.CreateDoubleSidedAttr(True); m.CreateSubdivisionSchemeAttr('none')
    uv = UsdGeom.PrimvarsAPI(m).CreatePrimvar('st',Sdf.ValueTypeNames.TexCoord2fArray,'vertex')
    uv.Set([(1,0),(0,0),(0,1),(1,1)] if not front else [(0,0),(1,0),(1,1),(0,1)])
    mat = UsdShade.Material.Define(stage, '/World/Materials/Label_' + digest)
    shader=UsdShade.Shader.Define(stage,str(mat.GetPath())+'/Surface'); shader.CreateIdAttr('UsdPreviewSurface')
    tex=UsdShade.Shader.Define(stage,str(mat.GetPath())+'/Texture'); tex.CreateIdAttr('UsdUVTexture')
    tex.CreateInput('file',Sdf.ValueTypeNames.Asset).Set(str(file))
    tex.CreateInput('sourceColorSpace',Sdf.ValueTypeNames.Token).Set('sRGB')
    uvread=UsdShade.Shader.Define(stage,str(mat.GetPath())+'/UV'); uvread.CreateIdAttr('UsdPrimvarReader_float2')
    uvread.CreateInput('varname',Sdf.ValueTypeNames.Token).Set('st')
    tex.CreateInput('st',Sdf.ValueTypeNames.Float2).ConnectToSource(uvread.ConnectableAPI(),'result')
    shader.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).ConnectToSource(tex.ConnectableAPI(),'rgb')
    shader.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(.65)
    mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(),'surface'); bind(m.GetPrim(),mat)
