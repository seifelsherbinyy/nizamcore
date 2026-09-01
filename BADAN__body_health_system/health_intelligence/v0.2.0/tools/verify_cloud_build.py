#!/usr/bin/env python3
from pathlib import Path
import json, re, sys
root=Path(__file__).resolve().parents[1]
errors=[]
required=[
'00_MANIFEST_CLOUD_FIRST.md','01_RESEARCH_REPORT_AND_BIBLIOGRAPHY.md',
'02_CLOUD_ARCHITECTURE_AND_IMPLEMENTATION_SPEC.md','03_METRIC_DICTIONARY_AND_CALCULATION_SPEC.md',
'04_BEHAVIOR_JOURNAL_STRESS_METHOD.md','05_DAILY_1100_HERMES_AND_CALENDAR_WORKFLOW.md',
'06_VALIDATION_RISKS_AND_ROADMAP.md','07_PROPOSED_SCHEMA_PACKAGE.md',
'08_STORAGE_AUTHORITY_AND_RETRIEVAL_CONTRACT.md','09_HERMES_EXECUTION_PROMPT_100_WORDS.md']
for f in required:
    p=root/f
    if not p.exists(): errors.append(f'missing:{f}')
for f in required[:-1]:
    p=root/f
    if p.exists() and 'v0.2.0' not in p.read_text(errors='ignore'):
        errors.append(f'marker:{f}')
for p in (root/'schemas').glob('*.json'):
    try: json.loads(p.read_text())
    except Exception as e: errors.append(f'json:{p.name}:{e}')
manifest=(root/'00_MANIFEST_CLOUD_FIRST.md').read_text() if (root/'00_MANIFEST_CLOUD_FIRST.md').exists() else ''
for marker in ['OVH VPS','Google Drive `47_NIZAM`','GitHub','Hermes']:
    if marker not in manifest: errors.append('authority:'+marker)
# obvious secret-value patterns, not mentions
pat=re.compile(r'(?i)(api[_-]?key|client[_-]?secret|refresh[_-]?token)\s*[:=]\s*[A-Za-z0-9_\-]{12,}')
for p in root.rglob('*'):
    if p.is_file() and p.suffix in {'.md','.json','.py'} and p.name!='verify_cloud_build.py':
        if pat.search(p.read_text(errors='ignore')): errors.append('possible_secret:'+str(p.relative_to(root)))
if '--tamper-test' in sys.argv:
    errors.append('tamper_probe_detected')
if errors:
    print('VERIFY_FAIL')
    for e in errors: print(e)
    sys.exit(1)
print('VERIFY_PASS')
print(f'docs={len(required)} schemas={len(list((root/"schemas").glob("*.json")))} marker=NIZAM-HEALTH-INTELLIGENCE v0.2.0')
