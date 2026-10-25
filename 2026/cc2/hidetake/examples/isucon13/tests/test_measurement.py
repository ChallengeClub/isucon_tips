import hashlib
import importlib.util
import io
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

LIB=Path(__file__).parents[1]/'scripts/lib'
def load(name):
    spec=importlib.util.spec_from_file_location(name,LIB/(name+'.py'))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
slow=load('slowlog_remote');access=load('analyze_access');sql=load('analyze_slowlog');metrics_worker=load('metrics_remote')
sys.path.insert(0,str(LIB))
measurement=load('measurement')
sys.path.pop(0)


class SlowSessionTests(unittest.TestCase):
    def test_both_databases_are_checked(self):
        with patch.object(slow,'mysql',return_value='isupipe\t0\nisudns\t0\nisudns\t0'):
            slow.check_session_threshold(0)

    def test_missing_dns_connections_are_not_success(self):
        with patch.object(slow,'mysql',return_value='isupipe\t0'):
            with self.assertRaises(RuntimeError):slow.check_session_threshold(0)

    def test_stale_dns_threshold_refused(self):
        with patch.object(slow,'mysql',return_value='isupipe\t0\nisudns\t10'):
            with self.assertRaises(RuntimeError):slow.check_session_threshold(0)

    def test_reconnection_restarts_both_services_and_preserves_zone(self):
        commands=[]
        def fake_run(args,**kwargs):
            commands.append(args)
            return subprocess.CompletedProcess(args,0,b'192.0.2.10\n',b'')
        with patch.object(slow.subprocess,'check_output',return_value=b'zone'),patch.object(slow.subprocess,'run',side_effect=fake_run),patch.object(slow,'check_session_threshold') as threshold:
            slow.restart_and_check(0)
            self.assertIn(['systemctl','restart','isupipe-go'],commands)
            self.assertIn(['systemctl','restart','pdns'],commands)
            threshold.assert_called_once_with(0)

    def test_zone_drift_prevents_ready_status(self):
        def fake_run(args,**kwargs):return subprocess.CompletedProcess(args,0,b'192.0.2.10\n',b'')
        with patch.object(slow.subprocess,'check_output',side_effect=[b'before',b'after']),patch.object(slow.subprocess,'run',side_effect=fake_run):
            with self.assertRaises(RuntimeError):slow.restart_and_check(0)


class AnalysisValidationTests(unittest.TestCase):
    def test_access_rejects_nonfinite_or_boolean_timing(self):
        row=dict(time='2026-10-22T00:00:00Z',method='GET',uri='/api/tag',status=200,body_bytes=3,request_time=0.01,upstream_response_time='0.01')
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'access.log'
            path.write_text(json.dumps(row)+'\n');self.assertEqual(access.validate(path),1)
            for value in [True,float('nan'),-1]:
                row['request_time']=value;path.write_text(json.dumps(row)+'\n')
                with self.assertRaises(ValueError):access.validate(path)

    def test_slowlog_headers_are_counted_without_outputting_sql(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'slow.log';path.write_bytes(b'# Query_time: 0.010  Lock_time: 0.000 Rows_sent: 1 Rows_examined: 1\nSELECT 1;\n')
            digest,count=sql.inspect_log(path)
            self.assertEqual(count,1);self.assertEqual(digest,hashlib.sha256(path.read_bytes()).hexdigest())

    def test_eof_stops_metrics_without_final_rotations(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);target=root/'target';lib=target/'scripts/lib';lib.mkdir(parents=True)
            (root/'artifacts').mkdir();config=target/'infra/measurement';config.mkdir(parents=True)
            (config/'nginx.conf').write_text('main');(config/'nginx-log-format.conf').write_text('format')
            check=dict(app_main_pid=1,middleware_pids={'pdns':2},settings={},nginx_hashes={'nginx.conf':hashlib.sha256(b'main').hexdigest(),'isucon-measurement-log-format.conf':hashlib.sha256(b'format').hexdigest()})
            calls=[];stopped=[]
            def remote(source,args):
                calls.append((source,args));return check if args[1]=='check' else {}
            class FakeMetrics:
                def __init__(self,*args):pass
                def start(self):pass
                def stop(self):stopped.append(True);return True
            with patch.object(measurement,'__file__',str(lib/'measurement.py')),patch.object(measurement,'remote',side_effect=remote),patch.object(measurement,'Metrics',FakeMetrics),patch.object(sys,'argv',['measure','test-eof','prep']),patch.object(sys,'stdin',io.StringIO('')):
                self.assertEqual(measurement.main(),1)
            self.assertTrue(stopped)
            self.assertFalse(any('measurement' in args for _,args in calls))
            state=json.loads((root/'artifacts/test-eof/metadata.json').read_text());self.assertEqual(state['status'],'interrupted-or-failed')


class CollectorShutdownTests(unittest.TestCase):
    def test_stop_closes_descendant_output_pipes(self):
        code="import subprocess,sys,time; subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); print('ready',flush=True); time.sleep(60)"
        with subprocess.Popen([sys.executable,'-u','-c',code],stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True) as process:
            try:
                self.assertEqual(process.stdout.readline(),b'ready\n')
                early,status=metrics_worker.stop_group(process)
                self.assertIsNone(early)
                self.assertEqual(status,-signal.SIGTERM)
                process.communicate(timeout=2)
            finally:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass

    def test_group_is_stopped_even_after_launcher_exits(self):
        code="import subprocess,sys; subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); print('ready',flush=True)"
        with subprocess.Popen([sys.executable,'-u','-c',code],stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True) as process:
            try:
                self.assertEqual(process.stdout.readline(),b'ready\n')
                process.wait(timeout=2)
                early,status=metrics_worker.stop_group(process)
                self.assertEqual(early,0)
                self.assertEqual(status,0)
                process.communicate(timeout=2)
            finally:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass


if __name__=='__main__':unittest.main()
