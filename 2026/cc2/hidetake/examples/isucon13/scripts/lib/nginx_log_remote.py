#!/usr/bin/env python3
"""ISUCON13 JSON/error log boundaries; preserve metadata and reopen only."""

import datetime
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time


def old_files_open(identities):
    for process in Path('/proc').glob('[0-9]*'):
        try:
            if process.joinpath('comm').read_text().strip() != 'nginx':
                continue
            for fd in process.joinpath('fd').iterdir():
                try:
                    info = fd.stat()
                    if (info.st_dev, info.st_ino) in identities:
                        return True
                except FileNotFoundError:
                    pass
        except (FileNotFoundError, ProcessLookupError):
            pass
    return False


def rotate(log_dir, run_id, phase):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', run_id):
        raise ValueError('Invalid run ID')
    if phase not in ('before', 'measurement'):
        raise ValueError('Invalid phase')
    names = ('isucon-access.json', 'error.log')
    info = {name: (log_dir / name).lstat() for name in names}
    if any(not stat.S_ISREG(value.st_mode) for value in info.values()):
        raise ValueError('Expected regular nginx log files, not symlinks')
    root = log_dir / 'measurements'
    root.mkdir(mode=0o700, exist_ok=True)
    if root.is_symlink():
        raise ValueError('Measurement directory must not be a symlink')
    run = root / run_id
    if phase == 'before':
        run.mkdir(mode=0o700)
    elif not run.is_dir() or run.is_symlink():
        raise ValueError('Missing measurement directory')
    destination = run / phase
    destination.mkdir(mode=0o700)
    for name in names:
        source = log_dir / name
        # Destination is new, so no archived log can be overwritten.
        source.rename(destination / name)
        descriptor = os.open(source, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.fchown(descriptor, info[name].st_uid, info[name].st_gid)
            os.fchmod(descriptor, stat.S_IMODE(info[name].st_mode))
        finally:
            os.close(descriptor)
    subprocess.run(['/usr/sbin/nginx', '-s', 'reopen'], check=True, capture_output=True)
    identities = {(value.st_dev, value.st_ino) for value in info.values()}
    for _ in range(100):
        if not old_files_open(identities):
            return {
                'phase': phase,
                'reopened_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'files': {name: str(destination / name) for name in names},
            }
        time.sleep(0.1)
    raise RuntimeError('nginx still holds an archived log; check remote state before retrying')


if __name__ == '__main__':
    print(json.dumps(rotate(Path('/var/log/nginx'), sys.argv[1], sys.argv[2])))
