import argparse
import json
from pathlib import Path
from dotenv import load_dotenv
from .dataset import build_dataset
from .training import train, predict
from .repair import repair

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description='PyFix experiment and repair commands')
    commands = parser.add_subparsers(dest='command',required=True)
    generate = commands.add_parser('generate'); generate.add_argument('--variants',type=int,default=12)
    commands.add_parser('train')
    classify = commands.add_parser('classify'); classify.add_argument('traceback')
    fix = commands.add_parser('repair'); fix.add_argument('source'); fix.add_argument('--tests',required=True); fix.add_argument('--contract',required=True); fix.add_argument('--provider',choices=['offline','gemini'],default='offline'); fix.add_argument('--runner',choices=['docker','trusted'],default='docker'); fix.add_argument('--output',default='repair-result.json')
    commands.add_parser('serve')
    args = parser.parse_args()
    if args.command == 'generate':
        if not 1 <= args.variants <= 100: parser.error('variants must be between 1 and 100')
        rows = build_dataset('data/dataset.jsonl',args.variants); print(f'Generated {len(rows)} verified mutations')
    elif args.command == 'train': print(json.dumps(train('data/dataset.jsonl','artifacts'),indent=2))
    elif args.command == 'classify': print(json.dumps(predict(Path(args.traceback).read_text(),'artifacts/model.joblib'),indent=2))
    elif args.command == 'repair':
        result = repair(Path(args.source).read_text(),Path(args.tests).read_text(),'artifacts/model.joblib',contract=args.contract,provider=args.provider,backend=args.runner)
        Path(args.output).write_text(json.dumps(result,indent=2)); print(result['status'])
        raise SystemExit(0 if result['status'] in {'tests_passed','already_passing'} else 1)
    else:
        import uvicorn
        uvicorn.run('pyfix.app:app',host='127.0.0.1',port=8000)
if __name__ == '__main__': main()
