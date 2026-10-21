#!/usr/bin/env python3
"""Validate a collected JSON access log and save an alp report locally."""

import argparse
import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess


GROUPS = r'^/posts/[0-9]+$,^/image/[0-9]+\.(jpg|png|gif)$,^/@[^/]+$'


def validate(path):
    count = 0
    with path.open() as source:
        for number, line in enumerate(source, 1):
            try:
                row = json.loads(line)
                assert isinstance(row, dict)
                assert isinstance(row['time'], str)
                assert isinstance(row['method'], str)
                assert isinstance(row['uri'], str) and row['uri'].startswith('/')
                assert isinstance(row['status'], int) and not isinstance(row['status'], bool)
                assert 100 <= row['status'] <= 599
                for key in ['body_bytes', 'request_time']:
                    assert isinstance(row[key], (int, float)) and not isinstance(row[key], bool)
                    assert math.isfinite(row[key]) and row[key] >= 0
                assert isinstance(row['upstream_response_time'], str)
            except (ValueError, KeyError, AssertionError, TypeError):
                raise ValueError(f'Invalid JSON access log at line {number}; check log format') from None
            count += 1
    if not count:
        raise ValueError('Access log is empty')
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    from example_guard import require_target_checkout
    require_target_checkout(parser)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', args.run_id):
        parser.error('Invalid run ID')
    root = Path(__file__).resolve().parents[2] / 'artifacts' / args.run_id
    log = root / 'logs/nginx-access.log'
    try:
        count = validate(log)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    alp = shutil.which('alp')
    if alp is None:
        parser.error('Install alp locally first; see docs/RUNBOOK.md')
    directory = root / 'analysis'
    try:
        directory.mkdir()  # Do not overwrite an earlier analysis.
    except FileExistsError:
        parser.error('Analysis already exists; preserve or move the earlier analysis first')
    command = [alp, 'json', '--file', str(log), '--restime-key', 'request_time',
               '--sort', 'sum', '--reverse', '--matching-groups', GROUPS,
               '--output', 'count,method,uri,sum,avg,p95,max', '--format', 'tsv']
    metadata = dict(started_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
                    input_lines=count, command=command, timing='request_time', status='started')
    try:
        version = subprocess.run([alp, '--version'], capture_output=True, text=True, check=True)
        metadata['alp_version'] = (version.stdout + version.stderr).strip()
        with (directory / 'alp.txt.partial').open('w') as output, (directory / 'alp.stderr.log').open('w') as error:
            result = subprocess.run(command, stdout=output, stderr=error)
        metadata['exit_code'] = result.returncode
        metadata['status'] = 'passed' if result.returncode == 0 else 'failed'
        if result.returncode == 0:
            (directory / 'alp.txt.partial').rename(directory / 'alp.txt')
    except (OSError, subprocess.CalledProcessError) as error:
        metadata.update(status='error', error=str(error))
    finally:
        metadata['finished_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        (directory / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(metadata['status'] + ': ' + str(directory))
    return 0 if metadata['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
