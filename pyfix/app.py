"""Local-only API. Never deploy trusted execution on a public host."""
from pathlib import Path
import json
import os
import threading
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .training import predict
from .repair import repair
from .examples import examples
load_dotenv()
ROOT=Path(__file__).parent
ARTIFACTS=Path(os.getenv('PYFIX_ARTIFACTS','artifacts'))
app=FastAPI(title='PyFix Research Workspace',version='2.0.0')
app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')
lock=threading.Lock()

@app.middleware('http')
async def local_origin(request:Request,call_next):
    host=request.headers.get('host','').split(':')[0]
    if host not in {'localhost','127.0.0.1','testserver'}:return JSONResponse({'detail':'Local access only'},status_code=403)
    origin=request.headers.get('origin')
    if origin and origin not in {'http://localhost:8000','http://127.0.0.1:8000'}:return JSONResponse({'detail':'Origin rejected'},status_code=403)
    if request.headers.get('sec-fetch-site')=='cross-site':return JSONResponse({'detail':'Cross-site request rejected'},status_code=403)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Cache-Control']='no-store'
    return response

class TraceRequest(BaseModel):
    traceback:str=Field(min_length=10,max_length=64000)
class RepairRequest(BaseModel):
    source:str=Field(min_length=1,max_length=40000)
    tests:str=Field(min_length=1,max_length=20000)
    contract:str=Field(min_length=5,max_length=4000)
    provider:str='offline'
    retries:int=Field(default=6,ge=1,le=12)
    allow_uncertain:bool=False

def artifact():
    path=ARTIFACTS/'model.joblib'
    if not path.exists():raise HTTPException(503,'Train the model first: python -m pyfix.cli train')
    return path

def report(name):
    path=ARTIFACTS/name
    if not path.exists():raise HTTPException(503,'Run training and benchmarks to generate this report.')
    return json.loads(path.read_text())
@app.get('/')
def index():return FileResponse(ROOT/'static/index.html')
@app.get('/api/metrics')
def metrics():return report('metrics.json')
@app.get('/api/benchmarks')
def benchmarks():return {'repair':report('repair_benchmark.json'),'external':report('external_benchmark.json')}
@app.get('/api/errors')
def errors():return report('error_analysis.json')
@app.get('/api/examples')
def demo_examples():return examples()
@app.get('/api/config')
def config():return {'runner':os.getenv('PYFIX_RUNNER','docker'),'gemini_configured':bool(os.getenv('GEMINI_API_KEY') and os.getenv('GEMINI_MODEL')),'version':'2.0.0'}
@app.post('/api/classify')
def classify(data:TraceRequest):return predict(data.traceback,artifact())
@app.post('/api/repair')
def fix(data:RepairRequest):
    model=artifact()
    if not lock.acquire(blocking=False):raise HTTPException(429,'A repair is already running')
    try:return repair(data.source,data.tests,model,contract=data.contract,provider=data.provider,retries=data.retries,allow_uncertain=data.allow_uncertain,backend=os.getenv('PYFIX_RUNNER','docker'))
    except (ValueError,SyntaxError) as exc:raise HTTPException(400,str(exc)) from exc
    except RuntimeError as exc:raise HTTPException(503,str(exc)) from exc
    finally:lock.release()
