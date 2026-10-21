#!/usr/bin/env python3
"""Local entry point for explicitly approved deploy/rollback operations."""

import argparse
import datetime
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['deploy', 'rollback'])
    parser.add_argument('--revision')
    parser.add_argument('--backup-id')
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    for value in [args.run_id] + ([args.backup_id] if args.backup_id else []):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', value):
            parser.error('Invalid run/backup ID')
    if args.operation == 'deploy' and not args.revision:
        parser.error('deploy requires --revision')
    if args.operation == 'rollback' and not args.backup_id:
        parser.error('rollback requires --backup-id')
    repo = Path(__file__).resolve().parents[1]
    if not (repo / '.git').exists():
        parser.error('Copy this example into a private target repository before execution')
    settings = json.loads((repo / 'ansible/settings.json').read_text())
    required = ['ssh_alias', 'login_user', 'app_user', 'app_group', 'webapp',
                'backup_root', 'app_service', 'health_url']
    if any(not isinstance(settings.get(key), str) or not settings[key].strip() for key in required):
        parser.error('Fill in ansible/settings.json before execution')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', settings['ssh_alias']):
        parser.error('Use an approved SSH alias')
    if any(not settings[key].startswith('/') or settings[key] == '/' for key in ['webapp', 'backup_root']):
        parser.error('Set absolute application and backup directory paths')
    revision = None
    archive = None
    if args.operation == 'deploy':
        revision = subprocess.check_output(
            ['git', '-C', str(repo), 'rev-parse', '--verify', '--end-of-options', args.revision + '^{commit}'],
            text=True,
        ).strip()
        archive = subprocess.check_output(
            ['git', '-C', str(repo), 'archive', revision, 'webapp/ruby', 'webapp/public']
        )
    output = repo.parent / 'artifacts' / args.run_id
    output.parent.mkdir(exist_ok=True)
    try:
        output.mkdir()
    except FileExistsError:
        parser.error('Run ID already exists')
    metadata = dict(operation=args.operation, revision=revision, restore_id=args.backup_id,
                    run_id=args.run_id, host=settings['ssh_alias'], status='started',
                    started_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    backup_path=settings['backup_root'].rstrip('/') + '/' + args.run_id)
    path = output / 'metadata.json'
    path.write_text(json.dumps(metadata, indent=2) + '\n')
    try:
        with tempfile.TemporaryDirectory(prefix='isucon-deploy-') as temp:
            temp = Path(temp)
            payload = temp / 'payload.tar'
            if archive is not None:
                with tarfile.open(fileobj=io.BytesIO(archive)) as source, tarfile.open(payload, 'w') as target:
                    for member in source:
                        parts = Path(member.name).parts
                        if len(parts) < 2:
                            continue
                        if parts[0] != 'webapp' or parts[1] not in ('ruby', 'public') or '..' in parts:
                            raise ValueError('Unexpected archive path')
                        if not member.isfile() and not member.isdir():
                            raise ValueError('Symlinks and special files are outside this deployment scope')
                        member.name = '/'.join(parts[1:])
                        target.addfile(member, source.extractfile(member) if member.isfile() else None)
            variables = dict(run_id=args.run_id, revision=revision, restore_id=args.backup_id,
                             archive_path=str(payload))
            variables.update(settings)
            varfile = temp / 'vars.json'
            varfile.write_text(json.dumps(variables))
            command = ['ansible-playbook', '-i', str(repo / 'ansible/inventory.yml'),
                       str(repo / 'ansible' / (args.operation + '.yml')), '-e', '@' + str(varfile)]
            with (output / 'ansible.log').open('w') as log:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
            metadata['exit_code'] = result.returncode
            metadata['status'] = 'passed' if result.returncode == 0 else 'failed'
    except Exception as error:
        metadata.update(status='error', error=str(error), exit_code=1)
    finally:
        metadata['finished_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        path.write_text(json.dumps(metadata, indent=2) + '\n')
    print(metadata['status'] + ': ' + str(output))
    if metadata['status'] != 'passed':
        print('Inspect ansible.log and remote state before retrying; rollback is explicit.')
    return 0 if metadata['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
