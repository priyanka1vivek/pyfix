import json
from pathlib import Path
import pytest
from pyfix.runner import run_code
from pyfix.dataset import normalize_traceback, RECIPES
from pyfix.repair import repair, offline_patch
from pyfix.training import predict
from fastapi.testclient import TestClient
from pyfix.app import app

ARTIFACT = Path('artifacts/model.joblib')
SOURCE = 'def add_fee(amount):\n    return amount + 2\n'
TESTS = '''from candidate import add_fee

def test_string():
    assert add_fee('7') == 9

def test_decimal():
    assert add_fee('2.5') == 4.5

def test_number():
    assert add_fee(3) == 5
'''

def test_runner_success_and_error():
    assert run_code('print(3)',backend='trusted').stdout.strip() == '3'
    assert not run_code('1/0',backend='trusted').passed

def test_timeout():
    assert run_code('while True: pass',backend='trusted',timeout=.15).timed_out

def test_tests_are_required_to_pass():
    r = run_code('def f(): return 1','from candidate import f\ndef test_f(): assert f() == 2',backend='trusted')
    assert not r.passed

def test_normalization():
    assert '/secret/path' not in normalize_traceback('File "/secret/path/x.py", line 123')

def test_split_integrity():
    rows = [json.loads(x) for x in Path('data/dataset.jsonl').read_text().splitlines()]
    for a,b in [('train','test'),('train','validation'),('validation','test')]:
        left,right = ([r for r in rows if r['split']==s] for s in [a,b])
        assert not {r['family'] for r in left} & {r['family'] for r in right}
        assert not {r['traceback'] for r in left} & {r['traceback'] for r in right}
    assert {r['label'] for r in rows} == set(RECIPES)

def test_offline_repair_is_test_verified():
    r = repair(SOURCE,TESTS,ARTIFACT,contract='Numeric strings and numbers plus 2',backend='trusted')
    assert r['status'] == 'tests_passed'
    assert 'float' in r['source']
    assert r['diff']

def test_bad_patch_not_accepted():
    r = repair(SOURCE,TESTS,ARTIFACT,contract='Numeric strings and numbers plus 2',backend='trusted',proposer=lambda *args:'def add_fee(amount): return 9\n')
    assert r['status'] == 'needs_review'
    assert r['source'] == SOURCE
    assert len(r['attempts']) == 2

def test_syntax_error_patch_rejected():
    r = repair(SOURCE,TESTS,ARTIFACT,contract='Add 2',backend='trusted',proposer=lambda *args:'def broken(')
    assert r['status'] == 'needs_review'

def test_already_passing():
    fixed = offline_patch(SOURCE,'','type_conversion','')
    assert repair(fixed,TESTS,ARTIFACT,contract='Add 2',backend='trusted')['status'] == 'already_passing'

def test_no_tests_rejected():
    with pytest.raises(ValueError): repair(SOURCE,'pass',ARTIFACT,contract='Add 2',backend='trusted')

def test_api(monkeypatch):
    monkeypatch.setenv('PYFIX_RUNNER','trusted')
    client = TestClient(app)
    assert client.get('/').status_code == 200
    assert client.get('/api/metrics').json()['selected_model']
    assert client.post('/api/repair',json={'source':SOURCE,'tests':TESTS,'contract':'Numeric strings plus 2'}).json()['status'] == 'tests_passed'
    assert client.post('/api/repair',json={},headers={'origin':'https://attacker.invalid'}).status_code == 403
    assert client.post('/api/classify',json={'traceback':'TypeError: can only concatenate str (not "int") to str'}).status_code == 200
    assert client.post('/api/repair',json={}).status_code == 422
