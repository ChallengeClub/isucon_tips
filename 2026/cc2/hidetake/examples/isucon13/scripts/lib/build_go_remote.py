"""Local controller for the approved remote build entry."""
import base64
import hashlib
import io
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tarfile


def payload(target, revision, ident, original):
    if not re.fullmatch(r'[0-9a-f]{40}', revision) or not re.fullmatch(r'[0-9a-f]{64}', original):
        raise ValueError('full source commit and original SHA-256 required')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', ident):
        raise ValueError('invalid build ID')
    archive = subprocess.check_output(['git', '-C', str(target), 'archive', revision, 'webapp/go'])
    files = {}
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for member in tar.getmembers():
            path = Path(member.name)
            if path.suffix == '.go' and path.parent != Path('webapp/go'):
                raise ValueError('Go subdirectories require a separate build plan')
            if path.parent == Path('webapp/go') and (path.suffix == '.go' or path.name in {'go.mod', 'go.sum'}):
                if not member.isfile():
                    raise ValueError('source symlinks refused')
                files[path.name] = tar.extractfile(member).read()
    return dict(id=ident, source_commit=revision, expected_original_sha256=original,
                source_manifest={p: hashlib.sha256(b).hexdigest() for p, b in files.items()},
                files={p: base64.b64encode(b).decode() for p, b in files.items()})


def main():
    revision, ident, original = sys.argv[1:4]
    target = Path(__file__).resolve().parents[2]
    request = payload(target, revision, ident, original)
    if len(sys.argv) == 5:
        request['expected_source_manifest'] = payload(target, sys.argv[4], ident, original)['source_manifest']
    folder = target.parent / 'artifacts' / ident
    folder.mkdir(mode=0o700)
    # Stop if another benchmark is running; build does not start a benchmark.
    check = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                            'isucon-benchmark', 'if pgrep -x bench >/dev/null; then exit 1; fi'], capture_output=True)
    if check.returncode:
        raise RuntimeError('benchmark host unavailable or busy')
    code = (target / 'scripts/lib/build_go_remote_worker.py').read_text()
    # cd before sudo: ubuntu's login cwd may not be accessible to isucon.
    remote = 'cd /home/isucon && sudo -n -u isucon -H python3 -c ' + shlex.quote(code)
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                             'isucon-target', remote], input=json.dumps(request).encode(), capture_output=True)
    (folder / 'remote-build.stdout').write_bytes(result.stdout)
    (folder / 'remote-build.stderr').write_bytes(result.stderr)
    (folder / 'remote-build-exit-code.txt').write_text(str(result.returncode) + '\n')
    # Request explicit build files only; never env.sh or credentials.
    for name in ['state.json', 'build.log', 'build-info.txt', 'build.json', 'isupipe']:
        fetched = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                                  'isucon-target', f'sudo -n -u isucon cat /home/isucon/builds/{ident}/{name}'], capture_output=True)
        (folder / (name if fetched.returncode == 0 else name + '.fetch.stderr')).write_bytes(
            fetched.stdout if fetched.returncode == 0 else fetched.stderr)
    if result.returncode:
        print('Remote build failed; artifacts saved, no retry or deploy.', file=sys.stderr)
        sys.exit(result.returncode)
    metadata = json.loads((folder / 'build.json').read_text())
    if metadata['source_commit'] != revision or metadata['source_manifest'] != request['source_manifest']:
        raise RuntimeError('returned build provenance mismatch')
    if metadata.get('expected_source_manifest') != request.get('expected_source_manifest', request['source_manifest']):
        raise RuntimeError('returned live source baseline mismatch')
    if metadata['expected_original_sha256'] != original or metadata.get('build_location') != 'remote':
        raise RuntimeError('returned build conditions mismatch')
    if hashlib.sha256((folder / 'isupipe').read_bytes()).hexdigest() != metadata['binary_sha256']:
        raise RuntimeError('returned artifact digest mismatch')
    print(json.dumps({k: metadata[k] for k in ['source_commit', 'binary_sha256', 'elapsed_seconds', 'build_location']}))


if __name__ == '__main__':
    main()
