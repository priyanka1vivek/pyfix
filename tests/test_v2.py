import ast
import json
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from pyfix.app import app
from pyfix.examples import examples
from pyfix.runner import run_code
from pyfix.repair import repair
from pyfix.training import predict
from pyfix.proposals import candidates

@pytest.mark.parametrize('example',examples(),ids=lambda e:e['id'])
def test_six_repair_examples(example):
    result=repair(example['source'],example['tests'],'artifacts/model.joblib',contract=example['contract'],backend='trusted')
    assert result['status']=='tests_passed', result
    assert result['attempts'][-1]['after']['returncode']==0

@pytest.mark.parametrize('trace',['RecursionError: maximum recursion depth exceeded','SyntaxError: invalid syntax','AssertionError: unexpected result','RuntimeError: server failed'])
def test_unsupported_errors_abstain(trace):
    result=predict(trace,'artifacts/model.joblib')
    assert result['decision']=='needs_review'
    assert result['reasons']

def test_program_splits_and_provenance():
    rows=[json.loads(line) for line in Path('data/dataset.jsonl').read_text().splitlines()]
    assert len({r['program'] for r in rows})==48
    assert {r['split'] for r in rows}=={'train','calibration','validation','test'}
    for row in rows:
        assert row['origin']=='authored_synthetic'
        assert row['source']!=row['clean_source']
    for program in {r['program'] for r in rows}:
        assert len({r['split'] for r in rows if r['program']==program})==1

def test_ast_proposals_are_independent():
    source='def solve(x):\n    return x + 2\n'
    proposals=candidates(source,'type_conversion')
    assert proposals
    assert len({p['source'] for p in proposals})==len(proposals)
    for p in proposals:ast.parse(p['source'])
    assert candidates(source,'type_conversion')==proposals

def test_reports_and_examples_api():
    client=TestClient(app)
    assert len(client.get('/api/examples').json())==6
    assert client.get('/api/metrics').json()['version']==2
    assert client.get('/api/benchmarks').json()['external']['programs']==4
    assert client.get('/api/errors').status_code==200

def test_unsupported_repair_retains_original():
    source='def solve(x):\n    raise RuntimeError("unsupported")\n'
    tests='from candidate import solve\ndef test_one(): assert solve(1)==1\n'
    result=repair(source,tests,'artifacts/model.joblib',contract='Return the input',backend='trusted')
    assert result['status']=='needs_review'
    assert result['attempts']==[]
    assert result['source']==source

@pytest.mark.skipif(os.getenv('PYFIX_TEST_DOCKER')!='1',reason='Docker integration is explicitly enabled in CI')
def test_docker_repair_and_isolation():
    ex=examples()[0]
    result=repair(ex['source'],ex['tests'],'artifacts/model.joblib',contract=ex['contract'],backend='docker')
    assert result['status']=='tests_passed',result
    result=run_code('import os, socket\nassert os.getuid() != 0\ntry:\n open("/work/overwrite", "w")\nexcept OSError:\n pass\nelse:\n raise AssertionError("writable code mount")\ns=socket.socket()\ns.settimeout(1)\nassert s.connect_ex(("1.1.1.1",443)) != 0\nprint("isolated")',backend='docker')
    assert result.passed,result
    assert 'isolated' in result.stdout
