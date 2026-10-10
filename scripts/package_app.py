#!/usr/bin/env python3
"""Package a reproducible App Lab import archive including the local voice model."""
import argparse
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT/'python/models/vosk-model-small-en-us-0.15/am/final.mdl'


def package(output, without_model=False):
    if not without_model and not MODEL.is_file():
        raise SystemExit('Run python3 scripts/download_voice_model.py first. Model is required for voice.')
    output = output.resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    paths = [ROOT/'app.yaml']
    for folder in ['python','sketch']:
        paths.extend(sorted((ROOT/folder).rglob('*')))
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for path in paths:
            rel=path.relative_to(ROOT)
            if not path.is_file() or '__pycache__' in rel.parts or path.suffix == '.pyc' or path.name == '.gitkeep':
                continue
            if without_model and 'models' in rel.parts:
                continue
            # App manifest at archive root, as expected by App Lab import.
            z.write(path,rel.as_posix())
    print(output)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'build/AICar.zip')
    parser.add_argument('--without-model',action='store_true',help='For structural testing only; voice cannot start.')
    a=parser.parse_args()
    package(a.output,a.without_model)
