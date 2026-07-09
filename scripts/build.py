"""Stage an explicit source-only Cloud Run functions build context."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    destination = ROOT / 'artifacts'
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir()
    (ROOT / 'build').mkdir(exist_ok=True)
    names = ['main.py', 'requirements.txt', 'LICENSE', *[str(p.relative_to(ROOT)) for p in sorted((ROOT / 'app').glob('*.py'))]]
    hashes = {}
    for name in names:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
        hashes[name] = hashlib.sha256(target.read_bytes()).hexdigest()
    (ROOT / 'build/source-manifest.json').write_text(json.dumps(hashes, indent=2) + '\n')
    print(f'Staged {len(names)} source files; Cloud Build installs the hashed runtime dependencies.')


if __name__ == '__main__':
    main()
