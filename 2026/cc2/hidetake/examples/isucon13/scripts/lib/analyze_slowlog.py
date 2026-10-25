"""Run local pt-query-digest on a verified, collected slow log; print no SQL."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def inspect_log(path):
    digest = hashlib.sha256()
    queries = 0
    with path.open('rb') as source:
        for line in source:
            digest.update(line)
            if re.match(rb'^# Query_time: [0-9.]+\s+Lock_time: [0-9.]+\s+Rows_sent: [0-9]+\s+Rows_examined: [0-9]+', line):
                queries += 1
    if not queries:
        raise ValueError('No slow-query records found')
    return digest.hexdigest(), queries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', args.run_id):
        parser.error('Invalid measurement ID')
    directory = Path(__file__).resolve().parents[2].parent / 'artifacts' / args.run_id / 'sql'
    source = directory / 'slow.log'
    collection = json.loads((directory.parent / 'metadata.json').read_text())
    if collection.get('status') != 'collected':
        parser.error('Collection did not finish successfully')
    try:
        metadata = json.loads((directory / 'metadata.json').read_text())
        digest, queries = inspect_log(source)
        if metadata.get('status') != 'collected' or metadata['log']['sha256'] != digest:
            raise ValueError('Only a successfully collected log with matching hash can be analyzed')
    except (OSError, ValueError, KeyError) as error:
        parser.error(str(error))
    tool = shutil.which('pt-query-digest')
    if tool is None:
        parser.error('Install percona-toolkit locally first; see docs/RUNBOOK.md')
    analysis = directory / 'analysis'
    try:
        analysis.mkdir(mode=0o700)  # Refuse overwrite.
    except FileExistsError:
        parser.error('Analysis already exists; preserve the previous report')
    command = [tool, '--config', '/dev/null', '--no-version-check', '--type', 'slowlog',
               '--group-by', 'fingerprint', '--order-by', 'Query_time:sum', '--limit', '100%',
               '--report-format', 'header,profile,query_report', str(source)]
    report = dict(status='started', started_at_utc=now(), input_sha256=digest,
                  input_query_headers=queries, command=command,
                  note='Report and raw log may contain SQL values; keep them outside Git')
    try:
        version = subprocess.run([tool, '--config', '/dev/null', '--version'], capture_output=True, text=True, check=True)
        report['tool_version'] = (version.stdout + version.stderr).strip()
        partial = analysis / 'pt-query-digest.txt.partial'
        with os.fdopen(os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as output, \
                (analysis / 'pt-query-digest.stderr.log').open('wb') as error:
            result = subprocess.run(command, stdout=output, stderr=error)
        report['exit_code'] = result.returncode
        if result.returncode:
            raise RuntimeError('pt-query-digest failed; inspect private analysis files')
        with partial.open('rb') as output:
            if not any(line.startswith(b'# Query ') for line in output):
                raise ValueError('No per-query report was produced')
        partial.rename(analysis / 'pt-query-digest.txt')
        report['status'] = 'passed'
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        report.update(status='error', error=str(error))
    finally:
        report['finished_at_utc'] = now()
        (analysis / 'metadata.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['status'] + ': ' + str(analysis))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
