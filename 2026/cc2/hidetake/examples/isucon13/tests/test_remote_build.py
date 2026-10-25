import base64
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('worker', Path(__file__).parents[1] / 'scripts/lib/build_go_remote_worker.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


class RemoteBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        app=self.root/'app';app.mkdir()
        files={'main.go':b'package main', 'go.mod':b'module mock', 'go.sum':b'mock'}
        for name,data in files.items():(app/name).write_bytes(data)
        self.original=b'\x7fELF-original';(app/'isupipe').write_bytes(self.original)
        self.request=dict(id='remote-test',source_commit='a'*40,expected_original_sha256=w.digest(self.original),
                          files={n:base64.b64encode(d).decode() for n,d in files.items()},
                          source_manifest={n:w.digest(d) for n,d in files.items()})
        for key,value in [('ROOT',self.root/'builds'),('APP',app)]:
            p=patch.object(w,key,value);p.start();self.addCleanup(p.stop)
        self.compile_code=0;self.pid=123;self.mutate_live=False;self.commands=[]
        p=patch.object(w.subprocess,'run',self.fake_command);p.start();self.addCleanup(p.stop)

    def fake_command(self,args,**kwargs):
        self.commands.append((args,kwargs))
        if args[0]=='systemctl':return subprocess.CompletedProcess(args,0,str(self.pid).encode(),b'')
        if args[1]=='version':
            output=b'go version go1.21.2 linux/amd64\n' if len(args)==2 else b'mock build info\n'
            return subprocess.CompletedProcess(args,0,output,b'')
        self.assertEqual(args[1],'build')
        env=kwargs['env'];self.assertEqual(env['GOPROXY'],'off');self.assertNotIn('SECRET',env)
        if self.compile_code==0:Path(args[args.index('-o')+1]).write_bytes(b'\x7fELF-built')
        if self.mutate_live:self.pid+=1
        return subprocess.CompletedProcess(args,self.compile_code)

    def test_success_preserves_live_binary_and_returns_deploy_contract(self):
        original_meta=(w.APP/'isupipe').stat()
        w.build(self.request)
        folder=w.ROOT/'remote-test';meta=json.loads((folder/'build.json').read_text())
        self.assertEqual((w.APP/'isupipe').read_bytes(),self.original)
        self.assertEqual((w.APP/'isupipe').stat().st_mtime_ns,original_meta.st_mtime_ns)
        self.assertEqual(meta['source_commit'],self.request['source_commit'])
        self.assertEqual(meta['source_manifest'],self.request['source_manifest'])
        self.assertEqual(meta['binary_sha256'],w.digest((folder/'isupipe').read_bytes()))
        self.assertEqual(meta['expected_original_sha256'],w.digest(self.original))
        self.assertEqual(meta['build_location'],'remote')
        self.assertEqual(json.loads((folder/'state.json').read_text())['phase'],'built')
        self.assertTrue(all(args[:2]==['systemctl','show'] for args,_ in self.commands if args[0]=='systemctl'))

    def test_source_drift_stops_before_remote_writes(self):
        (w.APP/'main.go').write_bytes(b'changed')
        with self.assertRaises(RuntimeError):w.build(self.request)
        self.assertFalse(w.ROOT.exists())

    def test_changed_candidate_build_preserves_live_sources(self):
        self.request['expected_source_manifest'] = w.source_manifest()
        changed = b'package main // candidate'
        self.request['files']['main.go'] = base64.b64encode(changed).decode()
        self.request['source_manifest']['main.go'] = w.digest(changed)
        w.build(self.request)
        meta = json.loads((w.ROOT/'remote-test/build.json').read_text())
        self.assertEqual(meta['expected_source_manifest'], w.source_manifest())
        self.assertEqual((w.APP/'main.go').read_bytes(), b'package main')
        self.assertEqual((w.ROOT/'remote-test/source/main.go').read_bytes(), changed)

    def test_bad_payload_and_traversal_refused(self):
        self.request['files']['../env.sh']=base64.b64encode(b'secret').decode()
        with self.assertRaises(ValueError):w.build(self.request)
        self.assertFalse(w.ROOT.exists())

    def test_digest_mismatch_refused_before_writes(self):
        self.request['files']['main.go']=base64.b64encode(b'changed').decode()
        with self.assertRaises(ValueError):w.build(self.request)
        self.assertFalse(w.ROOT.exists())

    def test_compile_failure_keeps_original_and_no_deploy_metadata(self):
        self.compile_code=1
        with self.assertRaises(RuntimeError):w.build(self.request)
        folder=w.ROOT/'remote-test'
        self.assertEqual(json.loads((folder/'state.json').read_text())['phase'],'build-failed')
        self.assertFalse((folder/'build.json').exists())
        self.assertEqual((w.APP/'isupipe').read_bytes(),self.original)

    def test_restart_during_build_refuses_result(self):
        self.mutate_live=True
        with self.assertRaises(RuntimeError):w.build(self.request)
        self.assertFalse((w.ROOT/'remote-test/build.json').exists())

    def test_existing_build_id_is_not_overwritten(self):
        w.build(self.request)
        saved=(w.ROOT/'remote-test/build.json').read_bytes()
        with self.assertRaises(FileExistsError):w.build(self.request)
        self.assertEqual((w.ROOT/'remote-test/build.json').read_bytes(),saved)


if __name__=='__main__':unittest.main()
