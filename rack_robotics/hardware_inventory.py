"""Read-only component inventory from cooked saved-model geometry.

Counts are model components, not a purchasable or manufacturing-ready BOM.
Composite guide blocks and carrier links are counted once, not per solid.
"""
import math
from pathlib import PurePosixPath
import re


def component(path):
    parts = PurePosixPath(path).parts
    name = parts[-1]
    if 'ServiceCarriers' in parts:
        for i, part in enumerate(parts):
            if re.fullmatch(r'Link\d+', part):
                return 'carrier_links', str(PurePosixPath(*parts[:i+1]))
    if 'GuideInterfaces' in parts and name in ('Crown', 'Side0', 'Side1'):
        if re.fullmatch(r'(Lift|Traverse|Horizontal)Block[\d_]+', parts[-2]):
            return 'guide_blocks', str(PurePosixPath(path).parent)
    if re.fullmatch(r'DepthBlock\d+', name): return 'guide_blocks', path
    if re.fullmatch(r'(Guide|VerticalGuide|DepthRail)\d+|XGuide|HorizontalGuide', name):
        return 'linear_rails', path
    if re.fullmatch(r'Screw\d*|XScrew|LiftScrew|DepthScrew', name):
        return 'screw_shafts', path
    if re.fullmatch(r'Motor\d*|XMotor|LiftMotor|DepthMotor|StationaryMotor\d+', name):
        return 'axis_motor_envelopes', path
    if 'Brakes' in parts and name == 'Housing':
        return 'brake_housings', str(PurePosixPath(path).parent)
    if name.startswith('PostClamp'): return 'rack_clamps', path
    if re.fullmatch(r'Upright\d*|Beam|Boom', name): return 'structural_members', path
    if 'Bolt' in name: return 'fastener_markers', path
    return 'other_geometry', path


def inventory(properties):
    if properties.get('passed') is not True: raise ValueError('Property query did not pass')
    grouped = {}; seen = set()
    for owner, body in properties['bodies'].items():
        if not owner.startswith('/World/Robot/'): raise ValueError('Nonrobot body')
        for shape in body['geometry']:
            path = shape['path']
            if path in seen or not path.startswith(owner+'/'):
                raise ValueError('Duplicate or unowned geometry: '+path)
            seen.add(path)
            lower, upper = shape['lower_m'], shape['upper_m']
            if (len(lower) != 3 or len(upper) != 3
                    or not all(math.isfinite(v) for v in lower+upper)
                    or any(a>b for a,b in zip(lower,upper))):
                raise ValueError('Invalid geometry bounds: '+path)
            category, identity = component(path)
            key = (category, identity)
            row = grouped.setdefault(key, {'category':category,'component_path':identity,
                'rigid_owner':owner,'geometry_paths':[],'lower_body_m':list(lower),
                'upper_body_m':list(upper)})
            if row['rigid_owner'] != owner: raise ValueError('Composite spans rigid owners')
            row['geometry_paths'].append(path)
            row['lower_body_m'] = [min(a,b) for a,b in zip(row['lower_body_m'],lower)]
            row['upper_body_m'] = [max(a,b) for a,b in zip(row['upper_body_m'],upper)]
    rows = sorted(grouped.values(), key=lambda row:(row['category'],row['component_path']))
    for row in rows:
        row['body_aligned_size_mm'] = [1000*(b-a) for a,b in zip(row['lower_body_m'],row['upper_body_m'])]
        row['unit_price_usd'] = None
    counts = {category:sum(row['category']==category for row in rows)
              for category in sorted({row['category'] for row in rows})}
    rails = [row for row in rows if row['category']=='linear_rails']
    return {'schema':'saved_model_hardware_inventory_v1','robot':properties['robot'],
        'gripper':properties['gripper'],'component_counts':counts,'geometry_records':len(seen),
        'total_modeled_rail_length_m':sum(max(row['body_aligned_size_mm'])/1000 for row in rails),
        'components':rows,'complete_purchase_cost_usd':None,
        'scope':'Body-aligned bounds and component counts from the named saved model; not fabrication dimensions or a purchase-ready BOM',
        'limitations':[
            'Guide block solids and carrier link solids are grouped; detailed bearing internals are abstract.',
            'Fastener markers are not a complete bolt/nut/washer procurement count.',
            'Other geometry includes custom adapters, guards, shafts and tool solids; it is not zero-cost.',
            'Body-aligned bounds may exceed part-local sizes for rotated geometry; holes, tolerances and threads are not manufacturing drawings.',
            'No catalog part or price is inferred from a visual envelope. Complete cost remains unknown.']}
