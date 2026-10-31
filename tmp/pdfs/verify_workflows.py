import subprocess, tempfile, os, json
from pathlib import Path

git='/Users/yueyan_liu/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback/git'
base=Path(tempfile.mkdtemp(prefix='github-doc-check-',dir='/private/tmp'))
env=dict(os.environ,GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_EDITOR='true',GIT_TERMINAL_PROMPT='0')
def run(cwd,*args,ok=True):
    p=subprocess.run([git,*args],cwd=cwd,env=env,text=True,capture_output=True)
    if ok and p.returncode: raise AssertionError((args,p.stdout,p.stderr))
    return p
def identity(p):
    run(p,'config','user.name','Tutorial Check')
    run(p,'config','user.email','check@example.com')

origin=base/'origin.git';a=base/'a';b=base/'b';a.mkdir()
run(base,'init','--bare','--initial-branch=main',str(origin))
run(a,'init','-b','main');identity(a)
(a/'README.md').write_text('Run with Python 3.10.\n')
run(a,'add','README.md');run(a,'commit','-m','Initial project structure')
run(a,'remote','add','origin',str(origin));run(a,'push','-u','origin','main')
run(base,'clone',str(origin),str(b));identity(b)
run(a,'switch','-c','docs/usage')
(a/'README.md').write_text('Run with Python 3.11.\n')
run(a,'add','README.md');run(a,'commit','-m','docs: explain quick start')
run(a,'push','-u','origin','docs/usage')
(b/'README.md').write_text('Run with Python 3.12.\n')
run(b,'add','README.md');run(b,'commit','-m','Update environment');run(b,'push')
run(a,'fetch','origin')
conflict=run(a,'merge','origin/main',ok=False)
assert conflict.returncode!=0 and '<<<<<<< HEAD' in (a/'README.md').read_text()
(a/'README.md').write_text('Run with Python 3.12.\n')
run(a,'add','README.md');run(a,'commit','-m','Merge main and resolve README conflict');run(a,'push')
run(b,'fetch','origin');run(b,'merge','origin/docs/usage');run(b,'push')
run(a,'switch','main');run(a,'pull','--ff-only');run(a,'branch','-d','docs/usage')

run(a,'switch','-c','practice/undo')
original=(a/'README.md').read_text()
(a/'README.md').write_text(original+'temporary\n')
run(a,'add','README.md');run(a,'restore','--staged','README.md')
assert run(a,'diff','--cached').stdout=='' and 'temporary' in run(a,'diff').stdout
run(a,'restore','README.md');assert (a/'README.md').read_text()==original
(a/'README.md').write_text(original+'bad line\n')
run(a,'add','README.md');run(a,'commit','-m','Bad practice line')
bad=run(a,'rev-parse','HEAD').stdout.strip()
run(a,'revert','--no-edit',bad);assert (a/'README.md').read_text()==original
(a/'README.md').write_text(original+'keep change\n')
run(a,'add','README.md');run(a,'commit','-m','Local only change')
run(a,'reset','--soft','HEAD~1')
assert 'keep change' in run(a,'diff','--cached').stdout
run(a,'commit','-m','Local only change retained')
(a/'draft.txt').write_text('untracked work')
run(a,'stash','push','-u','-m','WIP before switching tasks')
assert not (a/'draft.txt').exists()
run(a,'stash','apply','stash@{0}');assert (a/'draft.txt').read_text()=='untracked work'
run(a,'stash','drop','stash@{0}')
assert bad in run(a,'reflog','--format=%H').stdout
run(a,'branch','rescue/recovered',bad)
assert run(a,'rev-parse','rescue/recovered').stdout.strip()==bad
print(json.dumps({'passed':['init and push','clone and tracking','feature branch','conflict resolution',
                            'merge and fast-forward pull','safe branch deletion','unstage without losing edits',
                            'restore unstaged edits','revert shared-style commit','soft reset retains staged work',
                            'stash includes untracked files','reflog rescue branch'],
                  'test_repository':str(base)},ensure_ascii=False,indent=2))
