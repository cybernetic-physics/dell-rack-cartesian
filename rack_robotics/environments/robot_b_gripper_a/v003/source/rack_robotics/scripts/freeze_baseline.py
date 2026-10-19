"""Create a write-protected, hash-verified baseline without modifying the demo.

Run on the VM with system Python, before robotics development. Existing snapshots
are verified, never replaced. Large vendor dependencies remain shared and hashed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--name', default='baseline-001')
    args = parser.parse_args()
    root = args.root.resolve()
    dest = root / 'rack_robotics/assets/shared_rack' / args.name
    manifest_path = dest / 'manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        for name, expected in manifest['files'].items():
            if digest(dest / name) != expected:
                raise RuntimeError(f'Baseline modified: {name}')
        for name, expected in manifest['shared_dependencies'].items():
            if digest(root / name) != expected:
                raise RuntimeError(f'Shared dependency modified: {name}')
        print(f'BASELINE_VERIFIED {dest}', flush=True)
        return
    if dest.exists():
        raise RuntimeError(f'Incomplete snapshot exists; inspect it, do not overwrite: {dest}')
    include = ['rack_sim', 'demo.py', 'assets/latch-row', 'assets/connectors',
               'assets/labels', 'scripts/latch_probe.py', 'scripts/fetch_assets.sh',
               'scripts/catalog_datacenter.py', 'tests', 'README.md', 'RESEARCH.md',
               'PROGRESS.md', 'PLAN_p2.md']
    files = {}
    for name in include:
        source = root / name
        candidates = sorted(source.rglob('*')) if source.is_dir() else [source]
        for path in candidates:
            if not path.is_file() or '__pycache__' in path.parts:
                continue
            rel = path.relative_to(root)
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            files[str(rel)] = digest(target)
            target.chmod(0o444)
    shared = {}
    pack = root / 'assets/vendor/datacenter'
    if not pack.is_dir():
        raise RuntimeError('Run this on the VM where the original datacenter pack exists')
    for path in sorted(pack.rglob('*')):
        if path.is_file():
            shared[str(path.relative_to(root))] = digest(path)
    manifest = {
        'format_version': 1, 'baseline': args.name,
        'files': files, 'shared_dependencies': shared,
        'vendor_recovery': {
            'url': 'https://d4i3qtqj3r0z5.cloudfront.net/Datacenter_NVD%4010012.zip',
            'archive_sha256': '4972d1a9726b36279d7c26531b4d0a084156b7d512f5340b6e1063a9cf458fd4',
            'instructions': 'scripts/fetch_assets.sh and scripts/catalog_datacenter.py',
        },
        'notes': ['Files are read-only and verified by SHA-256, not WORM storage.',
                  'Absolute USD dependencies remain shared on the existing VM.',
                  'Robotics trials must not command baseline HandDrive or ClipPress.'],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    manifest_path.chmod(0o444)
    print(f'BASELINE_FROZEN {dest}: {len(files)} files, {len(shared)} shared dependencies', flush=True)


if __name__ == '__main__':
    main()
