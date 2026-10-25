"""ISUCON13 adaptation of the private-isu reference slow-log helper.
Go/isudns sessions and HTTPS health checks are target-specific; original is not run.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import pwd
import grp
import re
import stat
import shutil
import subprocess
import sys
import time

BACKUPS = Path('/var/lib/isucon-mysql-log-backups')
LOGS = Path('/var/log/mysql/measurements')
FIELDS = ('slow_query_log', 'slow_query_log_file', 'long_query_time', 'log_output',
          'min_examined_row_limit', 'log_queries_not_using_indexes',
          'log_slow_admin_statements', 'log_slow_extra', 'log_timestamps')


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def mysql(query):
    result = subprocess.run(['mysql', '--no-defaults', '--batch', '--raw', '--skip-column-names'],
                            input='SET SESSION long_query_time=31536000;\n' + query,
                            capture_output=True, text=True, timeout=20)
    if result.returncode:
        raise RuntimeError('MySQL operation failed (SQL and data omitted)')
    return result.stdout.strip()


def settings():
    pairs = ','.join("'%s',@@GLOBAL.%s" % (name, name) for name in FIELDS)
    return json.loads(mysql("SELECT JSON_OBJECT('server_uuid',@@server_uuid," + pairs + ');'))


def set_value(name, value):
    if name == 'slow_query_log_file':
        value = 'CONVERT(0x' + value.encode().hex() + ' USING utf8mb4)'
    elif name == 'slow_query_log':
        value = str(int(value))
    elif name == 'long_query_time':
        value = str(float(value))
        if not 0 <= float(value) <= 31536000:
            raise ValueError('Invalid saved threshold')
    else:
        raise ValueError('Unexpected setting name')
    mysql('SET GLOBAL ' + name + '=' + value + ';')


def write_json(path, data):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')


def check_session_threshold(expected_threshold):
    rows = mysql("SELECT t.PROCESSLIST_DB,v.VARIABLE_VALUE FROM performance_schema.variables_by_thread v "
                 "JOIN performance_schema.threads t ON t.THREAD_ID=v.THREAD_ID "
                 "WHERE t.PROCESSLIST_DB IN ('isupipe','isudns') AND v.VARIABLE_NAME='long_query_time';").splitlines()
    seen = set()
    for row in rows:
        database, value = row.split('\t')
        seen.add(database)
        if float(value) != float(expected_threshold):
            raise RuntimeError('Application or DNS session threshold differs')
    if seen != {'isupipe', 'isudns'}:
        raise RuntimeError('Both application and DNS sessions must be confirmed')


def restart_and_check(expected_threshold):
    # PowerDNS holds separate persistent MySQL sessions. Keep the current zone.
    before = subprocess.check_output(['pdnsutil','list-zone','u.isucon.local'], stderr=subprocess.DEVNULL)
    if not before.strip():
        raise RuntimeError('Existing DNS zone required')
    for service in ('isupipe-go', 'pdns'):
        subprocess.run(['systemctl','restart',service], check=True, capture_output=True, timeout=60)
    for service in ('isupipe-go','pdns','mysql'):
        subprocess.run(['systemctl','is-active','--quiet',service],check=True,capture_output=True,timeout=10)
    for _ in range(15):
        result = subprocess.run(['curl','--insecure','--silent','--show-error','--fail','--max-time','2',
                                 '--output','/dev/null','--resolve','pipe.u.isucon.local:443:127.0.0.1',
                                 'https://pipe.u.isucon.local/api/tag'],capture_output=True,timeout=5)
        dns = subprocess.run(['dig','@127.0.0.1','pipe.u.isucon.local','A','+short','+time=2','+tries=1'],capture_output=True,timeout=5)
        if result.returncode == 0 and dns.returncode == 0 and dns.stdout.strip() == b'192.0.2.10':
            break
        time.sleep(1)
    else:
        raise RuntimeError('API or DNS health failed')
    after = subprocess.check_output(['pdnsutil','list-zone','u.isucon.local'], stderr=subprocess.DEVNULL)
    if before != after:
        raise RuntimeError('DNS zone changed during reconnection')
    check_session_threshold(expected_threshold)


def log_report(path):
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(block)
    return dict(path=str(path), sha256=digest.hexdigest(), bytes=path.stat().st_size)


def check_owned_settings(current, saved, path):
    if current['server_uuid'] != saved['server_uuid']:
        raise RuntimeError('MySQL server identity changed; inspect before restoring')
    candidate = dict(saved, slow_query_log=1, slow_query_log_file=str(path), long_query_time=0)
    for key in FIELDS:
        if current[key] not in (saved[key], candidate[key], *([0] if key == 'slow_query_log' else [])):
            raise RuntimeError('MySQL settings changed outside this run: ' + key)


def prepared_state(preparation_id):
    if not preparation_id or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', preparation_id):
        raise ValueError('Invalid preparation ID')
    backup = BACKUPS / preparation_id
    if (backup / 'restored.json').exists():
        raise RuntimeError('Preparation was already restored')
    saved = json.loads((backup / 'settings.json').read_text())
    path = LOGS / preparation_id / 'slow.log'
    current = settings()
    if current != dict(saved, slow_query_log=1, slow_query_log_file=str(path), long_query_time=0):
        raise RuntimeError('Expected the active prepared MySQL settings')
    check_session_threshold(0)
    pid = subprocess.check_output(['systemctl', 'show', 'isupipe-go', '--property=MainPID', '--value'], text=True).strip()
    if not pid.isdigit() or int(pid) == 0:
        raise RuntimeError('Application service is not running')
    hashes = {name: hashlib.sha256(Path('/etc/nginx', name).read_bytes()).hexdigest()
              for name in ('nginx.conf', 'isucon-measurement-log-format.conf')}
    extra_pids = {service: int(subprocess.check_output(['systemctl','show',service,'--property=MainPID','--value'],text=True).strip())
                  for service in ('pdns','mysql','nginx')}
    if not all(extra_pids.values()):
        raise RuntimeError('Middleware service is not running')
    return path, dict(preparation_id=preparation_id, app_main_pid=int(pid), middleware_pids=extra_pids,
                      settings=current, nginx_hashes=hashes, at_utc=now())


def mysql_log_open(identity):
    for process in Path('/proc').glob('[0-9]*'):
        try:
            if process.joinpath('comm').read_text().strip() != 'mysqld':
                continue
            for fd in process.joinpath('fd').iterdir():
                try:
                    value = fd.stat()
                    if (value.st_dev, value.st_ino) == identity:
                        return True
                except FileNotFoundError:
                    pass
        except (FileNotFoundError, ProcessLookupError):
            pass
    return False


def continuous_operation(run_id, action, preparation_id):
    path, state = prepared_state(preparation_id)
    if action == 'check':
        return dict(action=action, status='ready', **state)
    phase = {'rotate-before': 'before', 'rotate-measurement': 'measurement'}[action]
    if run_id == preparation_id:
        raise ValueError('Measurement ID must differ from preparation ID')
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError('Expected a regular slow log')
    run = LOGS / run_id
    if phase == 'before':
        run.mkdir(mode=0o700)
        write_json(run / 'preparation.json', {'id': preparation_id})
    elif json.loads((run / 'preparation.json').read_text())['id'] != preparation_id:
        raise ValueError('Measurement belongs to another preparation')
    destination = run / phase
    destination.mkdir(mode=0o700)
    path.rename(destination / 'slow.log')
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.fchown(fd, info.st_uid, info.st_gid)
        os.fchmod(fd, stat.S_IMODE(info.st_mode))
    finally:
        os.close(fd)
    mysql('FLUSH LOCAL SLOW LOGS;')  # Reopen only the slow log; no threshold or service changes.
    for _ in range(100):
        if not mysql_log_open((info.st_dev, info.st_ino)):
            return dict(action=action, status='rotated', reopened_at_utc=now(),
                        state=state, log=log_report(destination / 'slow.log'))
        time.sleep(0.1)
    raise RuntimeError('MySQL still holds the archived slow log; inspect before retry')


def operate(run_id, action, controller_id, preparation_id=None):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', run_id):
        raise ValueError('Invalid measurement ID')
    if action in ('check', 'rotate-before', 'rotate-measurement'):
        return continuous_operation(run_id, action, preparation_id)
    backup = BACKUPS / run_id
    path = LOGS / run_id / 'slow.log'
    if action == 'start':
        current = settings()
        if shutil.disk_usage('/var/log/mysql').free < 4 * 1024**3:
            raise RuntimeError('At least 4 GiB free space required before all-query logging')
        if current['slow_query_log'] or current['log_output'] != 'FILE' or current['min_examined_row_limit'] != 0:
            raise RuntimeError('Expected slow log OFF, FILE output and min_examined_row_limit=0')
        if backup.exists() or path.parent.exists():
            raise FileExistsError('Measurement ID already exists remotely')
        for service in ('isupipe-go', 'mysql'):
            subprocess.run(['systemctl', 'is-active', '--quiet', service], check=True, timeout=10)
        BACKUPS.mkdir(mode=0o700, exist_ok=True)
        backup.mkdir(mode=0o700)
        write_json(backup / 'controller.json', {'id': controller_id})
        write_json(backup / 'settings.json', current)  # Before changing MySQL or restarting the app.
        uid, gid = pwd.getpwnam('mysql').pw_uid, grp.getgrnam('adm').gr_gid
        LOGS.mkdir(mode=0o750, exist_ok=True)
        os.chown(LOGS, uid, gid)
        path.parent.mkdir(mode=0o750)
        os.chown(path.parent, uid, gid)
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o640)
        os.fchown(fd, uid, gid)
        os.close(fd)
        set_value('slow_query_log_file', str(path))
        set_value('long_query_time', 0)
        restart_and_check(0)  # Logging stays OFF during restart and warm-up.
        set_value('slow_query_log', 1)
        actual = settings()
        if actual != dict(current, slow_query_log=1, slow_query_log_file=str(path), long_query_time=0):
            raise RuntimeError('Slow log settings did not match the candidate')
        return dict(action=action, status='ready', at_utc=now(), path=str(path), backup=str(backup))
    if action not in ('restore', 'pause'):
        raise ValueError('Invalid action')
    if not backup.exists():
        return dict(action=action, status='not_started', at_utc=now())
    if controller_id != 'manual' and json.loads((backup / 'controller.json').read_text())['id'] != controller_id:
        raise RuntimeError('Backup belongs to another invocation; use explicit manual restoration')
    saved = json.loads((backup / 'settings.json').read_text())
    current = settings()
    check_owned_settings(current, saved, path)
    # Avoid stopping a different run, even if the original run was already restored.
    restored = backup / 'restored.json'
    if restored.exists():
        if current != saved:
            raise RuntimeError('Settings changed after restoration')
        return dict(action=action, status='restored', at_utc=now(), log=log_report(path) if path.exists() else None)
    set_value('slow_query_log', 0)
    if action == 'pause':
        return dict(action=action, status='paused', at_utc=now())
    set_value('long_query_time', saved['long_query_time'])
    set_value('slow_query_log_file', saved['slow_query_log_file'])
    restart_and_check(saved['long_query_time'])
    set_value('slow_query_log', saved['slow_query_log'])
    if settings() != saved:
        raise RuntimeError('MySQL settings did not match the saved state')
    report = dict(action=action, status='restored', at_utc=now(),
                  log=log_report(path) if path.exists() else None)
    write_json(restored, report)
    return report


if __name__ == '__main__':
    try:
        print(json.dumps(operate(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)))
    except Exception as error:
        # Do not print SQL text or exception output containing data.
        print('Slow log operation failed (' + type(error).__name__ + '); inspect saved state, no automatic rollback.', file=sys.stderr)
        sys.exit(1)
