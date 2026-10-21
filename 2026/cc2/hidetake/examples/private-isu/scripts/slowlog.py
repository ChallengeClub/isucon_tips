"""Local controller for explicitly approved slow-log measurement and restoration."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import uuid


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class SlowLog:
    def __init__(self, host, run_id, output):
        if host != 'isucon-target' or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', run_id):
            raise ValueError('Invalid target alias or measurement ID')
        self.host, self.run_id = host, run_id
        self.directory = output / 'sql'
        self.directory.mkdir(mode=0o700)
        self.source = Path(__file__).with_name('slowlog_remote.py').read_bytes()
        self.metadata = dict(status='not_started', run_id=run_id, target_host=host,
                             backup=f'/home/isucon/mysql-log-backups/{run_id}', started_at_utc=now())
        self.attempted = False
        self.ready = False
        self.controller_id = uuid.uuid4().hex

    def save(self):
        (self.directory / 'metadata.json').write_text(json.dumps(self.metadata, indent=2) + '\n')

    def ssh(self, argv):
        return ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', self.host, shlex.join(argv)]

    def remote(self, action, preparation_id=None):
        with (self.directory / 'operations.log').open('ab') as log:
            log.write((now() + ' ' + action + '\n').encode())
            log.flush()
            command = ['sudo', '-n', '/usr/bin/python3', '-', self.run_id, action, self.controller_id]
            if preparation_id is not None:
                command.append(preparation_id)
            result = subprocess.run(self.ssh(command),
                                    input=self.source, stdout=subprocess.PIPE, stderr=log, timeout=180)
            log.write(result.stdout)
        if result.returncode:
            raise RuntimeError('Slow log ' + action + ' failed; inspect sql/operations.log and restore if needed')
        report = json.loads(result.stdout)
        if report.get('action') != action:
            raise ValueError('Unexpected slow-log response')
        return report

    def start(self):
        self.attempted = True
        self.metadata['status'] = 'starting'
        self.save()
        try:
            report = self.remote('start')
            if report['status'] != 'ready':
                raise ValueError('Slow log did not become ready')
            self.ready = True
            self.metadata.update(status='ready', start=report)
            self.save()
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
            self.metadata.update(status='error', error=str(error))
            self.save()
            raise RuntimeError('Slow log startup failed; automatic restoration will be attempted') from error

    def collect(self, report):
        base = f'/var/log/mysql/measurements/{self.run_id}'
        expected = (base + '/slow.log', base + '/measurement/slow.log')
        info = report.get('log')
        if not info or info.get('path') not in expected:
            raise ValueError('Unexpected slow-log collection path')
        partial = self.directory / 'slow.log.partial'
        with os.fdopen(os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as data, \
                (self.directory / 'operations.log').open('ab') as log:
            result = subprocess.run(self.ssh(['sudo', '-n', 'cat', '--', info['path']]), stdout=data, stderr=log)
        if result.returncode:
            raise RuntimeError('Slow log transfer failed')
        digest = hashlib.sha256()
        with partial.open('rb') as data:
            for block in iter(lambda: data.read(1024 * 1024), b''):
                digest.update(block)
        if digest.hexdigest() != info['sha256'] or partial.stat().st_size != info['bytes']:
            raise ValueError('Slow log size/hash mismatch')
        partial.rename(self.directory / 'slow.log')
        self.metadata['log'] = info

    def finish(self, benchmark_status, ssh_exit_code):
        try:
            if not self.attempted:
                return False
            if benchmark_status == 'interrupted' or ssh_exit_code == 255:
                self.metadata['pause'] = self.remote('pause')
                self.metadata.update(status='requires_remote_check',
                                     error='Logging paused; check remote benchmark before restoring and restarting the app')
                return False
            report = self.remote('restore')
            self.metadata['restore'] = report
            self.metadata['restored'] = report['status'] == 'restored'
            if not self.ready:
                self.metadata['status'] = 'error'
                return False
            if not self.metadata['restored']:
                raise RuntimeError('Restoration was not confirmed')
            self.collect(report)
            self.metadata['status'] = 'collected'
            return True
        except (OSError, RuntimeError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
            self.metadata.update(status='error', error=str(error))
            return False
        finally:
            self.metadata['finished_at_utc'] = now()
            self.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('probe', 'prepare', 'restore'), required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--backup-id')
    args = parser.parse_args()
    from example_guard import require_target_checkout
    require_target_checkout(parser)
    if os.environ.get("TARGET_HOST") != "isucon-target":
        parser.error("Configure the approved target SSH alias in config.sh")
    for value in (args.run_id, args.backup_id or args.run_id):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', value):
            parser.error('Invalid operation/backup ID')
    if args.mode == 'restore' and not args.backup_id:
        parser.error('restore requires --backup-id')
    if args.mode != 'restore' and args.backup_id:
        parser.error('--backup-id is only used for restore')
    output = Path(__file__).resolve().parents[2] / 'artifacts' / args.run_id
    output.parent.mkdir(exist_ok=True)
    try:
        output.mkdir(mode=0o700)  # Refuse overwriting an operation.
    except FileExistsError:
        parser.error('Operation ID already exists')
    controller = SlowLog('isucon-target', args.backup_id or args.run_id, output)
    controller.metadata.update(operation=args.mode, operation_run_id=args.run_id)
    success = False
    keep_enabled = False
    try:
        if args.mode == 'restore':
            controller.attempted = controller.ready = True
            controller.controller_id = 'manual'
        else:
            controller.start()
            if args.mode == 'prepare':
                keep_enabled = True
            else:
                result = subprocess.run(['ssh', '-o', 'BatchMode=yes', 'isucon-target',
                                     'curl --fail --silent --show-error --max-time 15 --output /dev/null http://127.0.0.1/'],
                                    capture_output=True, timeout=25)
                if result.returncode:
                    raise RuntimeError('Probe HTTP request failed')
        success = True
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired):
        controller.metadata['probe_or_restore_error'] = True
    except KeyboardInterrupt:
        controller.metadata['probe_or_restore_error'] = True
    finally:
        if keep_enabled:
            controller.metadata['prepared_at_utc'] = now()
            controller.save()
        else:
            success = controller.finish('completed', 0) and success
    print(('passed' if success else 'error') + ': ' + str(output))
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
