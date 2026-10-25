"""Read-only measurement inventory; no source/env/credential contents or log data."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess


def run(args, timeout=15):
    try:
        p = subprocess.run(args, capture_output=True, timeout=timeout)
        return p.returncode, p.stdout.decode(errors='replace')
    except (OSError, subprocess.TimeoutExpired):
        return -1, ''


def metadata(path, hash_content=False):
    p = Path(path)
    try:
        s = p.lstat()
    except FileNotFoundError:
        return dict(path=path, exists=False)
    row = dict(path=path, exists=True, uid=s.st_uid, gid=s.st_gid,
               mode=oct(stat.S_IMODE(s.st_mode)), size=s.st_size)
    if stat.S_ISLNK(s.st_mode):
        row['symlink_target'] = os.readlink(p)
    elif hash_content and stat.S_ISREG(s.st_mode):
        row['sha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
    return row


def main():
    report = dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    configs = ['/etc/nginx/nginx.conf', '/etc/nginx/sites-enabled/isupipe.conf',
               '/etc/nginx/isucon-measurement-log-format.conf']
    report['nginx_configs'] = [metadata(p, True) for p in configs]
    report['log_metadata'] = [metadata(str(p)) for directory in ['/var/log/nginx', '/var/log/mysql']
                              if Path(directory).is_dir() for p in Path(directory).iterdir() if p.is_file()]
    report['config_directory_metadata'] = [metadata(str(p)) for directory in
        ['/etc/nginx/conf.d', '/etc/nginx/sites-enabled', '/etc/mysql/mysql.conf.d']
        if Path(directory).is_dir() for p in Path(directory).iterdir()]
    report['tool_paths'] = {name: shutil.which(name) for name in ['vmstat', 'mpstat', 'pidstat', 'iostat', 'timeout']}
    for name, args in {
        'block_devices': ['lsblk', '-J', '-o', 'NAME,TYPE,SIZE,MOUNTPOINTS'],
        'disk_space': ['df', '-h', '/'],
        'process_map': ['ps', '-eo', 'pid=,ppid=,user=,comm='],
        'services': ['systemctl', 'show', 'isupipe-go', 'nginx', 'mysql', 'pdns',
                     '-p', 'Id', '-p', 'MainPID', '-p', 'ActiveState'],
    }.items():
        code, data = run(args)
        report[name] = dict(exit_code=code, output=data.strip())
    # Only explicitly named non-secret server variables; no table data/statements.
    variables = ['slow_query_log','slow_query_log_file','long_query_time','log_output',
                 'min_examined_row_limit','log_queries_not_using_indexes','log_slow_admin_statements',
                 'log_slow_extra','log_timestamps','performance_schema']
    sql = 'SELECT @@version; SHOW GLOBAL VARIABLES WHERE Variable_name IN (' + ','.join("'"+n+"'" for n in variables) + ');'
    code, data = run(['mysql', '--no-defaults', '--batch', '--skip-column-names', '-e', sql])
    report['mysql_variables'] = dict(exit_code=code, output=data.strip() if code == 0 else None)
    sql = ("SELECT t.PROCESSLIST_DB,v.VARIABLE_VALUE,COUNT(*) FROM performance_schema.variables_by_thread v "
           "JOIN performance_schema.threads t ON t.THREAD_ID=v.THREAD_ID "
           "WHERE t.PROCESSLIST_DB IN ('isupipe','isudns') AND v.VARIABLE_NAME='long_query_time' "
           "GROUP BY t.PROCESSLIST_DB,v.VARIABLE_VALUE;")
    code, data = run(['mysql','--no-defaults','--batch','--skip-column-names','-e',sql])
    report['mysql_session_thresholds'] = dict(exit_code=code, output=data.strip() if code == 0 else None)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
