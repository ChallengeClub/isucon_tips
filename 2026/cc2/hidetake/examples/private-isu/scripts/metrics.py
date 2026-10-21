"""Local controller for a single read-only remote metrics session."""
import datetime
import json
from pathlib import Path
import shlex
import subprocess
import threading


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class Metrics:
    def __init__(self, host, output):
        if host != 'isucon-target':
            raise ValueError('Only the approved target SSH alias is supported')
        self.directory = output / 'metrics'
        self.directory.mkdir()
        source = Path(__file__).with_name('metrics_remote.py').read_text()
        self.argv = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', host,
                     shlex.join(['/usr/bin/python3', '-u', '-c', source])]
        self.metadata = dict(status='starting', target_host=host, started_at_utc=now())
        self.ready = threading.Event()
        self.process = None
        self.thread = None

    def save(self):
        (self.directory / 'metadata.json').write_text(
            json.dumps(self.metadata, ensure_ascii=False, indent=2) + '\n')

    def read(self):
        try:
            for line in self.process.stdout:
                event = json.loads(line)
                kind = event['type']
                if kind == 'line':
                    name, stream = event['name'], event['stream']
                    if name not in ('vmstat', 'mpstat', 'pidstat', 'iostat') or stream not in ('stdout', 'stderr'):
                        raise ValueError('Unexpected metrics output name')
                    with (self.directory / f'{name}.{stream}.log').open('a') as f:
                        f.write(event['text'])
                elif kind == 'ready':
                    self.metadata.update(remote_started_at_utc=event['at_utc'],
                                         info=event['info'], status='running')
                    self.ready.set()
                elif kind == 'error':
                    self.metadata.update(status='error', error=event['error'])
                    self.ready.set()
                elif kind == 'stopped':
                    self.metadata.update(remote_finished_at_utc=event['at_utc'],
                                         collectors=event['results'])
        except Exception as error:
            self.metadata.update(status='error', error=str(error))
        finally:
            self.ready.set()

    def start(self):
        self.save()
        self.stderr = (self.directory / 'ssh.stderr.log').open('w')
        self.process = subprocess.Popen(self.argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=self.stderr, text=True)
        self.thread = threading.Thread(target=self.read, daemon=True)
        self.thread.start()
        if not self.ready.wait(20) or self.metadata['status'] != 'running':
            raise RuntimeError('Metrics startup failed; inspect metrics/')
        self.save()

    def stop(self):
        if self.process:
            try:
                self.process.stdin.close()
            except BrokenPipeError:
                pass
            try:
                code = self.process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.process.kill()
                code = self.process.wait()
                self.metadata['error'] = 'SSH stop timed out; check remote collectors'
            self.thread.join(timeout=5)
            if not self.thread.is_alive():
                self.process.stdout.close()
            self.stderr.close()
            self.metadata['ssh_exit_code'] = code
        elif hasattr(self, 'stderr'):
            self.stderr.close()
        results = self.metadata.get('collectors', {})
        success = (self.metadata['status'] == 'running' and not self.metadata.get('error')
                   and self.metadata.get('ssh_exit_code') == 0 and len(results) == 4
                   and all(not r['exited_before_stop'] and r['exit_code'] in (-15, 0)
                           for r in results.values()))
        self.metadata.update(status='collected' if success else 'error', finished_at_utc=now())
        self.save()
        return success
