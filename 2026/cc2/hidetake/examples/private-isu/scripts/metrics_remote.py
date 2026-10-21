"""Read-only collectors, streamed to the local controller; no remote files."""
import datetime
import json
import os
import subprocess
import sys
import threading
import time


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


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
                if line.split()[-1] in ('ruby', 'mysqld', 'nginx', 'memcached')]
        if not pids:
            raise RuntimeError('No application/middleware PIDs found')
        commands = {
            'vmstat': ['vmstat', '-w', '-t', '1'],
            'mpstat': ['mpstat', '-P', 'ALL', '1'],
            'pidstat': ['sudo', '-n', 'env', 'LC_ALL=C', 'TZ=UTC', 'S_TIME_FORMAT=ISO',
                        'pidstat', '-h', '-u', '-r', '-d', '-p', ','.join(pids), '1'],
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
                                 text=True, env=env)
            processes[name] = p
            for stream in ('stdout', 'stderr'):
                t = threading.Thread(target=pump, args=(name, stream, getattr(p, stream)))
                t.start()
                threads.append(t)
        time.sleep(1.2)  # Catch missing sudo permission/failed collectors before benchmark.
        if any(p.poll() is not None for p in processes.values()):
            raise RuntimeError('A collector exited during startup')
        emit(dict(type='ready', info=info))
        # EOF is the stop request, including controller/SSH disconnection.
        while sys.stdin.read(1):
            pass
    except Exception as error:
        emit(dict(type='error', error=str(error)))
    finally:
        results = {}
        for name, p in processes.items():
            early = p.poll()
            if early is None:
                p.terminate()
            try:
                code = p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
                code = p.wait()
            results[name] = dict(exit_code=code, exited_before_stop=early is not None)
        for t in threads:
            t.join()
        for p in processes.values():
            p.stdout.close()
            p.stderr.close()
        emit(dict(type='stopped', results=results))


if __name__ == '__main__':
    main()
