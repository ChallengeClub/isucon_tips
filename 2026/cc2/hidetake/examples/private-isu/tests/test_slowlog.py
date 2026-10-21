"""Local files and mocked services only: never change a server or run benchmark."""
import contextlib
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


remote = load('slowlog_remote')
local = load('slowlog')
BASELINE = dict(server_uuid='test', slow_query_log=0, slow_query_log_file='/var/lib/mysql/original-slow.log',
                long_query_time=10, log_output='FILE', min_examined_row_limit=0,
                log_queries_not_using_indexes=0, log_slow_admin_statements=0,
                log_slow_extra=0, log_timestamps='UTC')


class RemoteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = copy.deepcopy(BASELINE)
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(remote, 'BACKUPS', self.root / 'backups'))
        stack.enter_context(patch.object(remote, 'LOGS', self.root / 'logs'))
        stack.enter_context(patch.object(remote, 'settings', side_effect=lambda: dict(self.state)))
        stack.enter_context(patch.object(remote, 'set_value', side_effect=lambda n, v: self.state.update({n: v})))
        stack.enter_context(patch.object(remote.os, 'chown'))
        stack.enter_context(patch.object(remote.os, 'fchown'))
        stack.enter_context(patch.object(remote.pwd, 'getpwnam', return_value=type('User', (), {'pw_uid': os.getuid()})()))
        stack.enter_context(patch.object(remote.grp, 'getgrnam', return_value=type('Group', (), {'gr_gid': os.getgid()})()))
        stack.enter_context(patch.object(remote.subprocess, 'run'))
        self.restart = stack.enter_context(patch.object(remote, 'restart_and_check'))

    def test_start_and_restore_preserve_settings_and_closed_log(self):
        report = remote.operate('run1', 'start', 'owner')
        self.assertEqual(report['status'], 'ready')
        path = Path(report['path'])
        self.assertEqual(self.state['long_query_time'], 0)
        self.assertEqual(self.state['slow_query_log'], 1)
        saved = self.root / 'backups/run1/settings.json'
        self.assertEqual(json.loads(saved.read_text()), BASELINE)
        self.assertEqual(stat.S_IMODE(saved.stat().st_mode), 0o600)
        path.write_bytes(b'keep measurement\n')
        restored = remote.operate('run1', 'restore', 'owner')
        self.assertEqual(self.state, BASELINE)
        self.assertEqual(restored['log']['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual([c.args for c in self.restart.call_args_list], [(0,), (10,)])
        remote.operate('run1', 'restore', 'manual')
        self.assertEqual(self.restart.call_count, 2)  # A repeated restore does not restart again.

    def test_pause_disables_log_without_restarting_or_changing_session_threshold(self):
        remote.operate('run1', 'start', 'owner')
        remote.operate('run1', 'pause', 'owner')
        self.assertEqual(self.state['slow_query_log'], 0)
        self.assertEqual(self.state['long_query_time'], 0)
        self.assertEqual(self.restart.call_count, 1)
        remote.operate('run1', 'restore', 'manual')
        self.assertEqual(self.state, BASELINE)

    def test_duplicate_or_wrong_invocation_does_not_restore_another_run(self):
        remote.operate('run1', 'start', 'owner')
        candidate = dict(self.state)
        with self.assertRaises(RuntimeError):
            remote.operate('run1', 'start', 'other')
        with self.assertRaises(RuntimeError):
            remote.operate('run1', 'restore', 'other')
        self.assertEqual(self.state, candidate)

    def test_failed_start_can_restore_from_saved_settings(self):
        self.restart.side_effect = [RuntimeError('start failed'), None]
        with self.assertRaises(RuntimeError):
            remote.operate('run1', 'start', 'owner')
        remote.operate('run1', 'restore', 'owner')
        self.assertEqual(self.state, BASELINE)

    def test_foreign_change_is_not_overwritten(self):
        remote.operate('run1', 'start', 'owner')
        self.state['long_query_time'] = 5
        with self.assertRaisesRegex(RuntimeError, 'outside this run'):
            remote.operate('run1', 'restore', 'owner')
        self.assertEqual(self.state['long_query_time'], 5)

    def test_nonbaseline_is_rejected_before_backup_or_restart(self):
        self.state['log_output'] = 'TABLE'
        with self.assertRaises(RuntimeError):
            remote.operate('run1', 'start', 'owner')
        self.assertFalse((self.root / 'backups').exists())
        self.restart.assert_not_called()


class CollectionTests(unittest.TestCase):
    def test_transfer_must_match_path_hash_and_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            c = local.SlowLog('isucon-target', 'run1', Path(tmp))
            content = b'private SQL log\n'
            info = dict(path='/var/log/mysql/measurements/run1/slow.log',
                        sha256=hashlib.sha256(content).hexdigest(), bytes=len(content))

            def transfer(*args, **kwargs):
                kwargs['stdout'].write(content)
                return subprocess.CompletedProcess(args, 0)

            with patch.object(local.subprocess, 'run', side_effect=transfer):
                c.collect({'log': info})
            self.assertEqual((c.directory / 'slow.log').read_bytes(), content)
            self.assertEqual(stat.S_IMODE((c.directory / 'slow.log').stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(c.directory.stat().st_mode), 0o700)
            with self.assertRaises(ValueError):
                c.collect({'log': dict(info, path='/etc/shadow')})

    def test_hash_mismatch_keeps_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            c = local.SlowLog('isucon-target', 'run1', Path(tmp))
            def transfer(*args, **kwargs):
                kwargs['stdout'].write(b'wrong')
                return subprocess.CompletedProcess(args, 0)
            with patch.object(local.subprocess, 'run', side_effect=transfer), self.assertRaises(ValueError):
                c.collect({'log': dict(path='/var/log/mysql/measurements/run1/slow.log', sha256='0'*64, bytes=5)})
            self.assertTrue((c.directory / 'slow.log.partial').exists())
            self.assertFalse((c.directory / 'slow.log').exists())


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(SCRIPTS, self.root / 'target/scripts', ignore=shutil.ignore_patterns('__pycache__'))
        (self.root / 'target/.git').mkdir()
        directory = self.root / 'artifacts/run1/sql'
        directory.mkdir(parents=True)
        content = (Path(__file__).parent / 'fixtures/mysql-slow.txt').read_bytes()
        (directory / 'slow.log').write_bytes(content)
        (directory / 'metadata.json').write_text(json.dumps(dict(status='collected', log={'sha256': hashlib.sha256(content).hexdigest()})))
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        tool = self.bin / 'pt-query-digest'
        tool.write_text('''#!/usr/bin/python3
import os,sys
assert sys.argv[1:3]==['--config','/dev/null']
if '--version' in sys.argv:print('pt-query-digest test');sys.exit(0)
assert '--no-version-check' in sys.argv
print('# Query 1: sample report with PRIVATE_VALUE')
sys.exit(1 if os.environ.get('PT_FAIL') else 0)
''')
        tool.chmod(0o755)
        self.env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ['PATH'])
        self.command = ['bash', str(self.root / 'target/scripts/analyze-slowlog.sh'), '--run-id', 'run1']

    def test_local_analysis_saves_report_without_printing_values_and_refuses_overwrite(self):
        result = subprocess.run(self.command, env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('PRIVATE_VALUE', result.stdout + result.stderr)
        directory = self.root / 'artifacts/run1/sql/analysis'
        metadata = json.loads((directory / 'metadata.json').read_text())
        self.assertEqual(metadata['input_query_headers'], 2)
        self.assertEqual(metadata['status'], 'passed')
        self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)
        self.assertNotEqual(subprocess.run(self.command, env=self.env, capture_output=True).returncode, 0)

    def test_analysis_failure_keeps_partial_report(self):
        result = subprocess.run(self.command, env=dict(self.env, PT_FAIL='1'), capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertTrue((self.root / 'artifacts/run1/sql/analysis/pt-query-digest.txt.partial').exists())

if __name__ == '__main__':
    unittest.main()
