#!/usr/bin/env python3
"""Download the small offline recognizer model; never execute downloaded files."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import urllib.request
import zipfile

NAME = 'vosk-model-small-en-us-0.15'
URL = f'https://alphacephei.com/vosk/models/{NAME}.zip'


def install(destination):
    destination = destination.resolve()
    target = destination/NAME
    if target.is_dir():
        print(f'Already installed: {target}')
        return
    destination.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination) as temp:
        archive = Path(temp)/'model.zip'
        print(f'Downloading {URL}')
        with urllib.request.urlopen(URL,timeout=60) as response, archive.open('wb') as out:
            digest = hashlib.sha256()
            total = 0
            while chunk := response.read(1024*1024):
                total += len(chunk)
                if total > 100*1024*1024:
                    raise ValueError('unexpectedly large model archive')
                out.write(chunk);digest.update(chunk)
        with zipfile.ZipFile(archive) as z:
            if sum(i.file_size for i in z.infolist()) > 200*1024*1024:
                raise ValueError('unexpectedly large unpacked model')
            for member in z.infolist():
                path = (Path(temp)/member.filename).resolve()
                if not path.is_relative_to(Path(temp).resolve()) or not member.filename.startswith(NAME+'/'):
                    raise ValueError('unsafe model archive path')
            z.extractall(temp)
        unpacked = Path(temp)/NAME
        if not (unpacked/'am/final.mdl').is_file():
            raise ValueError('model archive is incomplete')
        unpacked.rename(target)
        record = {'url':URL,'sha256':digest.hexdigest(),'license':'Apache-2.0'}
        (destination/f'{NAME}.download.json').write_text(json.dumps(record,indent=2)+'\n')
        print(f'Installed {target}; SHA-256 {digest.hexdigest()}')
        print('SHA is a download record, not verification against a separately trusted publisher hash.')


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--destination',type=Path,default=Path(__file__).parents[1]/'python/models')
    args=parser.parse_args()
    install(args.destination)
