#!/usr/bin/env python3
"""Local entry point for explicitly approved nginx logging configuration."""

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', required=True, choices=['enable', 'restore'])
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--backup-id')
    args = parser.parse_args()
    from example_guard import require_target_checkout
    require_target_checkout(parser)
    for value in [args.run_id] + ([args.backup_id] if args.backup_id else []):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', value):
            parser.error('Invalid operation/backup ID')
    if args.mode == 'restore' and not args.backup_id:
        parser.error('restore requires --backup-id')
    repo = Path(__file__).resolve().parents[1]
    main_path = repo / 'infra/nginx/nginx.conf'
    settings = json.loads((repo / 'ansible/logging-settings.json').read_text())
    baseline = settings.get('baseline_sha256', '')
    if not re.fullmatch(r'[a-f0-9]{64}', baseline):
        parser.error('Set the inspected original nginx.conf SHA256 in ansible/logging-settings.json')
    variables = dict(logging_mode=args.mode, run_id=args.run_id, backup_id=args.backup_id,
                     main_path=str(main_path), format_path=str(repo / 'infra/nginx/isucon-json-log.conf'),
                     baseline_sha256=baseline, candidate_sha256=hashlib.sha256(main_path.read_bytes()).hexdigest())
    output = repo.parent / 'artifacts' / args.run_id
    output.parent.mkdir(exist_ok=True)
    try:
        output.mkdir()
    except FileExistsError:
        parser.error('Operation ID already exists')
    metadata = dict(mode=args.mode, run_id=args.run_id, backup_id=args.backup_id,
                    host='isucon-target', status='started',
                    started_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    backup_path='/home/isucon/nginx-log-backups/' + args.run_id)
    try:
        with tempfile.TemporaryDirectory(prefix='nginx-logging-') as tmp:
            varfile = Path(tmp) / 'vars.json'
            varfile.write_text(json.dumps(variables))
            with (output / 'ansible.log').open('w') as log:
                result = subprocess.run(
                    ['ansible-playbook', '-i', str(repo / 'ansible/logging-inventory.yml'),
                     str(repo / 'ansible/nginx-logging.yml'), '-e', '@' + str(varfile)],
                    stdout=log, stderr=subprocess.STDOUT,
                )
            metadata.update(status='passed' if result.returncode == 0 else 'failed', exit_code=result.returncode)
    except OSError as error:
        metadata.update(status='error', exit_code=1, error=str(error))
    finally:
        metadata['finished_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        (output / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(metadata['status'] + ': ' + str(output))
    return 0 if metadata['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
