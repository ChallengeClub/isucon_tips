"""Measure a manually started benchmark; leave instrumentation enabled afterwards."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from metrics import Metrics
from nginx_logs import NginxLogs
from slowlog import SlowLog
from analyze_slowlog import inspect_log


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def measure(output, run_id, preparation_id, deployed_revision=None, input_stream=None):
    stream = sys.stdin if input_stream is None else input_stream
    slow = SlowLog('isucon-target', run_id, output)
    nginx = NginxLogs('isucon-target', run_id, output)
    metrics = Metrics('isucon-target', output)
    metadata = dict(run_id=run_id, preparation_id=preparation_id, target_host='isucon-target',
                    status='starting', started_at_utc=now(), benchmark_executed_by_script=False,
                    deployed_revision=deployed_revision,
                    deployed_revision_note='Operator-reported; not automatically verified',
                    instrumentation_restored=False,
                    note='Collection includes queueing and idle time; it is not the exact benchmark load interval')
    external = dict(source='manual', job_id=None, result='unrecorded', score=None,
                    requested_at_utc=None, started_at_utc=None, finished_at_utc=None,
                    result_path=None, note='Fill only observed values; submission time is not load start time')
    (output / 'benchmark-result.json').write_text(json.dumps(external, indent=2) + '\n')

    def save():
        (output / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')

    def remote(action):
        report = slow.remote(action, preparation_id)
        expected = 'ready' if action == 'check' else 'rotated'
        if report.get('status') != expected:
            raise ValueError('Unexpected continuous-measurement response')
        return report

    completed = False
    metrics_attempted = False
    save()
    try:
        state = remote('check')
        infra = Path(__file__).resolve().parents[1] / 'infra/nginx'
        hashes = {name: hashlib.sha256((infra / name).read_bytes()).hexdigest()
                  for name in ('nginx.conf', 'isucon-json-log.conf')}
        if state.get('nginx_hashes') != hashes:
            raise ValueError('nginx JSON configuration does not match the prepared candidate')
        metadata['initial_state'] = state
        metadata['slowlog_before'] = remote('rotate-before')
        metadata['nginx_before'] = nginx.rotate('before')
        metrics_attempted = True
        metrics.start()
        metadata.update(status='collecting', collection_started_at_utc=now())
        save()
        print('採取準備完了。別操作でbenchmarkを実行し、結果確定後にEnterを押してください。', flush=True)
        if stream.readline() != '\n':
            raise EOFError('Explicit Enter confirmation was not received; benchmark completion is unknown')
        metadata['operator_confirmed_finished_at_utc'] = now()
        metrics_attempted = False
        metadata['metrics_stopped'] = metrics.stop()
        if not metadata['metrics_stopped']:
            raise RuntimeError('OS metrics failed; inspect metrics/')
        metadata['collection_finished_at_utc'] = now()
        metadata['nginx_measurement'] = nginx.rotate('measurement')
        report = remote('rotate-measurement')
        metadata['slowlog_measurement'] = report
        nginx.collect(metadata['nginx_measurement'])
        slow.collect(report)
        slow.metadata.update(status='collected', preparation_id=preparation_id,
                             mode='manual-measurement', finished_at_utc=now())
        slow.save()
        final_state = remote('check')
        metadata['final_state'] = final_state
        if (state['settings'] != final_state['settings']
                or state['app_main_pid'] != final_state['app_main_pid']
                or state['nginx_hashes'] != final_state['nginx_hashes']):
            raise RuntimeError('Prepared settings or application PID changed during collection')
        metadata['logs_collected'] = True
        metadata['analysis'] = {}
        for name in ('analyze-access.sh', 'analyze-slowlog.sh'):
            path = output / ('logs/nginx-access.log' if name == 'analyze-access.sh' else 'sql/slow.log')
            empty = path.stat().st_size == 0
            if name == 'analyze-slowlog.sh' and not empty:
                try:
                    inspect_log(path)
                except ValueError:
                    empty = True  # A newly reopened slow log may contain only the server header.
            if empty:
                metadata['analysis'][name] = {'status': 'skipped', 'reason': 'No records in the collected log'}
                continue
            result = subprocess.run(['bash', str(Path(__file__).with_name(name)), '--run-id', run_id], check=False)
            metadata['analysis'][name] = {'status': 'passed' if result.returncode == 0 else 'error',
                                          'exit_code': result.returncode}
            if result.returncode:
                raise RuntimeError('Local analysis failed; preserved logs can be analyzed separately')
        metadata['status'] = 'collected'
        completed = True
    except (EOFError, KeyboardInterrupt):
        metadata.update(status='interrupted', requires_remote_check=True,
                        error='No completion confirmation; instrumentation remains enabled. Check the external benchmark before further operations')
    except (OSError, RuntimeError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        metadata.update(status='error', requires_remote_check=True, error=str(error))
    finally:
        if metrics_attempted:
            try:
                metadata['metrics_stopped'] = metrics.stop()
            except (OSError, RuntimeError, ValueError) as error:
                metadata['metrics_stop_error'] = str(error)
        metadata['finished_at_utc'] = now()
        if slow.metadata['status'] != 'collected':
            slow.metadata.update(status=metadata['status'], finished_at_utc=now(),
                                 note='Instrumentation was not restored by this measurement')
        slow.save()
        save()
    print(metadata['status'] + ': ' + str(output), flush=True)
    return 0 if completed else 130 if metadata['status'] == 'interrupted' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--preparation-id', required=True, help='Active mysql-slowlog.sh prepare ID')
    parser.add_argument('--deployed-revision', help='Operator-reported full deployed commit SHA')
    args = parser.parse_args()
    from example_guard import require_target_checkout
    require_target_checkout(parser)
    for value in (args.run_id, args.preparation_id):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', value):
            parser.error('Invalid measurement/preparation ID')
    if args.run_id == args.preparation_id:
        parser.error('Measurement ID must differ from preparation ID')
    if args.deployed_revision and not re.fullmatch(r'[a-fA-F0-9]{40}', args.deployed_revision):
        parser.error('Use a full deployed commit SHA')
    if os.environ.get('TARGET_HOST') != 'isucon-target':
        parser.error('Configure the approved target SSH alias')
    for tool in ('alp', 'pt-query-digest'):
        if shutil.which(tool) is None:
            parser.error('Install ' + tool + ' locally and add it to PATH')
    output = Path(__file__).resolve().parents[2] / 'artifacts' / args.run_id
    output.parent.mkdir(exist_ok=True)
    try:
        output.mkdir(mode=0o700)
    except FileExistsError:
        parser.error('Measurement ID already exists')
    return measure(output, args.run_id, args.preparation_id, args.deployed_revision)


if __name__ == '__main__':
    raise SystemExit(main())
