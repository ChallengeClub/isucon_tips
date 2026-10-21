"""Local-only JSON schema, analysis and Ansible entry-point checks."""

import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('analyze_access', REPO / 'scripts/analyze_access.py')
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


class LoggingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'target'
        for name in ['scripts', 'infra', 'ansible']:
            shutil.copytree(REPO / name, self.repo / name, ignore=shutil.ignore_patterns('__pycache__'))
        (self.repo / '.git').mkdir()
        (self.repo / 'ansible/logging-settings.json').write_text(json.dumps({'baseline_sha256': 'a' * 64}))
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ['PATH'])

    def row(self, uri='/posts/123'):
        return dict(time='2026-10-21T00:00:00+00:00', method='GET', uri=uri, status=200,
                    body_bytes=123, request_time=0.123, upstream_response_time='0.120')

    def log(self, data):
        path = self.root / 'artifacts/run1/logs/nginx-access.log'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data)
        return path

    def command(self, script, *args):
        return subprocess.run(['bash', str(self.repo / 'scripts' / script), *args],
                              env=self.env, capture_output=True, text=True)

    def mock_alp(self):
        alp = self.bin / 'alp'
        alp.write_text('''#!/usr/bin/env python3
import sys
if '--version' in sys.argv:print('alp version 1.0.22')
else:
 assert sys.argv[1]=='json'
 assert sys.argv[sys.argv.index('--restime-key')+1]=='request_time'
 assert sys.argv[sys.argv.index('--sort')+1]=='sum' and '--reverse' in sys.argv
 print('COUNT\\tMETHOD\\tURI\\tSUM\\tAVG\\tP95\\tMAX')
 print('1\\tGET\\t/posts/[0-9]+\\t0.123\\t0.123\\t0.123\\t0.123')
''')
        alp.chmod(0o755)

    def test_format_is_valid_json_with_escaped_uri_and_no_upstream(self):
        source = (REPO / 'infra/nginx/isucon-json-log.conf').read_text()
        template = ''.join(re.findall(r"'([^']*)'", source))
        values = dict(time_iso8601='2026-10-21T00:00:00+00:00', request_method='GET',
                      uri='/posts/"quoted', status=200, body_bytes_sent=12,
                      request_time=0.1, upstream_response_time='-')
        rendered = re.sub(r'\$([a-z0-9_]+)', lambda m: json.dumps(values[m[1]])[1:-1]
                          if isinstance(values[m[1]], str) else str(values[m[1]]), template)
        row = json.loads(rendered)
        self.assertEqual(row['uri'], '/posts/"quoted')
        self.assertEqual(row['upstream_response_time'], '-')
        self.assertNotIn('$request_uri', source)

    def test_validation_rejects_old_format_and_invalid_timings(self):
        for data in ['combined log\n', '', json.dumps(dict(self.row(), request_time=-1)) + '\n',
                     json.dumps(dict(self.row(), request_time='0.1')) + '\n']:
            with self.subTest(data=data), self.assertRaises(ValueError):
                analysis.validate(self.log(data))

    def test_route_groups_match_only_dynamic_routes(self):
        patterns = [re.compile(p) for p in analysis.GROUPS.split(',')]
        for uri in ['/posts/123', '/image/123.jpg', '/@example']:
            self.assertTrue(any(p.match(uri) for p in patterns))
        for uri in ['/posts', '/posts/123/edit', '/admin/banned', '/login']:
            self.assertFalse(any(p.match(uri) for p in patterns))

    def test_analysis_saves_report_version_and_input_identity(self):
        self.mock_alp()
        self.log(json.dumps(self.row()) + '\n')
        result = self.command('analyze-access.sh', '--run-id', 'run1')
        self.assertEqual(result.returncode, 0, result.stderr)
        directory = self.root / 'artifacts/run1/analysis'
        metadata = json.loads((directory / 'metadata.json').read_text())
        self.assertEqual(metadata['input_lines'], 1)
        self.assertEqual(metadata['status'], 'passed')
        self.assertIn('1.0.22', metadata['alp_version'])
        self.assertTrue((directory / 'alp.txt').exists())
        again = self.command('analyze-access.sh', '--run-id', 'run1')
        self.assertNotEqual(again.returncode, 0)

    def test_analysis_failure_preserves_partial_report(self):
        self.mock_alp()
        path = self.bin / 'alp'
        path.write_text(path.read_text() + '\nif "--version" not in sys.argv:sys.exit(1)\n')
        self.log(json.dumps(self.row()) + '\n')
        result = self.command('analyze-access.sh', '--run-id', 'run1')
        self.assertNotEqual(result.returncode, 0)
        directory = self.root / 'artifacts/run1/analysis'
        self.assertEqual(json.loads((directory / 'metadata.json').read_text())['status'], 'failed')
        self.assertTrue((directory / 'alp.txt.partial').exists())
        self.assertFalse((directory / 'alp.txt').exists())

    def test_enable_and_restore_pass_explicit_variables(self):
        mock = self.bin / 'ansible-playbook'
        mock.write_text('''#!/usr/bin/env python3
import json,pathlib,sys
v=json.loads(pathlib.Path(sys.argv[-1][1:]).read_text())
assert len(v['baseline_sha256'])==64
assert pathlib.Path(v['format_path']).exists()
assert v['logging_mode'] in ['enable','restore']
if v['logging_mode']=='restore':assert v['backup_id']=='enable1'
print('mock passed')
''')
        mock.chmod(0o755)
        for mode, run, extra in [('enable', 'enable1', []), ('restore', 'restore1', ['--backup-id', 'enable1'])]:
            result = self.command('nginx-logging.sh', '--mode', mode, '--run-id', run, *extra)
            self.assertEqual(result.returncode, 0, result.stderr)
            meta = json.loads((self.root / 'artifacts' / run / 'metadata.json').read_text())
            self.assertEqual(meta['status'], 'passed')
        result = self.command('nginx-logging.sh', '--mode', 'restore', '--run-id', 'invalid')
        self.assertNotEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()
