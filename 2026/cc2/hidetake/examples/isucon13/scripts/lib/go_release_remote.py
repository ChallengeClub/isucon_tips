"""Binary deploy/rollback with an explicit live source baseline and candidate provenance."""
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time

APP = Path('/home/isucon/webapp/go')
BINARY = APP / 'isupipe'
UNIT = Path('/etc/systemd/system/isupipe-go.service')
ENV = Path('/home/isucon/env.sh')
BACKUPS = Path('/var/lib/isucon-deploy-backups')
LOCK = '/run/lock/isucon-go-release.lock'
SERVICE = 'isupipe-go'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def command(*args):
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError('command failed: ' + args[0])
    return result.stdout


def info(path):
    s = path.lstat()
    if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1:
        raise RuntimeError('regular single-link file required')
    return dict(uid=s.st_uid, gid=s.st_gid, mode=stat.S_IMODE(s.st_mode),
                mtime_ns=s.st_mtime_ns, size=s.st_size)


def source_manifest():
    paths = list(APP.glob('*.go')) + [APP / 'go.mod', APP / 'go.sum']
    return {p.name: digest(p.read_bytes()) for p in paths}


def save(folder, state, phase):
    state['phase'] = phase
    temp = folder / 'state.tmp'
    temp.write_text(json.dumps(state, indent=2))
    os.replace(temp, folder / 'state.json')


def install(data, meta):
    fd, name = tempfile.mkstemp(prefix='.release-', dir=APP)
    try:
        os.fchown(fd, meta['uid'], meta['gid'])
        os.fchmod(fd, meta['mode'])
        with os.fdopen(fd, 'wb') as stream:
            fd = None
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.utime(name, ns=(meta['mtime_ns'], meta['mtime_ns']))
        os.replace(name, BINARY)
        directory = os.open(APP, os.O_DIRECTORY | os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if fd is not None:
            os.close(fd)
        if os.path.exists(name):
            os.unlink(name)


def health(expected_hash):
    command('systemctl', 'is-active', SERVICE)
    pid = int(command('systemctl', 'show', SERVICE, '-p', 'MainPID', '--value'))
    if pid <= 0 or digest(Path(f'/proc/{pid}/exe').read_bytes()) != expected_hash:
        raise RuntimeError('running binary mismatch')
    for attempt in range(10):
        try:
            # GET only; API check reaches Go and DB through nginx.
            command('curl', '--insecure', '--fail', '--silent', '--show-error',
                    '--max-time', '3', '--output', '/dev/null', '--resolve',
                    'pipe.u.isucon.local:443:127.0.0.1',
                    'https://pipe.u.isucon.local/api/tag')
            return
        except RuntimeError:
            if attempt == 9:
                raise
            time.sleep(0.5)


def unchanged(state):
    if source_manifest() != state['source_manifest']:
        raise RuntimeError('source changed')
    if digest(UNIT.read_bytes()) != state['unit_sha256'] or info(ENV) != state['env_metadata']:
        raise RuntimeError('configuration changed; review before recovery')


def execute(action, ident, payload=None):
    if action not in {'deploy', 'rollback'} or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', ident):
        raise ValueError('invalid arguments')
    folder = BACKUPS / ident
    if action == 'deploy':
        candidate = base64.b64decode(payload['binary'], validate=True)
        if not candidate.startswith(b'\x7fELF') or digest(candidate) != payload['binary_sha256']:
            raise ValueError('invalid candidate binary')
        if not re.fullmatch(r'[0-9a-f]{40}', payload['source_commit']):
            raise ValueError('full source commit required')
        expected_sources = payload.get('expected_source_manifest', payload['source_manifest'])
        if source_manifest() != expected_sources:
            raise RuntimeError('live source baseline changed')
        if command('systemctl', 'is-active', SERVICE).strip() != b'active':
            raise RuntimeError('service must initially be active')
        original = BINARY.read_bytes()
        if digest(original) != payload['expected_original_sha256']:
            raise RuntimeError('original binary changed')
        health(digest(original))
        state = dict(source_commit=payload['source_commit'], source_manifest=expected_sources,
                     candidate_source_manifest=payload['source_manifest'],
                     original_sha256=digest(original), candidate_sha256=digest(candidate),
                     original_metadata=info(BINARY), unit_sha256=digest(UNIT.read_bytes()),
                     env_metadata=info(ENV), original_deployment_sha='unknown')
        BACKUPS.mkdir(mode=0o700, exist_ok=True)
        folder.mkdir(mode=0o700)
        (folder / 'original.isupipe').write_bytes(original)
        (folder / 'candidate.isupipe').write_bytes(candidate)
        shutil.copy2(UNIT, folder / 'isupipe-go.service')
        save(folder, state, 'prepared')
        save(folder, state, 'stopping')
        command('systemctl', 'stop', SERVICE)
        unchanged(state)
        if digest(BINARY.read_bytes()) != state['original_sha256']:
            raise RuntimeError('binary changed during preparation')
        save(folder, state, 'installing')
        install(candidate, state['original_metadata'])
        save(folder, state, 'starting')
        command('systemctl', 'start', SERVICE)
        health(state['candidate_sha256'])
        save(folder, state, 'deployed')
    else:
        if folder.is_symlink():
            raise RuntimeError('backup symlink refused')
        state = json.loads((folder / 'state.json').read_text())
        if state['phase'] == 'rolled-back':
            raise RuntimeError('already rolled back')
        original = (folder / 'original.isupipe').read_bytes()
        if digest(original) != state['original_sha256']:
            raise RuntimeError('backup digest mismatch')
        unchanged(state)
        if digest(BINARY.read_bytes()) not in [state['candidate_sha256'], state['original_sha256']]:
            raise RuntimeError('unrecognized installed binary')
        save(folder, state, 'rollback-stopping')
        command('systemctl', 'stop', SERVICE)
        unchanged(state)
        save(folder, state, 'restoring')
        install(original, state['original_metadata'])
        save(folder, state, 'rollback-starting')
        command('systemctl', 'start', SERVICE)
        health(state['original_sha256'])
        save(folder, state, 'rolled-back')
    print(json.dumps({k: state[k] for k in ['phase', 'source_commit', 'original_sha256', 'candidate_sha256']}))


if __name__ == '__main__':
    try:
        if os.geteuid() != 0:
            raise RuntimeError('root required')
        with open(LOCK, 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            action, ident = sys.argv[1:]
            execute(action, ident, json.load(sys.stdin) if action == 'deploy' else None)
    except Exception as exc:
        print('Release stopped (' + type(exc).__name__ + '); inspect saved phase. No automatic rollback.', file=sys.stderr)
        sys.exit(1)
