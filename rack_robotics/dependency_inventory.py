"""Read-only dependency closure for preserved environments and their code.

USD dependency enumeration is injected so file-integrity behavior can be tested
without a renderer. Shader imports/native runtime libraries are not USD assets;
the complete pinned Isaac installation remains an explicit prerequisite.
"""
import hashlib
import json
from pathlib import Path


def confined(root, value):
    path = (root/value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Path escapes declared root: '+str(value))
    return path


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


class Files:
    def __init__(self, project, runtime):
        self.roots = {'project':project.resolve(), 'isaac_runtime':runtime.resolve()}
        self.rows = {}
        self.signatures = {}

    @staticmethod
    def signature(path):
        s = path.stat()
        return s.st_size, s.st_mtime_ns, s.st_ino

    def add(self, value, role, expected=None):
        path = Path(value).resolve()
        matches = [(name,root) for name,root in self.roots.items() if path.is_relative_to(root)]
        if len(matches) != 1: raise ValueError('Dependency outside unique declared root: '+str(path))
        if not path.is_file(): raise ValueError('Missing dependency file: '+str(path))
        namespace,root = matches[0]; relative = str(path.relative_to(root))
        key = namespace+':'+relative
        before = self.signature(path)
        if key not in self.rows:
            value_hash = digest(path)
            if before != self.signature(path): raise ValueError('File changed during hash: '+str(path))
            self.rows[key] = {'namespace':namespace,'relative_path':relative,
                              'sha256':value_hash,'bytes':before[0],'roles':[]}
            self.signatures[key] = before
        if self.signatures[key] != before: raise ValueError('File changed during inventory: '+str(path))
        row = self.rows[key]
        if expected is not None and row['sha256'] != expected:
            raise ValueError('Declared hash mismatch: '+str(path))
        if role not in row['roles']: row['roles'].append(role)
        return key

    def finish(self):
        for key,row in self.rows.items():
            path = self.roots[row['namespace']]/row['relative_path']
            if self.signature(path) != self.signatures[key]: raise ValueError('Dependency changed before completion: '+str(path))
            row['roles'].sort()
        return dict(sorted(self.rows.items()))


def inventory(project, runtime, audit_path, enumerate_usd, progress=None):
    project = project.resolve(); runtime = runtime.resolve()
    audit_path = confined(project, audit_path)
    audit = json.loads(audit_path.read_text())
    declared = audit['environments']
    if len(declared) != audit['versions'] or len({r['environment'] for r in declared}) != len(declared):
        raise ValueError('Missing or duplicate preservation entries')
    disk = {str(p.parent.relative_to(project)) for p in
            (project/'rack_robotics/environments').glob('*/v*/manifest.json')}
    if {r['environment'] for r in declared} != disk:
        raise ValueError('Preservation audit does not cover every saved version')
    files = Files(project, runtime)
    audit_key = files.add(audit_path,'preservation_audit')
    environments = []; baselines = {}
    for row in declared:
        name = row['environment']; env = confined(project,name)
        manifest_path = env/'manifest.json'
        manifest_key = files.add(manifest_path,'environment_manifest',row['manifest_sha256'])
        manifest = json.loads(manifest_path.read_text())
        package = [files.add(confined(env,p),'packaged_environment',value_hash)
                   for p,value_hash in manifest['packaged_file_sha256'].items()]
        config = json.loads((env/'config.json').read_text())
        baseline = confined(project,env/config['baseline'])
        baseline_key = files.add(baseline/'manifest.json','baseline_manifest',manifest['baseline_manifest_sha256'])
        if baseline_key not in baselines:
            base = json.loads((baseline/'manifest.json').read_text())
            base_files = [files.add(confined(baseline,p),'baseline_file',h) for p,h in base['files'].items()]
            shared = [files.add(confined(project,p),'baseline_shared_dependency',h)
                      for p,h in base['shared_dependencies'].items()]
            baselines[baseline_key] = {'files':sorted(base_files),'shared_dependencies':sorted(shared),
                                      'vendor_recovery':base.get('vendor_recovery')}
        scene = confined(env,config['scene'])
        layers,assets,unresolved = enumerate_usd(scene)
        if unresolved: raise ValueError('Unresolved USD dependencies for '+name+': '+repr(unresolved))
        layer_keys = sorted({files.add(p,'usd_layer') for p in layers})
        asset_keys = sorted({files.add(p,'usd_asset') for p in assets})
        if files.add(scene,'usd_layer') not in layer_keys: raise ValueError('USD closure omitted root scene')
        environments.append({'environment':name,'manifest':manifest_key,
            'baseline_manifest':baseline_key,'package_files':sorted(package),
            'usd_layers':layer_keys,'usd_assets':asset_keys,'unresolved':[],
            'scope':'File closure only; task outcome remains in preservation/physics evidence'})
        if progress: progress(name,len(layer_keys),len(asset_keys))
    records = files.finish()
    return {'schema':'preserved_dependency_closure_v1','passed':True,
        'preservation_audit':audit_key,'preserved_versions':len(environments),
        'roots':{name:str(path) for name,path in files.roots.items()},
        'files':records,'unique_files':len(records),'unique_file_bytes':sum(r['bytes'] for r in records.values()),
        'environments':environments,'baselines':baselines,
        'limitations':[
            'USD-authored layer/asset dependencies and declared package/baseline files only; not a runnable archive.',
            'Keep the project mounted at /workspace and the complete pinned Isaac runtime at /isaac-sim; absolute USD paths are not rewritten.',
            'Shader imports, native plugins, Python dependencies and driver/GPU compatibility require the complete runtime, not just the listed MDL file.',
            'File/dependency integrity does not prove a physical cycle, reliability, portability to arbitrary paths, or redistribution permission.',
            'Original-trial source mismatches and historical outcome exceptions remain in the separate preservation audit.']}
