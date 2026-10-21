"""Local public-example boundary and standalone benchmark tests; no remote access."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]


class ExampleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'target'
        shutil.copytree(REPO / 'scripts', self.repo / 'scripts', ignore=shutil.ignore_patterns('__pycache__'))
        (self.repo / '.git').mkdir()
        (self.repo / 'ansible').mkdir()
        (self.repo / 'ansible/logging-settings.json').write_text('{"baseline_sha256": ""}')
        (self.repo / 'infra/nginx').mkdir(parents=True)
        (self.repo / 'infra/nginx/nginx.conf').write_text('test config')
        binary_dir = self.root / 'bin'
        binary_dir.mkdir()
        ssh = binary_dir / 'ssh'
        ssh.write_text("#!/usr/bin/env python3\nimport json,os,sys\nfrom pathlib import Path\nPath(os.environ['SSH_CALLED']).touch()\nif 'sha256sum' in sys.argv[-1]:print('a'*64+' binary')\nelse:print(json.dumps(dict(pass_result=True)).replace('pass_result','pass'))\n")
        ssh.chmod(0o755)
        self.env = dict(os.environ, PATH=str(binary_dir)+os.pathsep+os.environ['PATH'],
                        SSH_CALLED=str(self.root / 'called'))

    def run_script(self, name, *args):
        return subprocess.run(['bash', str(self.repo / 'scripts' / name), *args],
                              env=self.env, capture_output=True, text=True)

    def test_public_checkout_location_refuses_operation_before_ssh(self):
        (self.repo / '.git').rmdir()
        for name, args in [('measure.sh', ['--run-id', 'm1', '--preparation-id', 'p1']),
                           ('mysql-slowlog.sh', ['--mode', 'prepare', '--run-id', 'p1']),
                           ('nginx-logging.sh', ['--mode', 'enable', '--run-id', 'n1'])]:
            result = self.run_script(name, *args)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Copy this example', result.stderr)
        self.assertFalse((self.root / 'called').exists())
        self.assertFalse((self.root / 'artifacts').exists())

    def test_unconfigured_baseline_refuses_before_ansible_or_artifacts(self):
        result = self.run_script('nginx-logging.sh', '--mode', 'enable', '--run-id', 'n1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ansible/logging-settings.json', result.stderr)
        self.assertFalse((self.root / 'artifacts').exists())

    def test_unconfigured_measurement_and_benchmark_refuse_before_ssh(self):
        for name, args in [('measure.sh', ['--run-id', 'm1', '--preparation-id', 'p1']),
                           ('benchmark.sh', ['--run-id', 'b1']),
                           ('mysql-slowlog.sh', ['--mode', 'prepare', '--run-id', 'p1'])]:
            self.assertNotEqual(self.run_script(name, *args).returncode, 0)
        self.assertFalse((self.root / 'called').exists())
        self.assertFalse((self.root / 'artifacts').exists())

    def test_standalone_benchmark_keeps_results_separate_from_collection(self):
        (self.repo / 'scripts/config.sh').write_text("BENCHMARK_HOST=isucon-benchmark\nBENCHMARK_USER=isucon\nBENCHMARK_BINARY=/example/benchmarker\nBENCHMARK_USERDATA=/example/userdata\nBENCHMARK_TARGET_URL=http://example.invalid\n")
        result = self.run_script('benchmark.sh', '--run-id', 'b1')
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads((self.root / 'artifacts/b1/metadata.json').read_text())
        self.assertTrue(report['benchmark_pass'])
        self.assertEqual(report['mode'], 'benchmark-only')
        self.assertIsNone(report['deployed_revision'])
        self.assertNotEqual(self.run_script('benchmark.sh', '--run-id', 'b1').returncode, 0)


if __name__ == '__main__':
    unittest.main()
