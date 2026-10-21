"""Exercise the real streaming controller/remote lifecycle with local fake tools."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
spec = importlib.util.spec_from_file_location('metrics', SCRIPTS / 'metrics.py')
metrics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metrics)


class MetricsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.install('ssh', '''import os,shlex,sys
argv=shlex.split(sys.argv[-1]);os.execv(argv[0],argv)
''')
        self.install('sudo', '''import os,sys
argv=sys.argv[2:];os.execvp(argv[0],argv)
''')
        self.install('ps', "print('123 1 isucon ruby')\n")
        for name in ('vmstat', 'mpstat', 'pidstat', 'iostat'):
            self.install(name, '''import os,sys,time
from pathlib import Path
name=Path(sys.argv[0]).name
if '-V' in sys.argv:print(name+' test-version');sys.exit(0)
if os.environ.get('FAIL_COLLECTOR')==name:sys.exit(2)
with (Path(os.environ['TEST_PID_DIR'])/name).open('w') as f:f.write(str(os.getpid()))
print(name+' sample',flush=True)
print(name+' diagnostic',file=sys.stderr,flush=True)
while True:time.sleep(1)
''')
        self.env = dict(PATH=str(self.bin) + os.pathsep + os.environ['PATH'], TEST_PID_DIR=str(self.root))

    def install(self, name, source):
        file = self.bin / name
        file.write_text('#!/usr/bin/python3\n' + source)
        file.chmod(0o755)

    def assert_collectors_stopped(self):
        for name in ('vmstat', 'mpstat', 'pidstat', 'iostat'):
            file = self.root / name
            if file.exists():
                with self.assertRaises(ProcessLookupError):
                    os.kill(int(file.read_text()), 0)

    def test_streaming_and_stop_leave_no_collectors(self):
        with patch.dict(os.environ, self.env):
            collector = metrics.Metrics('isucon-target', self.root)
            try:
                collector.start()
            finally:
                success = collector.stop()
        self.assertTrue(success, collector.metadata)
        self.assert_collectors_stopped()
        for name in ('vmstat', 'mpstat', 'pidstat', 'iostat'):
            self.assertIn(name + ' sample', (self.root / 'metrics' / (name + '.stdout.log')).read_text())
            self.assertIn('diagnostic', (self.root / 'metrics' / (name + '.stderr.log')).read_text())
        info = json.loads((self.root / 'metrics/metadata.json').read_text())['info']
        self.assertEqual(info['tracked_pids'], ['123'])
        self.assertEqual(info['commands']['iostat'], ['iostat', '-x', '-y', '-t', 'nvme0n1', '1'])

    def test_failed_collector_stops_remaining_processes(self):
        with patch.dict(os.environ, dict(self.env, FAIL_COLLECTOR='pidstat')):
            collector = metrics.Metrics('isucon-target', self.root)
            try:
                with self.assertRaises(RuntimeError):
                    collector.start()
            finally:
                success = collector.stop()
        self.assertFalse(success)
        self.assertEqual(collector.metadata['status'], 'error')
        self.assert_collectors_stopped()


if __name__ == '__main__':
    unittest.main()
