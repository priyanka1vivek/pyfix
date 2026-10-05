"""Paired repair ablation plus an independently sourced scope challenge."""
import json
from pathlib import Path
from .catalog import catalog_rows
from .runner import run_code
from .repair import repair
from .training import predict

def oracle(program,argument):
    # Offline dataset construction only. The proposer never sees this implementation.
    namespace={};exec(program.source(),namespace)
    return namespace['solve'](argument)

def unittest_cases(cases):
    body='import unittest\nfrom candidate import solve\nclass TestContract(unittest.TestCase):\n    def test_cases(self):\n'
    return body+''.join(f'        self.assertEqual(solve({argument!r}), {expected!r})\n' for argument,expected in cases)

def repair_benchmark(artifact,output,provider='offline',budget=6):
    records=[]
    for program,split in catalog_rows():
        if split!='test':continue
        args=list(dict.fromkeys(repr(x) for x in program.inputs))
        import ast
        args=[ast.literal_eval(x) for x in args]
        visible=args[:max(1,len(args)//2)];hidden=args[max(1,len(args)//2):]
        if not hidden:
            # A single triggering None input has no independent additional fixture here.
            hidden=[]
        tests=unittest_cases([(x,oracle(program,x)) for x in visible])
        for guided in [False,True]:
            result=repair(program.source(True),tests,artifact,contract=program.contract,backend='trusted',test_framework='unittest',provider=provider,retries=budget,guided=guided)
            heldout=None
            if result['status']=='tests_passed' and hidden:
                heldout=run_code(result['source'],unittest_cases([(x,oracle(program,x)) for x in hidden]),backend='trusted',test_framework='unittest').passed
            records.append(dict(program=program.name,label=program.label,guided=guided,status=result['status'],attempts=len(result['attempts']),seconds=result.get('seconds',0),visible_tests_passed=result['status']=='tests_passed',heldout_tests_passed=heldout,hidden_input_count=len(hidden),prediction=result.get('prediction'),reason=result.get('reason')))
    summary={}
    for guided in [False,True]:
        subset=[r for r in records if r['guided']==guided]
        summary['guided' if guided else 'unguided']=dict(programs=len(subset),visible_passes=sum(r['visible_tests_passed'] for r in subset),heldout_passes=sum(r['heldout_tests_passed'] is True for r in subset),withheld_inputs_available=sum(r['hidden_input_count']>0 for r in subset),attempts=sum(r['attempts'] for r in subset))
    report=dict(provider=provider,budget=budget,summary=summary,records=records,limitations=['Same original programs, provider, tests and attempt budget in each arm.','Offline comparison measures classifier-guided ordering/pruning of hand-written AST rules, not Gemini quality.','Held-out input cases come from the same authored program; they are not independent real-world bugs.','Missing-None examples have no separate hidden triggering input; hidden result is null.','No hypothesis test is justified by this small paired sample.'])
    Path(output).write_text(json.dumps(report,indent=2));return report

def external_benchmark(artifact,output):
    root=Path(__file__).resolve().parent.parent/'benchmarks/quixbugs';records=[]
    for name in ['mergesort','flatten','next_permutation','find_in_sorted']:
        source=(root/'python_programs'/f'{name}.py').read_text()
        cases=[json.loads(line) for line in (root/'json_testcases'/f'{name}.json').read_text().splitlines() if line.strip()]
        for i,(args,expected) in enumerate(cases):
            expression=f'{name}(*{args!r})'
            if name=='flatten':expression=f'list({expression})'
            script=source+f'\nactual = {expression}\nassert actual == {expected!r}, "result mismatch"\n'
            result=run_code(script,backend='trusted',timeout=3)
            diagnosis=None if result.passed else predict(result.stderr,artifact)
            records.append(dict(program=name,case=i,status='passed' if result.passed else 'timeout' if result.timed_out else 'failed',diagnosis=diagnosis))
    failing=[r for r in records if r['status']!='passed']
    report=dict(dataset='QuixBugs',revision='4257f44b0ff1181dedaedee6a447e133219fcebf',source='https://github.com/jkoppel/QuixBugs',programs=4,cases=len(records),failing_cases=len(failing),abstained=sum(r['diagnosis'] is not None and r['diagnosis']['decision']=='needs_review' for r in failing),records=records,interpretation='External algorithmic defects are outside the six mutation labels. This measures rejection behavior, not classification accuracy or production generalisation. Tasks were chosen before scoring to exercise recursion and semantic errors; not a random benchmark sample.')
    Path(output).write_text(json.dumps(report,indent=2));return report
if __name__=='__main__':
    print(json.dumps(repair_benchmark('artifacts/model.joblib','artifacts/repair_benchmark.json')['summary'],indent=2))
    external_benchmark('artifacts/model.joblib','artifacts/external_benchmark.json')
