"""ISUCON13 adaptation: Go/MySQL/nginx/PowerDNS and inspected nvme0n1."""
import datetime
import json
import os
import signal
import subprocess
import sys
import threading
import time


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def stop_group(process):
    """Stop the full group we created, even if its launcher already exited."""
    early = process.poll()
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        code = process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        code = process.wait(timeout=5)
    return early, code


def main():
    lock = threading.Lock()
    processes = {}
    threads = []
    env = dict(os.environ, LC_ALL='C', TZ='UTC', S_TIME_FORMAT='ISO')

    def emit(event):
        with lock:
            print(json.dumps(dict(at_utc=now(), **event)), flush=True)

    def capture(argv):
        return subprocess.check_output(argv, env=env, text=True).strip()

    def pump(name, stream, pipe):
        for line in pipe:
            emit(dict(type='line', name=name, stream=stream, text=line))

    try:
        # Names and IDs only: never collect process arguments or environments.
        ps = capture(['ps', '-eo', 'pid=,ppid=,user=,comm='])
        pids = [line.split()[0] for line in ps.splitlines()
                if line.split()[-1] in ('isupipe', 'mysqld', 'nginx', 'pdns_server')]
        if not pids:
            raise RuntimeError('No application/middleware PIDs found')
        commands = {
            'vmstat': ['vmstat', '-w', '-t', '1'],
            'mpstat': ['mpstat', '-P', 'ALL', '1'],
            'pidstat': ['pidstat', '-h', '-u', '-r', '-d', '-p', ','.join(pids), '1'],
            'iostat': ['iostat', '-x', '-y', '-t', 'nvme0n1', '1'],
        }
        info = dict(kernel=capture(['uname', '-r']), process_map=ps,
                    tracked_pids=pids,
                    versions={n: capture([n, '-V']) for n in ('mpstat', 'pidstat', 'iostat')},
                    vmstat_version=capture(['vmstat', '-V']),
                    task_delayacct=(capture(['cat', '/proc/sys/kernel/task_delayacct'])
                                    if os.path.exists('/proc/sys/kernel/task_delayacct') else None),
                    commands=commands)
        for name, argv in commands.items():
            p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 text=True, env=env, stdin=subprocess.DEVNULL,
                                 start_new_session=True)
            processes[name] = p
            for stream in ('stdout', 'stderr'):
                t = threading.Thread(target=pump, args=(name, stream, getattr(p, stream)))
                t.start()
                threads.append(t)
        time.sleep(1.2)  # Catch missing sudo permission/failed collectors before benchmark.
        if any(p.poll() is not None for p in processes.values()):
            raise RuntimeError('A collector exited during startup')
        info['worker_pid'] = os.getpid()
        info['collector_pids'] = {name: p.pid for name, p in processes.items()}
        emit(dict(type='ready', info=info))
        # EOF is the stop request, including controller/SSH disconnection.
        while sys.stdin.read(1):
            pass
    except Exception as error:
        emit(dict(type='error', error=str(error)))
    finally:
        results = {}
        for name, p in processes.items():
            early, code = stop_group(p)
            results[name] = dict(exit_code=code, exited_before_stop=early is not None)
        for t in threads:
            t.join(timeout=5)
        for p in processes.values():
            p.stdout.close()
            p.stderr.close()
        emit(dict(type='stopped', results=results))


if __name__ == '__main__':
    main()
