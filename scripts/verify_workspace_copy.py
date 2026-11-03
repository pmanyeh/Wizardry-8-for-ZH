"""Verify a complete relocation copy before removing the original directory."""

import concurrent.futures
import hashlib
import json
import pathlib

PROJECT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = pathlib.Path(r'C:\dev\wiz8-ws')
DESTINATION = PROJECT / 'local/wiz8-ws'
REPORT = PROJECT / 'artifacts/workspace-relocation/verification.json'


def inventory(root):
    return {path.relative_to(root).as_posix(): path.stat().st_size
            for path in root.rglob('*') if path.is_file()}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify(relative):
    source_hash = digest(SOURCE / relative)
    destination_hash = digest(DESTINATION / relative)
    return relative, source_hash, destination_hash


if SOURCE.is_symlink() or SOURCE.is_junction():
    raise SystemExit('Source must still be the original physical directory')
if DESTINATION.resolve() != DESTINATION or not DESTINATION.is_relative_to(PROJECT):
    raise SystemExit('Unexpected destination')

source_files = inventory(SOURCE)
destination_files = inventory(DESTINATION)
if source_files != destination_files:
    missing = sorted(source_files.keys() - destination_files.keys())
    extra = sorted(destination_files.keys() - source_files.keys())
    size_mismatches = sorted(name for name in source_files.keys() & destination_files.keys()
                             if source_files[name] != destination_files[name])
    result = {'status': 'FAIL', 'missing': missing, 'extra': extra, 'size_mismatches': size_mismatches}
else:
    print(f'Verifying SHA-256 for {len(source_files)} files in both directories', flush=True)
    mismatches = []
    hashes = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for index, (relative, source_hash, destination_hash) in enumerate(pool.map(verify, source_files), 1):
            if source_hash != destination_hash:
                mismatches.append(relative)
            hashes[relative] = source_hash
            if index % 4000 == 0:
                print(f'Checked {index}/{len(source_files)}', flush=True)
    result = {
        'status': 'PASS' if not mismatches else 'FAIL',
        'source': str(SOURCE), 'destination': str(DESTINATION),
        'files': len(source_files), 'bytes': sum(source_files.values()),
        'mismatches': mismatches, 'sha256': hashes,
    }

REPORT.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({key: value for key, value in result.items() if key != 'sha256'}, indent=2), flush=True)
raise SystemExit(result['status'] != 'PASS')
