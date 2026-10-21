"""Manual measurement lifecycle and real local slow-log rotation, no real SSH."""
import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import measurement

spec = importlib.util.spec_from_file_location('continuous_remote', SCRIPTS / 'slowlog_remote.py')
remote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(remote)


class RotationTests(unittest.TestCase):
    def test_two_measurements_keep_settings_pid_permissions_and_archived_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / 'prepare1/slow.log'
            path.parent.mkdir()
            path.write_bytes(b'ambient\n')
            path.chmod(0o640)
            state = dict(preparation_id='prepare1', app_main_pid=123, settings={'slow_query_log': 1, 'long_query_time': 0})
            with patch.object(remote, 'LOGS', root), \
                    patch.object(remote, 'prepared_state', side_effect=lambda _: (path, copy.deepcopy(state))), \
                    patch.object(remote, 'mysql') as mysql, \
                    patch.object(remote, 'mysql_log_open', return_value=False), \
                    patch.object(remote, 'set_value') as set_value, \
                    patch.object(remote, 'restart_and_check') as restart:
                for run in ('measure1', 'measure2'):
                    before = path.read_bytes()
                    remote.operate(run, 'rotate-before', 'owner', 'prepare1')
                    path.write_bytes((run + '\n').encode())
                    report = remote.operate(run, 'rotate-measurement', 'owner', 'prepare1')
                    self.assertEqual((root / run / 'before/slow.log').read_bytes(), before)
                    self.assertEqual(Path(report['log']['path']).read_bytes(), (run + '\n').encode())
                    self.assertEqual(report['state'], state)
                    self.assertEqual(path.read_bytes(), b'')
                    self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)
                    path.write_bytes(b'between\n')
                self.assertEqual((root / 'measure1/measurement/slow.log').read_bytes(), b'measure1\n')
                self.assertEqual(mysql.call_count, 4)
                self.assertTrue(all(c.args == ('FLUSH LOCAL SLOW LOGS;',) for c in mysql.call_args_list))
                restart.assert_not_called()
                set_value.assert_not_called()
                with self.assertRaises(FileExistsError):
                    remote.operate('measure1', 'rotate-before', 'owner', 'prepare1')
                with self.assertRaises(ValueError):
                    remote.operate('prepare1', 'rotate-before', 'owner', 'prepare1')

    def test_reopen_failure_preserves_log_and_refuses_to_call_it_completed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / 'prepare1/slow.log'
            path.parent.mkdir()
            path.write_bytes(b'preserve\n')
            with patch.object(remote, 'LOGS', root), \
                    patch.object(remote, 'prepared_state', return_value=(path, {})), \
                    patch.object(remote, 'mysql', side_effect=RuntimeError('flush failed')):
                with self.assertRaises(RuntimeError):
                    remote.operate('measure1', 'rotate-before', 'owner', 'prepare1')
            self.assertEqual((root / 'measure1/before/slow.log').read_bytes(), b'preserve\n')
            self.assertTrue(path.exists())

    def test_restored_preparation_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'prepare1').mkdir()
            (root / 'prepare1/restored.json').write_text('{}')
            with patch.object(remote, 'BACKUPS', root), self.assertRaisesRegex(RuntimeError, 'already restored'):
                remote.prepared_state('prepare1')


class MeasurementTests(unittest.TestCase):
    def run_case(self, response='\n', failure=None):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        output = Path(temp.name)
        events = []
        infra = SCRIPTS.parent / 'infra/nginx'
        hashes = {n: measurement.hashlib.sha256((infra / n).read_bytes()).hexdigest()
                  for n in ('nginx.conf', 'isucon-json-log.conf')}
        state = dict(status='ready', preparation_id='prep1', settings={'slow_query_log': 1},
                     app_main_pid=123, nginx_hashes=hashes)
        check_count = 0

        class FakeSlow:
            def __init__(self, *args):
                self.metadata = {'status': 'not_started'}
                (output / 'sql').mkdir()

            def remote(self, action, preparation_id):
                nonlocal check_count
                events.append(action)
                if failure == action:
                    raise RuntimeError('failed ' + action)
                if action == 'check':
                    check_count += 1
                    result = copy.deepcopy(state)
                    if failure == 'pid_changed' and check_count == 2:
                        result['app_main_pid'] = 999
                    if failure == 'nginx_changed':
                        result['nginx_hashes'] = {}
                    return result
                return dict(status='rotated', log={'path': 'mock'})

            def collect(self, report):
                events.append('slow-collect')
                if failure == 'transfer':
                    raise RuntimeError('transfer failed')
                (output / 'sql/slow.log').write_text('server header\n' if failure == 'empty-logs' else
                    '# Query_time: 0.1  Lock_time: 0  Rows_sent: 1  Rows_examined: 1\nSELECT 1;\n')

            def save(self):
                pass

        class FakeNginx:
            def __init__(self, *args):
                pass

            def rotate(self, phase):
                events.append('nginx-' + phase)
                return {'phase': phase}

            def collect(self, report):
                events.append('nginx-collect')
                (output / 'logs').mkdir()
                (output / 'logs/nginx-access.log').write_text('' if failure == 'empty-logs' else '{}\n')

        class FakeMetrics:
            def __init__(self, *args):
                pass

            def start(self):
                events.append('metrics-start')
                if failure == 'metrics-start':
                    raise RuntimeError('metrics start failed')

            def stop(self):
                events.append('metrics-stop')
                return failure != 'metrics-stop'

        class Operator:
            def readline(self):
                events.append('operator-finish')
                self_meta = json.loads((output / 'metadata.json').read_text())
                assert self_meta['status'] == 'collecting'
                if response == 'interrupt':
                    raise KeyboardInterrupt
                return response

        def analyze(argv, **kwargs):
            events.append(Path(argv[1]).name)
            return subprocess.CompletedProcess(argv, 1 if failure == 'analysis' else 0)

        with patch.object(measurement, 'SlowLog', FakeSlow), \
                patch.object(measurement, 'NginxLogs', FakeNginx), \
                patch.object(measurement, 'Metrics', FakeMetrics), \
                patch.object(measurement.subprocess, 'run', side_effect=analyze), \
                contextlib.redirect_stdout(io.StringIO()):
            code = measurement.measure(output, 'measure1', 'prep1', input_stream=Operator())
        return code, json.loads((output / 'metadata.json').read_text()), events, output

    def test_enter_finishes_and_analyzes_without_benchmark_or_service_operations(self):
        code, meta, events, output = self.run_case()
        self.assertEqual(code, 0)
        self.assertEqual(meta['status'], 'collected')
        self.assertFalse(meta['benchmark_executed_by_script'])
        self.assertFalse(meta['instrumentation_restored'])
        self.assertEqual(events, ['check', 'rotate-before', 'nginx-before', 'metrics-start',
                                  'operator-finish', 'metrics-stop', 'nginx-measurement',
                                  'rotate-measurement', 'nginx-collect', 'slow-collect', 'check',
                                  'analyze-access.sh', 'analyze-slowlog.sh'])
        result = json.loads((output / 'benchmark-result.json').read_text())
        self.assertEqual(result['result'], 'unrecorded')
        self.assertIsNone(result['score'])
        self.assertIsNone(result['started_at_utc'])

    def test_eof_and_interrupt_stop_os_collection_without_finalizing_logs(self):
        for response in ('', 'interrupt'):
            with self.subTest(response=response):
                code, meta, events, _ = self.run_case(response=response)
                self.assertEqual(code, 130)
                self.assertEqual(meta['status'], 'interrupted')
                self.assertTrue(meta['requires_remote_check'])
                self.assertIn('metrics-stop', events)
                self.assertNotIn('rotate-measurement', events)
                self.assertNotIn('restore', events)

    def test_preparation_failure_or_nginx_drift_does_not_start_collectors(self):
        for failure in ('check', 'nginx_changed'):
            code, meta, events, _ = self.run_case(failure=failure)
            self.assertEqual(code, 1)
            self.assertEqual(meta['status'], 'error')
            self.assertNotIn('metrics-start', events)
            self.assertNotIn('operator-finish', events)

    def test_failed_metrics_start_is_cleaned_up(self):
        code, meta, events, _ = self.run_case(failure='metrics-start')
        self.assertEqual(code, 1)
        self.assertIn('metrics-stop', events)
        self.assertNotIn('operator-finish', events)

    def test_failed_metrics_stop_is_not_repeated(self):
        code, meta, events, _ = self.run_case(failure='metrics-stop')
        self.assertEqual(code, 1)
        self.assertEqual(events.count('metrics-stop'), 1)
        self.assertNotIn('rotate-measurement', events)

    def test_transfer_pid_change_and_analysis_failure_are_not_success(self):
        for failure in ('transfer', 'pid_changed', 'analysis'):
            code, meta, events, _ = self.run_case(failure=failure)
            self.assertEqual(code, 1)
            self.assertEqual(meta['status'], 'error')
            self.assertIn('metrics-stop', events)

    def test_no_traffic_collects_logs_but_skips_empty_analysis(self):
        code, meta, events, output = self.run_case(failure='empty-logs')
        self.assertEqual(code, 0)
        self.assertEqual(meta['status'], 'collected')
        self.assertTrue(all(v['status'] == 'skipped' for v in meta['analysis'].values()))
        self.assertNotIn('analyze-access.sh', events)
        self.assertNotIn('analyze-slowlog.sh', events)


if __name__ == '__main__':
    unittest.main()
