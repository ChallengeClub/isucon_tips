"""Remote build worker, run as isucon via build-go-remote.sh after approval."""
import base64
import datetime
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import subprocess
import sys
import time

ROOT = Path('/home/isucon/builds')
APP = Path('/home/isucon/webapp/go')
GO = '/home/isucon/local/golang/bin/go'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def command(args, **kwargs):
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
    if result.returncode:
        raise RuntimeError('build preflight command failed')
    return result.stdout


def running_state():
    pid = int(command(['systemctl', 'show', 'isupipe-go', '-p', 'MainPID', '--value']))
    if pid <= 0:
        raise RuntimeError('Go service is not running')
    return pid, digest((APP / 'isupipe').read_bytes())


def source_manifest():
    paths = list(APP.glob('*.go')) + [APP / 'go.mod', APP / 'go.sum']
    return {p.name: digest(p.read_bytes()) for p in paths}


def validate(request):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', request['id']):
        raise ValueError('invalid build ID')
    if not re.fullmatch(r'[0-9a-f]{40}', request['source_commit']):
        raise ValueError('full commit required')
    if not re.fullmatch(r'[0-9a-f]{64}', request['expected_original_sha256']):
        raise ValueError('original hash required')
    files = {}
    for name, encoded in request['files'].items():
        if not re.fullmatch(r'[A-Za-z0-9_]+\.go|go\.(?:mod|sum)', name):
            raise ValueError('only top-level Go sources and manifests supported')
        files[name] = base64.b64decode(encoded, validate=True)
    if not {'go.mod', 'go.sum', 'main.go'} <= files.keys():
        raise ValueError('required sources missing')
    if {p: digest(b) for p, b in files.items()} != request['source_manifest']:
        raise ValueError('source payload digest mismatch')
    return files


def build(request):
    files = validate(request)
    expected_sources = request.get('expected_source_manifest', request['source_manifest'])
    if source_manifest() != expected_sources:
        raise RuntimeError('live source differs; review deployment scope')
    initial = running_state()
    if initial[1] != request['expected_original_sha256']:
        raise RuntimeError('live binary changed')
    environment = dict(HOME='/home/isucon', USER='isucon', LOGNAME='isucon',
                       PATH='/home/isucon/local/golang/bin:/usr/local/bin:/usr/bin:/bin',
                       LANG='C.UTF-8', GOENV='off', GOTOOLCHAIN='local',
                       GOPATH='/home/isucon/go', GOMODCACHE='/home/isucon/go/pkg/mod',
                       GOCACHE='/home/isucon/.cache/go-build', GOPROXY='off',
                       CGO_ENABLED='1', GOOS='linux', GOARCH='amd64', GOAMD64='v1',
                       CGO_CFLAGS='', CGO_CPPFLAGS='', CGO_CXXFLAGS='', CGO_LDFLAGS='')
    if command([GO, 'version'], cwd=APP, env=environment).strip() != b'go version go1.21.2 linux/amd64':
        raise RuntimeError('unexpected toolchain')
    if ROOT.is_symlink():
        raise RuntimeError('build root symlink refused')
    ROOT.mkdir(mode=0o700, exist_ok=True)
    if ROOT.stat().st_uid != os.getuid():
        raise RuntimeError('build root owner mismatch')
    folder = ROOT / request['id']
    folder.mkdir(mode=0o700)
    source = folder / 'source'
    source.mkdir(mode=0o700)
    for name, data in files.items():
        (source / name).write_bytes(data)
    state = dict(id=request['id'], source_commit=request['source_commit'], phase='building',
                 builder_host_alias='isucon-target', initial_pid=initial[0],
                 start_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (folder / 'state.json').write_text(json.dumps(state, indent=2))
    args = [GO, 'build', '-buildvcs=false', '-mod=readonly', '-ldflags', '-s -w', '-o', str(folder / 'isupipe'), '.']
    start = time.monotonic()
    with (folder / 'build.log').open('wb') as log:
        result = subprocess.run(args, cwd=source, env=environment, stdout=log, stderr=subprocess.STDOUT)
    state.update(end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 elapsed_seconds=time.monotonic() - start, build_exit_code=result.returncode)
    state['phase'] = 'build-failed' if result.returncode else 'verifying'
    (folder / 'state.json').write_text(json.dumps(state, indent=2))
    if result.returncode:
        raise RuntimeError('build failed; no deployment performed')
    if any(digest((source / name).read_bytes()) != request['source_manifest'][name] for name in files):
        raise RuntimeError('input changed during build')
    if running_state() != initial or source_manifest() != expected_sources:
        raise RuntimeError('live state changed during build; do not deploy')
    binary = (folder / 'isupipe').read_bytes()
    if not binary.startswith(b'\x7fELF'):
        raise RuntimeError('build output is not ELF')
    metadata = dict(source_commit=request['source_commit'], source_manifest=request['source_manifest'],
                    expected_source_manifest=expected_sources,
                    binary_sha256=digest(binary), expected_original_sha256=initial[1],
                    toolchain='go1.21.2', build_command=args, cgo_enabled=1, buildvcs=False,
                    build_location='remote', builder_host_alias='isucon-target',
                    start_utc=state['start_utc'], end_utc=state['end_utc'],
                    elapsed_seconds=state['elapsed_seconds'], dependency_proxy='off')
    (folder / 'build-info.txt').write_bytes(command([GO, 'version', '-m', str(folder / 'isupipe')], cwd=source, env=environment))
    (folder / 'build.json').write_text(json.dumps(metadata, indent=2))
    state['phase'] = 'built'
    (folder / 'state.json').write_text(json.dumps(state, indent=2))
    print(json.dumps(dict(id=request['id'], phase='built', binary_sha256=metadata['binary_sha256'], elapsed_seconds=state['elapsed_seconds'])))


if __name__ == '__main__':
    try:
        os.umask(0o077)
        if pwd.getpwuid(os.getuid()).pw_name != 'isucon':
            raise RuntimeError('must run as isucon')
        build(json.load(sys.stdin))
    except Exception as exc:
        print('Remote build stopped (' + type(exc).__name__ + '); inspect artifacts without retrying.', file=sys.stderr)
        sys.exit(1)
