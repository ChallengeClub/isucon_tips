"""Local SSH client for the measurement's nginx log boundaries and collection."""

import datetime
import json
from pathlib import Path
import shlex
import subprocess


class NginxLogs:
    def __init__(self, host, run_id, output):
        if host != 'isucon-target':
            raise ValueError('Only the approved target SSH alias is supported')
        self.host, self.run_id, self.output = host, run_id, output
        self.source = Path(__file__).with_name('nginx_log_remote.py').read_bytes()

    def ssh(self, command):
        return ['ssh', '-o', 'BatchMode=yes', self.host, shlex.join(command)]

    def rotate(self, phase):
        with (self.output / 'operations.log').open('ab') as log:
            log.write((datetime.datetime.now(datetime.timezone.utc).isoformat()
                       + ' nginx logs: ' + phase + '\n').encode())
            log.flush()
            result = subprocess.run(
                self.ssh(['sudo', '-n', '/usr/bin/python3', '-', self.run_id, phase]),
                input=self.source, stdout=subprocess.PIPE, stderr=log,
            )
            log.write(result.stdout)
        if result.returncode:
            raise RuntimeError('Log boundary failed; inspect operations.log and remote files')
        report = json.loads(result.stdout)
        # Do not accept arbitrary paths for privileged collection.
        expected = {name: f'/var/log/nginx/measurements/{self.run_id}/{phase}/{name}'
                    for name in ('access.log', 'error.log')}
        if report.get('phase') != phase or report.get('files') != expected:
            raise ValueError('Unexpected archived log paths')
        return report

    def collect(self, report):
        directory = self.output / 'logs'
        directory.mkdir(exist_ok=True)
        errors = []
        for name, remote_path in report['files'].items():
            path = directory / ('nginx-' + name)
            partial = path.with_suffix(path.suffix + '.partial')
            with partial.open('xb') as data, (self.output / 'operations.log').open('ab') as log:
                result = subprocess.run(
                    self.ssh(['sudo', '-n', 'cat', '--', remote_path]), stdout=data, stderr=log,
                )
            if result.returncode:
                errors.append(name)
            else:
                partial.rename(path)
        if errors:
            raise RuntimeError('Log collection failed: ' + ', '.join(errors))
