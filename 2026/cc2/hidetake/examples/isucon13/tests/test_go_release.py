import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('release', Path(__file__).parents[1] / 'scripts/lib/go_release_remote.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        app = root / 'app';app.mkdir()
        for name, data in {'main.go': b'package main', 'go.mod': b'module mock', 'go.sum': b'mock'}.items():
            (app / name).write_bytes(data)
        self.original = b'\x7fELF-original'
        self.candidate = b'\x7fELF-candidate'
        (app / 'isupipe').write_bytes(self.original)
        (app / 'isupipe').chmod(0o775)
        unit = root / 'unit';unit.write_bytes(b'WorkingDirectory=mock')
        env = root / 'env';env.write_bytes(b'SECRET=mock-credential\n')
        for key, value in [('APP', app), ('BINARY', app / 'isupipe'), ('UNIT', unit), ('ENV', env), ('BACKUPS', root / 'backups')]:
            p=patch.object(r,key,value);p.start();self.addCleanup(p.stop)
        self.commands = []
        self.service = 'active'
        self.fail_health = False
        p=patch.object(r,'command',self.command);p.start();self.addCleanup(p.stop)
        p=patch.object(r,'health',self.health);p.start();self.addCleanup(p.stop)
        self.payload = dict(binary=base64.b64encode(self.candidate).decode(),
                            binary_sha256=r.digest(self.candidate), source_commit='a'*40,
                            source_manifest=r.source_manifest(), expected_original_sha256=r.digest(self.original))

    def command(self,*args):
        self.commands.append(args)
        if args[1]=='stop':self.service='inactive'
        if args[1]=='start':self.service='active'
        return self.service.encode()

    def health(self,expected):
        self.assertEqual(r.digest(r.BINARY.read_bytes()),expected)
        if self.fail_health and expected==r.digest(self.candidate):raise RuntimeError('mock unhealthy')

    def test_deploy_and_rollback_restore_bytes_mode_mtime(self):
        initial=r.info(r.BINARY)
        r.execute('deploy','test',self.payload)
        self.assertEqual(r.BINARY.read_bytes(),self.candidate)
        self.assertEqual(r.info(r.BINARY),dict(initial,size=len(self.candidate)))
        self.assertNotIn('mock-credential',(r.BACKUPS/'test/state.json').read_text())
        r.execute('rollback','test')
        self.assertEqual(r.BINARY.read_bytes(),self.original)
        self.assertEqual(r.info(r.BINARY),initial)
        self.assertEqual(self.service,'active')

    def test_unhealthy_candidate_can_be_explicitly_rolled_back(self):
        self.fail_health=True
        with self.assertRaises(RuntimeError):r.execute('deploy','test',self.payload)
        self.assertEqual(json.loads((r.BACKUPS/'test/state.json').read_text())['phase'],'starting')
        r.execute('rollback','test')
        self.assertEqual(r.BINARY.read_bytes(),self.original)

    def test_source_drift_refused_before_stop(self):
        (r.APP/'main.go').write_bytes(b'changed')
        with self.assertRaises(RuntimeError):r.execute('deploy','test',self.payload)
        self.assertFalse(self.commands)

    def test_changed_candidate_uses_explicit_live_baseline_and_can_rollback(self):
        self.payload['expected_source_manifest'] = r.source_manifest()
        self.payload['source_manifest'] = dict(self.payload['source_manifest'], **{'main.go': 'b'*64})
        r.execute('deploy', 'changed', self.payload)
        state = json.loads((r.BACKUPS/'changed/state.json').read_text())
        self.assertEqual(state['source_manifest'], r.source_manifest())
        self.assertEqual(state['candidate_source_manifest'], self.payload['source_manifest'])
        r.execute('rollback', 'changed')
        self.assertEqual(r.BINARY.read_bytes(), self.original)

    def test_changed_candidate_still_refuses_live_source_drift(self):
        self.payload['expected_source_manifest'] = r.source_manifest()
        (r.APP/'main.go').write_bytes(b'unexpected drift')
        with self.assertRaises(RuntimeError):r.execute('deploy', 'changed', self.payload)
        self.assertFalse(self.commands)

    def test_configuration_drift_refuses_rollback(self):
        r.execute('deploy','test',self.payload)
        r.UNIT.write_bytes(b'changed')
        before=len(self.commands)
        with self.assertRaises(RuntimeError):r.execute('rollback','test')
        self.assertEqual(len(self.commands),before)

    def test_backup_corruption_refuses_rollback(self):
        r.execute('deploy','test',self.payload)
        (r.BACKUPS/'test/original.isupipe').write_bytes(b'corrupt')
        before=len(self.commands)
        with self.assertRaises(RuntimeError):r.execute('rollback','test')
        self.assertEqual(len(self.commands),before)

    def test_atomic_install_failure_keeps_original(self):
        meta=r.info(r.BINARY)
        with patch.object(r.os,'replace',side_effect=OSError('mock full disk')):
            with self.assertRaises(OSError):r.install(self.candidate,meta)
        self.assertEqual(r.BINARY.read_bytes(),self.original)
        self.assertFalse(list(r.APP.glob('.release-*')))


if __name__=='__main__':unittest.main()
