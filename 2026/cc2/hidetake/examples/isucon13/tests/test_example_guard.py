import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ExampleGuardTests(unittest.TestCase):
    def test_public_example_refuses_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            repository = Path(temp)
            subprocess.run(['git', 'init', '--quiet', str(repository)], check=True)
            example = repository/'examples/isucon13'
            (example/'scripts/lib').mkdir(parents=True)
            shutil.copy2(ROOT/'scripts/benchmark.sh', example/'scripts/benchmark.sh')
            shutil.copy2(ROOT/'scripts/lib/example-guard.sh', example/'scripts/lib/example-guard.sh')
            result = subprocess.run(['bash', str(example/'scripts/benchmark.sh')], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Reference only', result.stderr)

    def test_private_copy_requires_review_before_ssh(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root/'target'
            (target/'scripts/lib').mkdir(parents=True)
            shutil.copy2(ROOT/'scripts/benchmark.sh', target/'scripts/benchmark.sh')
            shutil.copy2(ROOT/'scripts/lib/example-guard.sh', target/'scripts/lib/example-guard.sh')
            (target/'example-review.json').write_text(json.dumps({'reviewed_for_target': False}))
            subprocess.run(['git', 'init', '--quiet', str(target)], check=True)
            bin_dir = root/'bin'
            bin_dir.mkdir()
            marker = root/'ssh-called'
            spy = bin_dir/'ssh'
            spy.write_text('#!/bin/sh\ntouch "$GUARD_TEST_MARKER"\nexit 99\n')
            spy.chmod(0o755)
            env = dict(os.environ, PATH=str(bin_dir)+os.pathsep+os.environ['PATH'], GUARD_TEST_MARKER=str(marker))
            result = subprocess.run(['bash', str(target/'scripts/benchmark.sh'), 'guard-test'], env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Review ADAPTATION.md', result.stderr)
            self.assertFalse(marker.exists())
