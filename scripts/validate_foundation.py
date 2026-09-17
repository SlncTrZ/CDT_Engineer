#!/usr/bin/env python3
"""Foundation Validation — reproducible offline CDT_Engineer baseline gate.
Wing: code | Topic: foundation-validation | Updated: 2026-09-12 20:42
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
 schemas=[*ROOT.glob('domains/*/domain.schema.json'),*ROOT.glob('docs/schemas/*.json'),*ROOT.glob('catalogs/schemas/*.json')]
 for p in schemas: Draft202012Validator.check_schema(json.loads(p.read_text(encoding='utf-8')))
 profile_schema=json.loads((ROOT/'docs/schemas/agent-profile.schema.json').read_text(encoding='utf-8'))
 profile_validator=Draft202012Validator(profile_schema)
 profiles=list(ROOT.glob('domains/*/agent-profile.json'))
 for p in profiles:
  errors=list(profile_validator.iter_errors(json.loads(p.read_text(encoding='utf-8'))))
  if errors: raise SystemExit(f'invalid agent profile {p.relative_to(ROOT)}: {[e.message for e in errors]}')
 catalog_schema=json.loads((ROOT/'catalogs/schemas/engineering-asset-catalog.schema.json').read_text(encoding='utf-8'))
 catalog_validator=Draft202012Validator(catalog_schema)
 catalogs=list(ROOT.glob('catalogs/*/catalog.json'))
 for p in catalogs:
  errors=list(catalog_validator.iter_errors(json.loads(p.read_text(encoding='utf-8'))))
  if errors: raise SystemExit(f'invalid engineering asset catalog {p.relative_to(ROOT)}: {[e.message for e in errors]}')
 md=[ROOT/'README.md',ROOT/'AGENTS.md',ROOT/'MCP_PROVIDER_STANDARD.md',*ROOT.glob('docs/**/*.md'),*ROOT.glob('domains/**/*.md'),*ROOT.glob('software/**/*.md'),*ROOT.glob('catalogs/**/*.md')]
 class_pat=re.compile(r'^> Documentation class: (PUBLIC_[A-Z_]+)$',re.MULTILINE)
 missing_class=[]
 for f in md:
  if not f.exists(): continue
  head='\n'.join(f.read_text(encoding='utf-8').splitlines()[:12])
  if not class_pat.search(head): missing_class.append(str(f.relative_to(ROOT)))
 if missing_class: raise SystemExit(f'public markdown missing documentation class: {missing_class}')
 pat=re.compile(r'\[[^\]]+\]\(([^)]+)\)'); broken=[]
 root_resolved=ROOT.resolve()
 for f in md:
  if not f.exists(): continue
  for link in pat.findall(f.read_text(encoding='utf-8')):
   if link.startswith(('http://','https://','#','mailto:')): continue
   rel=link.split('#',1)[0]
   if not rel: continue
   target=(f.parent/rel).resolve()
   try:
    public_rel=target.relative_to(root_resolved)
   except ValueError:
    broken.append([str(f.relative_to(ROOT)),link,'target escapes public repository'])
    continue
   if '_private' in public_rel.parts:
    broken.append([str(f.relative_to(ROOT)),link,'public document depends on _private'])
   elif not target.exists():
    broken.append([str(f.relative_to(ROOT)),link,'target missing'])
 if broken: raise SystemExit(f'broken markdown links: {broken}')
 run(['git','diff','--check'])
 private_stdout,_=run(['git','ls-files','_private/**'])
 private=private_stdout.strip().splitlines()
 if private: raise SystemExit(f'private files tracked: {private}')
 count=(test_stdout+test_stderr).count(' ... ok')
 print(json.dumps({'result':'PASS','unit_tests':count,'schemas':len(schemas),'profiles':len(profiles),'catalogs':len(catalogs),'markdown_files':len(md),'documentation_classes':'PASS','git_diff_check':'PASS','private_tracked':0},indent=2))

if __name__=='__main__': main()
