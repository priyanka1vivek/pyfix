"""Seeded mutations with clean-source provenance and program-family splits."""
import hashlib
import json
import random
import re
from pathlib import Path
from .runner import run_code

# Each recipe is (working expression, injected expression, invocation).
RECIPES = {
    "type_conversion": [("int(x) + 2", "x + 2", "'7'"), ("float(x) * 2", "x / 2", "'8'"), ("int(x) - 1", "x - 1", "'9'"), ("int(x) ** 2", "x ** 2", "'4'"), ("10 / int(x)", "10 / x", "'5'"), ("int(x) // 2", "x // 2", "'6'")],
    "missing_none_guard": [("len(x or [])", "len(x)", "None"), ("(x or '').strip()", "x.strip()", "None"), ("(x or {}).get('a')", "x.get('a')", "None"), ("sum(x or [])", "sum(x)", "None"), ("(x or [0])[0]", "x[0]", "None"), ("(x or '').lower()", "x.lower()", "None")],
    "index_boundary": [("x[len(x)-1]", "x[len(x)]", "[1,2,3]"), ("x[0]", "x[len(x)+1]", "[4,5]"), ("x[-1]", "x[-len(x)-1]", "[7,8]"), ("x[1:][0]", "x[1:][len(x)]", "[3,4,5]"), ("x[0]", "x[99]", "'hello'"), ("x[-1]", "x[20]", "(2,3)")],
    "missing_mapping_key": [("x.get('cost',0)", "x['cost']", "{'price':4}"), ("x.get('name','')", "x['name']", "{'title':'book'}"), ("x.get('total',0)", "x['total']", "{'sum':2}"), ("x.get('id',0)", "x['id']", "{'code':3}"), ("x.get('score',0)", "x['score']", "{'grade':5}"), ("x.get('value',0)", "x['value']", "{'result':6}")],
    "zero_denominator": [("10 / (x or 1)", "10 / x", "0"), ("8 // (x or 1)", "8 // x", "0"), ("7 % (x or 1)", "7 % x", "0"), ("float(6) / (x or 1)", "float(6) / x", "0"), ("sum([2,3]) / (x or 1)", "sum([2,3]) / x", "0"), ("(9-3) / (x or 1)", "(9-3) / x", "0")],
    "wrong_argument_count": [("max(x, 2)", "max()", "4"), ("len([x])", "len()", "3"), ("abs(x)", "abs(x, 1)", "-2"), ("pow(x,2)", "pow(x)", "3"), ("round(x,1)", "round()", "2.4"), ("divmod(x,2)", "divmod(x)", "5")],
}

def normalize_traceback(text):
    text = re.sub(r'File "[^"]+", line \d+', 'File "candidate.py", line N', text)
    text = re.sub(r'0x[0-9a-fA-F]+', '0xADDR', text)
    return text.strip()

def build_dataset(destination, variants=12, seed=42):
    rng = random.Random(seed)
    rows = []
    for label, recipes in RECIPES.items():
        for family, (good, bad, argument) in enumerate(recipes):
            for variant in range(variants):
                variable = rng.choice(["value", "item", "data", "entry", "payload", "number"])
                name = rng.choice(["process", "calculate", "transform", "evaluate"])
                def source(expression):
                    expression = re.sub(r'\bx\b', variable, expression)
                    padding = '\n' * (variant % 3)
                    return f"{padding}def {name}({variable}):\n    return {expression}\n\nprint({name}({argument}))\n"
                clean, broken = source(good), source(bad)
                healthy = run_code(clean, backend="trusted")
                failed = run_code(broken, backend="trusted")
                if not healthy.passed or failed.passed or failed.timed_out:
                    raise RuntimeError(f"Invalid mutation {label}/{family}")
                trace = normalize_traceback(failed.stderr)
                rows.append(dict(id=hashlib.sha256(broken.encode()).hexdigest()[:16], label=label, family=f"{label}:{family}", split="train" if family < 4 else "validation" if family == 4 else "test", source=broken, clean_source=clean, traceback=trace, exception=trace.splitlines()[-1].split(':')[0], seed=seed))
    # Exact duplicate sources never inflate sample size.
    rows = list({row['id']: row for row in rows}.values())
    path = Path(destination); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(row)+'\n' for row in rows), encoding="utf-8")
    return rows
