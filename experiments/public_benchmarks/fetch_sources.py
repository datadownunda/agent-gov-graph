"""Download exactly the public source revisions recorded in sources.lock.json."""
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parent

def run(*args):subprocess.run(args,check=True)

if __name__=='__main__':
    for source in json.loads((ROOT/'sources.lock.json').read_text()):
        dest=ROOT/'upstream'/source['name']
        if not dest.exists():
            dest.mkdir(parents=True)
            run('git','init',str(dest))
            run('git','-C',str(dest),'remote','add','origin',source['url'])
            run('git','-C',str(dest),'fetch','--depth','1','origin',source['commit'])
            run('git','-C',str(dest),'checkout','--detach','FETCH_HEAD')
        actual=subprocess.check_output(['git','-C',str(dest),'rev-parse','HEAD'],text=True).strip()
        if actual!=source['commit']:raise SystemExit(f'Revision mismatch in {dest}; use a clean directory')
    traces=list((ROOT/'upstream/modus-trajectories').rglob('trajectory.json.gz'))
    if len(traces)!=5850 or any(p.open('rb').read(2)!=b'\x1f\x8b' for p in traces):
        raise SystemExit('Modus large files are incomplete. Install Git LFS and run git lfs pull in its repository.')
    print('Pinned public sources available. No model credentials used.')
