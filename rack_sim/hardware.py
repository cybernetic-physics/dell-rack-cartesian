"""Reference-built XE9680 H100 rear/front modules; dimensions from Dell manuals."""
from pathlib import Path
import math
from pxr import UsdGeom, Gf
from .geometry import box, cylinder, grille, xform, curve, bind
from .labels import label
from .config import SERVER_HEIGHT, REAR_IO_Y

def fan(stage, root, x,y,z, size, mats, grid=True):
    black, steel = mats['black'], mats['steel']
    box(stage,root+'/Housing',(x,y-.008,z),(size,.025,size),black,True)
    cylinder(stage,root+'/Rotor',(x,y+.006,z),size*.38,.004,mats['dark'])
    cylinder(stage,root+'/Hub',(x,y+.009,z),size*.13,.005,black)
    for a in range(7):
        ang=2*math.pi*a/7
        b=box(stage,root+f'/Blade{a}',(x+math.cos(ang)*size*.22,y+.008,z+math.sin(ang)*size*.22),(size*.37,.003,size*.10),black)
        b.AddRotateYOp().Set(-math.degrees(ang)+20)
    if grid:
        grille(stage,root+'/Guard',(x,y+.012,z),size*.9,size*.9,7,7,steel)
    for dx in (-.42,.42):
        for dz in (-.42,.42):
            cylinder(stage,root+f'/Screw{int(dx*100)}_{int(dz*100)}'.replace('-','n'),(x+dx*size,y+.014,z+dz*size),.002,.0015,black)

def passive_rj(stage,root,x,y,z,mats):
    p=xform(stage,root,(x,y,z))
    p.GetPrim().GetReferences().AddReference('/workspace/assets/connectors/socket_cad.usdc')
    bind(p.GetPrim(),mats['steel'])
    box(stage,root+'/DarkBore',(0,-.010,0),(.0118,.001,.0088),mats['black'])
    for i in range(8):
        box(stage,root+f'/Contact{i}',((i-3.5)*.00102,-.006,-.0032),(.0004,.009,.0004),mats['gold'])

def server(stage, root, z0, mats, active=False):
    xform(stage,root,(0,0,z0))
    h=SERVER_HEIGHT
    # No solid box through the target socket. Shell encloses a dark recessed interior.
    box(stage,root+'/Floor',(0,-.02,.002),(.434,.966,.004),mats['steel'],True)
    box(stage,root+'/Lid',(0,-.07,h-.002),(.447,.856,.004),mats['steel'],True)
    for side in (-1,1):
        box(stage,root+f'/Side{side}'.replace('-','n'),(side*.222,-.07,h/2),(.003,.856,h),mats['steel'],True)
        box(stage,root+f'/Ear{side}'.replace('-','n'),(side*.234,-.503,h/2),(.014,.008,h),mats['black'])
        box(stage,root+f'/FrontHandle{side}'.replace('-','n'),(side*.233,-.521,.09),(.009,.015,.09),mats['black'])
    # Rear lower 4U: ten hot-swap GPU fan modules in two rows of five.
    for row in range(2):
        for col in range(5):
            x=(col-2)*.086
            z=.046+row*.088
            f=root+f'/GPUFan{row*5+col+1}'
            fan(stage,f,x,.468,z,.080,mats)
            box(stage,f+'/Latch',(x,.484,z+.031),(.020,.005,.004),mats['orange'])
            box(stage,f+'/PullHandle',(x,.489,z-.032),(.060,.006,.005),mats['steel'])
    # Upper recessed 2U: six PSUs arranged around central I/O, matching Dell Figure 3.
    for i,(x,z) in enumerate([(-.165,.239),(-.165,.197),(-.079,.239),(.079,.239),(.165,.239),(.165,.197)]):
        p=root+f'/PSU{i+1}'
        box(stage,p+'/Face',(x,REAR_IO_Y,z),(.083,.006,.038),mats['steel'])
        fan(stage,p+'/Fan',x-.021,REAR_IO_Y+.004,z,.034,mats,False)
        box(stage,p+'/Inlet',(x+.021,REAR_IO_Y+.007,z),(.027,.008,.027),mats['black'])
        for n,(dx,dz) in enumerate([(-.006,-.004),(.006,-.004),(0,.006)]):
            box(stage,p+f'/Pin{n}',(x+.021+dx,REAR_IO_Y+.012,z+dz),(.002,.003,.004),mats['steel'])
        box(stage,p+'/Release',(x+.038,REAR_IO_Y+.013,z),(.004,.006,.015),mats['orange'])
        # Routed mains lead to vertical PDU, clear of management work area.
        curve(stage,p+'/PowerLead',[(x+.02,REAR_IO_Y+.016,z),(x+.02,.40,z+.02),(x+.025,.53,z+.025),(.265 if x>0 else -.265,.55,z+.04)],.004,mats['rubber'])
    grille(stage,root+'/IOVent',(0,REAR_IO_Y,.208),.22,.024,38,4,mats['steel'])
    # Lower I/O strip: LOM, OCP SFP cages, iDRAC, USB, VGA.
    box(stage,root+'/IOBack',(0,REAR_IO_Y-.025,.181),(.23,.002,.030),mats['dark'])
    for i in range(2): passive_rj(stage,root+f'/LOM{i}',-.080+i*.016,REAR_IO_Y+.003,.181,mats)
    for i in range(2):
        x=-.025+i*.025
        box(stage,root+f'/OCPCage{i}',(x,REAR_IO_Y+.001,.181),(.022,.025,.013),mats['steel'])
        box(stage,root+f'/OCPBore{i}',(x,REAR_IO_Y+.014,.181),(.019,.001,.010),mats['black'])
    if not active: passive_rj(stage,root+'/iDRAC',.066,REAR_IO_Y+.003,.181,mats)
    for i in range(2):
        box(stage,root+f'/USB{i}',(.084,REAR_IO_Y+.004,.177+i*.007),(.012,.010,.005),mats['steel'])
        box(stage,root+f'/USBCore{i}',(.084,REAR_IO_Y+.010,.177+i*.007),(.010,.001,.002),mats['blue'] if i else mats['black'])
    box(stage,root+'/VGA',(.106,REAR_IO_Y+.004,.181),(.020,.009,.008),mats['blue'])
    label(stage,root+'/iDRACLabel','iDRAC9',(.066,REAR_IO_Y+.004,.196),.026,.004)
    label(stage,root+'/RearLabel','DELL  |  XE9680',(0,REAR_IO_Y+.004,.256),.067,.007)
    # Front upper 2U: eight NVMe caddies, perforations; lower area: ten PCIe slots.
    for i in range(8):
        col=i%4; row=i//4; x=(col-1.5)*.102; z=.241-row*.021
        p=root+f'/NVMe{i}'
        box(stage,p+'/Caddy',(x,-.505,z),(.093,.018,.019),mats['black'])
        grille(stage,p+'/Vent',(x,-.515,z),.078,.014,15,2,mats['dark'])
        box(stage,p+'/Release',(x-.038,-.518,z),(.008,.003,.010),mats['orange'])
        box(stage,p+'/LED',(x+.041,-.518,z),(.002,.002,.004),mats['green'])
    grille(stage,root+'/FrontMidVent',(0,-.506,.196),.42,.025,65,4,mats['black'])
    box(stage,root+'/FrontLowerBack',(0,-.493,.088),(.427,.003,.167),mats['black'])
    for i in range(10):
        x=(i-4.5)*.040
        box(stage,root+f'/PCIe{i}',(x,-.509,.09),(.020,.003,.146),mats['steel'])
        grille(stage,root+f'/PCIeVent{i}',(x,-.512,.09),.014,.13,2,22,mats['dark'])
    label(stage,root+'/FrontLabel','DELL  PowerEdge XE9680',(0,-.519,.173),.19,.012,front=True)

def rack_frame(stage,root,mats):
    xform(stage,root)
    for x in (-.285,.285):
        for y in (-.575,.575):
            box(stage,root+f'/Post_{x}_{y}'.replace('-','n').replace('.','p'),(x,y,1.05),(.030,.030,2.10),mats['black'],True)
    for z in (.06,2.08):
        box(stage,root+f'/Cap{z}'.replace('.','p'),(0,0,z),(.60,1.2,.04),mats['black'],True)
    for i,x in enumerate((-.298,.298)):
        box(stage,root+f'/SidePanel{i}',(x,0,1.06),(.003,1.14,1.96),mats['black'],True)
        for j,y in enumerate((-.48,.48)):
            cylinder(stage,root+f'/Caster{i}_{j}',(x*.86,y,.026),.026,.020,mats['rubber'],'X')
    for x in (-.24,.24):
        for y in (-.50,.47):
            p=root+f'/Rail_{x}_{y}'.replace('-','n').replace('.','p')
            grille(stage,p,(x,y,1.055),.018,1.867,2,126,mats['steel'])
    for x in (-.27,.27):
        p=root+f'/PDU{x}'.replace('-','n').replace('.','p')
        box(stage,p+'/Body',(x,.535,1.05),(.030,.050,1.78),mats['black'])
        for i in range(24):
            box(stage,p+f'/Outlet{i}',(x,.564,.24+i*.069),(.021,.005,.026),mats['dark'])
    label(stage,root+'/Nameplate','DELL  |  GPU COMPUTE 01',(0,.602,2.065),.38,.035)
    for i,z in enumerate((.13,.175,.22,1.57,1.94,1.985)):
        box(stage,root+f'/BlankPanel{i}',(0,-.507,z),(.482,.006,.043),mats['black'])
        for x in (-.233,.233):
            cylinder(stage,root+f'/BlankScrew{i}_{x}'.replace('-','n').replace('.','p'),(x,-.512,z),.0026,.002,mats['steel'])

def switches(stage,root,mats,functional_row=False):
    for row,z in enumerate((1.66,1.72)):
        p=root+f'/Switch{row}'
        # Leave 24 mm behind the active mouth free of the chassis collider.
        box(stage,p+'/Chassis',(0,.188 if row==0 and functional_row else .20,z),
            (.44,.426 if row==0 and functional_row else .45,.043),mats['dark'],True)
        for i in range(16):
            x=(i-7.5)*.025
            if row==0:
                if not functional_row: passive_rj(stage,p+f'/RJ45_{i}',x,.429,z,mats)
            else:
                box(stage,p+f'/QSFP_{i}',(x,.429,z),(.020,.015,.012),mats['steel'])
                box(stage,p+f'/QSFP_Bore{i}',(x,.437,z),(.017,.001,.009),mats['black'])
        label(stage,p+'/Label','MANAGEMENT GbE' if row==0 else '100 GbE  |  QSFP28',(0,.438,z+.016),.19,.005)
