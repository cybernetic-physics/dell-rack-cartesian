"""Read saved nominal cable motion without loading physics or changing scenes."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from rack_robotics.cable_screen import screen_cable


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_geometry(stage):
    from pxr import UsdGeom, UsdPhysics
    cable = stage.GetPrimAtPath('/World/Cable')
    links = sorted((p for p in cable.GetChildren() if p.GetName().startswith('Link')),
                   key=lambda p: p.GetName())
    if not links:
        raise ValueError('No cable links')
    geometry = {'links': []}
    for i, prim in enumerate(links):
        joint = UsdPhysics.Joint(stage.GetPrimAtPath('/World/Cable/Joint%02d' % i))
        parents = [str(p) for p in joint.GetBody0Rel().GetTargets()]
        children = [str(p) for p in joint.GetBody1Rel().GetTargets()]
        expected_parent = '/World/Plug' if i == 0 else str(links[i-1].GetPath())
        if parents != [expected_parent] or children != [str(prim.GetPath())]:
            raise ValueError('Unexpected cable joint topology')
        for axis in ('transX', 'transY', 'transZ'):
            limit = UsdPhysics.LimitAPI(joint.GetPrim(), axis)
            if not limit or limit.GetLowAttr().Get() <= limit.GetHighAttr().Get():
                raise ValueError('Expected locked cable translation')
        if i == 0:
            geometry.update(attachment_body=parents[0],
                            attachment_local=list(joint.GetLocalPos0Attr().Get()))
        elif list(joint.GetLocalPos0Attr().Get()) != geometry['links'][-1]['distal']:
            raise ValueError('Unexpected distal anchor')
        capsule = UsdGeom.Capsule(prim)
        if not capsule or capsule.GetAxisAttr().Get() != 'Y':
            raise ValueError('Expected Y-axis cable capsule')
        proximal = list(joint.GetLocalPos1Attr().Get())
        distal = [-v for v in proximal]
        length = capsule.GetHeightAttr().Get() + 2*capsule.GetRadiusAttr().Get()
        if abs(length - (distal[1]-proximal[1])) > 1e-7:
            raise ValueError('Capsule/anchor length mismatch')
        geometry['links'].append({'path': str(prim.GetPath()),
                                  'proximal': proximal, 'distal': distal})
    return geometry


def main():
    from pxr import Usd
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    plan = json.loads(args.plan.read_text())
    evidence = {str(args.plan): sha(args.plan)}
    results = {}
    for label, case in plan['designs'].items():
        environment = ROOT/case['environment']
        manifest_path = environment/'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        for name, digest in manifest['packaged_file_sha256'].items():
            path = (environment/name).resolve()
            if environment.resolve() not in path.parents or sha(path) != digest:
                raise ValueError('Changed package: ' + str(path))
            evidence[str(path)] = digest
        evidence[str(manifest_path)] = sha(manifest_path)
        result = json.loads((environment/'results.json').read_text())
        if not result['passed']:
            continue
        mask = Usd.StagePopulationMask(['/World/Cable', '/World/Plug'])
        stage = Usd.Stage.OpenMasked(str(environment/'scene.usda'), mask)
        geometry = extract_geometry(stage)
        for layer in stage.GetUsedLayers():
            if layer.realPath:
                evidence[layer.realPath] = sha(Path(layer.realPath))
        with (environment/'trajectory.jsonl').open() as stream:
            header = json.loads(next(stream)); samples = [json.loads(line) for line in stream]
        report = screen_cable(geometry, header, samples)
        report.update(environment=case['environment'], geometry=geometry,
                      environment_manifest_sha256=sha(manifest_path),
                      recorded_physics_step_max_gap_m=result.get('cable_max_gap_m'),
                      units='Recorded world coordinates in metres, as configured by the saved Isaac runner; not inferred from USD default metadata.')
        results[label] = report
    for path, digest in evidence.items():
        if sha(Path(path)) != digest:
            raise ValueError('Input changed during analysis: ' + path)
    args.output.mkdir(parents=True)
    sources = {name: (ROOT/name).read_bytes() for name in (
        'rack_robotics/cable_screen.py', 'rack_robotics/mechanical_screen.py',
        'rack_robotics/scripts/screen_cable_motion.py')}
    for name, data in sources.items():
        target = args.output/'source'/name
        target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
    report = {'schema': 'recorded_nominal_cable_screen_v1', 'designs': results,
              'evidence_sha256': evidence,
              'analysis_sha256': {name: hashlib.sha256(data).hexdigest() for name, data in sources.items()},
              'scope': 'Exact saved nominal cycles only, not randomized reliability or tensile-force validation.'}
    (args.output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({label: row['maxima'] for label, row in results.items()}, indent=2))


if __name__ == '__main__':
    main()
