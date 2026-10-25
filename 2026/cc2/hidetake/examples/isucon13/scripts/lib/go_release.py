"""Local controller; access through deploy.sh / rollback.sh only."""
import base64
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys


def main():
    action, ident = sys.argv[1:]
    if action not in {'deploy', 'rollback'} or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', ident):
        raise ValueError('invalid arguments')
    target = Path(__file__).resolve().parents[2]
    folder = target.parent / 'artifacts' / ident
    payload = b''
    if action == 'deploy':
        metadata = json.loads((folder / 'build.json').read_text())
        binary = (folder / 'isupipe').read_bytes()
        if hashlib.sha256(binary).hexdigest() != metadata['binary_sha256']:
            raise ValueError('build artifact changed')
        metadata['binary'] = base64.b64encode(binary).decode()
        payload = json.dumps(metadata).encode()
    elif not folder.is_dir():
        raise ValueError('local recovery directory missing')
    code = (target / 'scripts/lib/go_release_remote.py').read_text()
    remote = 'sudo -n python3 -c ' + shlex.quote(code) + ' ' + action + ' ' + ident
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                             'isucon-target', remote], input=payload, capture_output=True)
    (folder / f'{action}.stdout').write_bytes(result.stdout)
    (folder / f'{action}.stderr').write_bytes(result.stderr)
    recovery = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                               'isucon-target', f'sudo -n cat /var/lib/isucon-deploy-backups/{ident}/state.json'], capture_output=True)
    (folder / f'{action}-state.json').write_bytes(recovery.stdout)
    (folder / f'{action}-state-fetch.stderr').write_bytes(recovery.stderr)
    print(f'action={action} exit_code={result.returncode} artifacts={folder}')
    if result.returncode == 0:
        print(result.stdout.decode().strip())
    sys.exit(result.returncode)


if __name__ == '__main__':
    main()
