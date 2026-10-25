"""Build a fixed committed source tree locally; does not access target hosts."""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile


def main():
    revision, ident, original_hash = sys.argv[1:]
    if not re.fullmatch(r'[0-9a-f]{40}', revision) or not re.fullmatch(r'[0-9a-f]{64}', original_hash):
        raise ValueError('full source commit and original SHA-256 required')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', ident):
        raise ValueError('invalid build ID')
    target = Path(__file__).resolve().parents[2]
    folder = target.parent / 'artifacts' / ident
    folder.mkdir(mode=0o700)
    source = folder / 'source'
    source.mkdir()
    archive = subprocess.check_output(['git', '-C', str(target), 'archive', revision, 'webapp/go'])
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        # Commit contents only, no links or traversal.
        for item in tar.getmembers():
            relative = Path(item.name)
            if relative.is_absolute() or '..' in relative.parts or not (item.isfile() or item.isdir()):
                raise ValueError('unexpected source archive member')
            dest = source / relative
            if item.isdir():
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(tar.extractfile(item).read())
    app = source / 'webapp/go'
    inputs = list(app.glob('*.go')) + [app / 'go.mod', app / 'go.sum']
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    env = os.environ.copy()
    env.update(GOTOOLCHAIN='go1.21.2', GOENV='off', GOPATH='/tmp/isucon-gopath',
               GOMODCACHE='/tmp/isucon-gomod', GOCACHE='/tmp/isucon-gocache',
               CGO_ENABLED='1', GOOS='linux', GOARCH='amd64', GOAMD64='v1',
               GOFLAGS='', CGO_CFLAGS='', CGO_CPPFLAGS='', CGO_CXXFLAGS='', CGO_LDFLAGS='')
    args = ['go', 'build', '-buildvcs=false', '-mod=readonly', '-ldflags', '-s -w', '-o', str(folder / 'isupipe'), '.']
    with (folder / 'build.log').open('wb') as log:
        subprocess.run(args, cwd=app, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    # Dependency manifest must not change during build.
    assert all(hashlib.sha256((app / p).read_bytes()).hexdigest() == h for p, h in manifest.items())
    metadata = dict(source_commit=revision, source_manifest=manifest,
                    binary_sha256=hashlib.sha256((folder / 'isupipe').read_bytes()).hexdigest(),
                    expected_original_sha256=original_hash, toolchain='go1.21.2',
                    build_command=args, cgo_enabled=1, buildvcs=False)
    (folder / 'build.json').write_text(json.dumps(metadata, indent=2) + '\n')
    (folder / 'build-info.txt').write_bytes(subprocess.check_output(['go', 'version', '-m', str(folder / 'isupipe')], env=env))
    print(json.dumps({k: metadata[k] for k in ['source_commit', 'binary_sha256', 'toolchain']}))


if __name__ == '__main__':
    main()
