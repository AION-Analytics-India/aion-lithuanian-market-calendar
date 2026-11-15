"""Test published-form archives in distinct disposable environments outside source."""
import hashlib, json, os, platform, subprocess, sys, tarfile, tempfile, venv
from pathlib import Path
def run(argv,wd,env): subprocess.run(list(map(str,argv)),cwd=wd,env=env,check=True)
def main():
    dist=Path(sys.argv[1]).resolve()
    fs=[*dist.glob('*.whl'),*dist.glob('*.tar.gz')]
    expected={Path(name).name:h for h,name in (line.split() for line in (dist.parent/'BUILD_SHA256.txt').read_text().splitlines())}
    assert {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in fs}==expected, 'Artifact identity differs from build job'
    assert len(fs)==2
    print('runtime',platform.platform(),platform.machine(),sys.version,flush=True)
    with tempfile.TemporaryDirectory() as name:
        wd=Path(name)
        with tarfile.open(fs[1]) as tar:
            for item in tar:
                parts=Path(item.name).parts
                if len(parts)>2 and parts[1]=='tests' and parts[-1].endswith('.py') and item.isfile() and '..' not in parts:
                    p=wd.joinpath(*parts[1:]);p.parent.mkdir(exist_ok=True,parents=True)
                    p.write_bytes(tar.extractfile(item).read())
        assert len(list((wd/'tests').glob('test_*.py')))>=7
        for index,artifact in enumerate(fs):
            print(artifact.name, hashlib.sha256(artifact.read_bytes()).hexdigest(),flush=True)
            d=wd/str(index);venv.create(d,with_pip=True)
            py=d/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
            env={**os.environ,'AION_LT_CALENDAR_OFFLINE':'1','AION_LT_CALENDAR_CACHE':str(d/'calendar-cache')};env.pop('PYTHONPATH',None)
            run([py,'-m','pip','install',artifact,'pytest'],wd,env)
            run([py,'-I','-c','from pathlib import Path;import sys,aion_lithuanian_market_calendar as m;assert Path(m.__file__).resolve().is_relative_to(Path(sys.prefix).resolve());assert m.__version__=="1.3.0"'],wd,env)
            run([py,'-I','-m','pytest','-q',wd/'tests'],wd,env)
if __name__=='__main__': main()
