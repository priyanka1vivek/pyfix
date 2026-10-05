"""Program-disjoint synthetic corpus with executable mutation provenance."""
import hashlib
import json
import re
from pathlib import Path
from .catalog import catalog_rows, PROGRAMS
from .runner import run_code
RECIPES = {program.label: [] for program in PROGRAMS}  # label compatibility for v1 notebooks

def normalize_traceback(text):
    text = re.sub(r'File "[^"]+", line \d+', 'File "candidate.py", line N', text)
    text = re.sub(r'0x[0-9a-fA-F]+', '0xADDR', text)
    text = re.sub(r'^\s*[~^]+\s*$', '', text, flags=re.M)
    return text.strip()

def exception_name(text):
    matches = re.findall(r'\b([A-Za-z]+(?:Error|Exception))(?::|\b)', text)
    return matches[-1] if matches else 'Unknown'

def build_dataset(destination, variants=8, seed=42):
    if variants < 1: raise ValueError('variants must be positive')
    rows = []
    for program, split in catalog_rows():
        seen = set()
        for argument in program.inputs[:variants]:
            if repr(argument) in seen: continue
            seen.add(repr(argument))
            call = f'\nprint(solve({argument!r}))\n'
            clean, broken = program.source(), program.source(True)
            healthy = run_code(clean+call, backend='trusted')
            failed = run_code(broken+call, backend='trusted')
            if not healthy.passed or failed.passed or failed.timed_out:
                raise RuntimeError(f'Invalid mutation: {program.name}: {failed.stderr}')
            trace = normalize_traceback(failed.stderr)
            identity = hashlib.sha256((program.name+repr(argument)).encode()).hexdigest()[:16]
            rows.append(dict(id=identity,label=program.label,program=program.name,family=program.name,split=split,source=broken,clean_source=clean,input=argument,contract=program.contract,traceback=trace,exception=exception_name(trace),seed=seed,origin='authored_synthetic',mutation={'before':program.good,'after':program.bad}))
    path=Path(destination);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(''.join(json.dumps(row)+'\n' for row in rows),encoding='utf-8')
    return rows
