"""Explicit measurement configuration entry. Does not run a benchmark."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def main():
    mode, ident, preparation = sys.argv[1:]
    if mode not in {'enable','restore','tools'} or not all(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', x) for x in [ident,preparation]):
        raise ValueError('invalid arguments')
    root=Path(__file__).resolve().parents[2]
    output=root.parent/'artifacts'/ident
    output.mkdir(mode=0o700)
    variables={}
    if mode!='tools':
        candidate=root/'infra/measurement/nginx.conf'
        fragment=root/'infra/measurement/nginx-log-format.conf'
        variables=dict(logging_mode=mode,preparation_id=preparation,
                       baseline_sha256=json.loads((root/'ansible/logging-settings.json').read_text())['baseline_sha256'],
                       candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
                       format_sha256=hashlib.sha256(fragment.read_bytes()).hexdigest(),
                       candidate_path=str(candidate),format_path=str(fragment))
    env=dict(os.environ,ANSIBLE_LOCAL_TEMP='/tmp/isucon-ansible-local',
             ANSIBLE_SSH_CONTROL_PATH_DIR='/tmp/isucon-ansible-cp')
    with tempfile.TemporaryDirectory(prefix='isucon-measurement-') as temp:
        varfile=Path(temp)/'vars.json';varfile.write_text(json.dumps(variables))
        play='measurement-tools.yml' if mode=='tools' else 'nginx-logging.yml'
        args=['ansible-playbook','-i',str(root/'ansible/measurement-inventory.yml'),str(root/'ansible'/play),'-e','@'+str(varfile)]
        with (output/'ansible.log').open('wb') as log:
            result=subprocess.run(args,env=env,stdout=log,stderr=subprocess.STDOUT)
    (output/'metadata.json').write_text(json.dumps(dict(mode=mode,preparation_id=preparation,exit_code=result.returncode),indent=2))
    print(f'{mode}: exit_code={result.returncode} artifacts={output}')
    sys.exit(result.returncode)


if __name__=='__main__':main()
