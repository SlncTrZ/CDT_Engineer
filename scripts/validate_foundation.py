#!/usr/bin/env python3
"""Foundation Validation — reproducible offline CDT_Engineer baseline gate.
Wing: code | Topic: foundation-validation | Updated: 2026-09-12 14:50
"""
from __future__ import annotations
import json,re,subprocess,sys
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]

def run(cmd):
 p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
 if p.returncode:
  print(p.stdout); print(p.stderr,file=sys.stderr); raise SystemExit(p.returncode)
 return p.stdout, p.stderr

def main():
 test_stdout,test_stderr=run([sys.executable,'-m','unittest','discover','-s','tests','-v'])
 schemas=[*ROOT.glob('domains/*/domain.schema.json'),*ROOT.glob('docs/schemas/*.json')]
 for p in schemas: Draft202012Validator.check_schema(json.loads(p.read_text()))
 md=[ROOT/'README.md',ROOT/'AGENTS.md',*ROOT.glob('docs/**/*.md'),*ROOT.glob('domains/**/*.md'),*ROOT.glob('software/**/*.md')]
 pat=re.compile(r'\[[^\]]+\]\(([^)]+)\)'); broken=[]
 for f in md:
  if not f.exists(): continue
  for link in pat.findall(f.read_text()):
   if link.startswith(('http://','https://','#','mailto:')): continue
   rel=link.split('#',1)[0]
   if rel and not (f.parent/rel).resolve().exists(): broken.append([str(f.relative_to(ROOT)),link])
 if broken: raise SystemExit(f'broken markdown links: {broken}')
 run(['git','diff','--check'])
 private_stdout,_=run(['git','ls-files','_private/**'])
 private=private_stdout.strip().splitlines()
 if private: raise SystemExit(f'private files tracked: {private}')
 count=(test_stdout+test_stderr).count(' ... ok')
 print(json.dumps({'result':'PASS','unit_tests':count,'schemas':len(schemas),'markdown_files':len(md),'git_diff_check':'PASS','private_tracked':0},indent=2))

if __name__=='__main__': main()
