"""ISUCON13 slow-log preparation/restoration controller; no benchmark."""
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys


def main():
    mode, ident, preparation=sys.argv[1:]
    if mode not in {'prepare','restore'} or not all(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',v) for v in [ident,preparation]):
        raise ValueError('invalid arguments')
    if mode=='prepare' and ident!=preparation:
        raise ValueError('prepare operation ID must equal preparation ID')
    root=Path(__file__).resolve().parents[2]
    folder=root.parent/'artifacts'/ident;folder.mkdir(mode=0o700)
    action='start' if mode=='prepare' else 'restore'
    code=(root/'scripts/lib/slowlog_remote.py').read_text()
    cmd='sudo -n python3 -c '+shlex.quote(code)+' '+preparation+' '+action+' manual'
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10','isucon-target',cmd],capture_output=True)
    (folder/'operation.stdout').write_bytes(result.stdout);(folder/'operation.stderr').write_bytes(result.stderr)
    (folder/'metadata.json').write_text(json.dumps(dict(mode=mode,preparation_id=preparation,exit_code=result.returncode),indent=2))
    for name in ['settings.json','restored.json']:
        fetched=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10','isucon-target',f'sudo -n cat /var/lib/isucon-mysql-log-backups/{preparation}/{name}'],capture_output=True)
        if fetched.returncode==0:(folder/name).write_bytes(fetched.stdout)
    print(f'{mode}: exit_code={result.returncode} artifacts={folder}')
    sys.exit(result.returncode)


if __name__=='__main__':main()
