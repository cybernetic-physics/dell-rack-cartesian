import json
from pathlib import Path
from zipfile import ZipFile

root = Path('/workspace/assets/vendor')
with ZipFile(root / 'datacenter.zip') as z:
    names = z.namelist()
    models = [n for n in names if n.lower().endswith(('.usd', '.usda', '.usdc'))]
    print('\n'.join(models[:150]), flush=True)
    (root / 'datacenter-index.json').write_text(json.dumps(names, indent=2))
    z.extractall(root / 'datacenter')
print('EXTRACTED', flush=True)
