"""Local tests only: no real SSH, benchmark or nginx signals."""

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
spec = importlib.util.spec_from_file_location('log_remote', SCRIPTS / 'nginx_log_remote.py')
log_remote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(log_remote)


class RemoteLogTests(unittest.TestCase):
    def test_boundaries_preserve_content_and_permissions_and_refuse_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('access.log', 'error.log'):
                (root / name).write_bytes(b'before\n')
                (root / name).chmod(0o640)
            with patch.object(log_remote.subprocess, 'run'), patch.object(log_remote, 'old_files_open', return_value=False):
                log_remote.rotate(root, 'run1', 'before')
                for name in ('access.log', 'error.log'):
                    self.assertEqual((root / 'measurements/run1/before' / name).read_bytes(), b'before\n')
                    self.assertEqual(stat.S_IMODE((root / name).stat().st_mode), 0o640)
                    (root / name).write_bytes(b'measured\n')
                with self.assertRaises(FileExistsError):
                    log_remote.rotate(root, 'run1', 'before')
                log_remote.rotate(root, 'run1', 'measurement')
                for name in ('access.log', 'error.log'):
                    self.assertEqual((root / 'measurements/run1/measurement' / name).read_bytes(), b'measured\n')
                    self.assertEqual((root / name).read_bytes(), b'')

    def test_reopen_timeout_keeps_archived_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('access.log', 'error.log'):
                (root / name).write_bytes(b'keep')
            with patch.object(log_remote.subprocess, 'run'), patch.object(log_remote, 'old_files_open', return_value=True), patch.object(log_remote.time, 'sleep'):
                with self.assertRaises(RuntimeError):
                    log_remote.rotate(root, 'run1', 'before')
            self.assertEqual((root / 'measurements/run1/before/access.log').read_bytes(), b'keep')



if __name__ == "__main__":
    unittest.main()
