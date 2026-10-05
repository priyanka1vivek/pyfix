"""Offline verification of the core, without pytest/FastAPI dependencies.
Run from repository root: python -m unittest discover -s tests -p stdlib_checks.py -v
The separate pytest suite checks the default pytest path and HTTP API.
"""
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from pyfix.runner import run_code
from pyfix.repair import repair
from pyfix.dataset import RECIPES

SOURCE = 'def add_fee(amount):\n    return amount + 2\n'
TESTS = '''import unittest
from candidate import add_fee
class TestFee(unittest.TestCase):
    def test_numeric(self):
        self.assertEqual(add_fee('7'),9)
        self.assertEqual(add_fee('2.5'),4.5)
        self.assertEqual(add_fee(3),5)
        self.assertEqual(add_fee('-4'),-2)
        with self.assertRaises(ValueError): add_fee('bad')
'''
class CoreChecks(unittest.TestCase):
    def fix(self, **kwargs):
        return repair(SOURCE,TESTS,'artifacts/model.joblib',contract='Numbers or numeric strings plus 2, preserve decimals',backend='trusted',test_framework='unittest',**kwargs)
    def test_execution(self):
        self.assertEqual(run_code('print(3)',backend='trusted').stdout.strip(),'3')
        self.assertFalse(run_code('1/0',backend='trusted').passed)
    def test_timeout(self):
        self.assertTrue(run_code('while True: pass',backend='trusted',timeout=.15).timed_out)
    def test_repair(self):
        result=self.fix()
        self.assertEqual(result['status'],'tests_passed')
        self.assertTrue(result['diff'])
        self.assertIn('float',result['source'])
    def test_rejected_patch(self):
        result=self.fix(proposer=lambda *args:'def add_fee(amount): return 9\n')
        self.assertEqual(result['status'],'needs_review')
        self.assertEqual(result['source'],SOURCE)
        self.assertEqual(len(result['attempts']),2)
    def test_invalid_patch(self):
        self.assertEqual(self.fix(proposer=lambda *args:'def bad(')['status'],'needs_review')
    def test_retry_limit(self):
        with self.assertRaises(ValueError): self.fix(retries=13)
    def test_missing_test(self):
        with self.assertRaises(ValueError): repair(SOURCE,'pass','unused',contract='test')
    def test_splits(self):
        rows=[json.loads(s) for s in Path('data/dataset.jsonl').read_text().splitlines()]
        self.assertEqual({r['label'] for r in rows},set(RECIPES))
        for a,b in [('train','test'),('train','validation'),('validation','test')]:
            for key in ['family','traceback']:
                self.assertFalse({r[key] for r in rows if r['split']==a}&{r[key] for r in rows if r['split']==b})
    def test_gemini_missing_configuration(self):
        from pyfix.repair import gemini_patch
        with patch.dict('os.environ',{},clear=True):
            with self.assertRaises(ValueError): gemini_patch(SOURCE,'','type_conversion','add 2')
    def test_secret_not_in_child_environment(self):
        with patch.dict('os.environ',{'GEMINI_API_KEY':'test-secret'}):
            result=run_code("import os; print(os.getenv('GEMINI_API_KEY'))",backend='trusted')
        self.assertEqual(result.stdout.strip(),'None')
