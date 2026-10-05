"""Four-way program-disjoint evaluation, calibrated probabilities and ablations."""
import json
from collections import Counter, defaultdict
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.decomposition import PCA
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, ConfusionMatrixDisplay, classification_report, log_loss
from .dataset import normalize_traceback, exception_name

SUPPORTED = {'TypeError','AttributeError','IndexError','KeyError','ZeroDivisionError'}

def metrics(y,p):
    precision,recall,f1,_=precision_recall_fscore_support(y,p,average='macro',zero_division=0)
    return dict(accuracy=float(accuracy_score(y,p)),precision_macro=float(precision),recall_macro=float(recall),f1_macro=float(f1))

def texts(frame,mode='traceback'):
    if mode=='exception': return frame.exception.tolist()
    if mode=='traceback_code': return [normalize_traceback(t)+'\nSOURCE_CONTEXT\n'+s for t,s in zip(frame.traceback,frame.source)]
    return [normalize_traceback(t) for t in frame.traceback]

def weights(frame):
    return np.array([len(frame)/(frame.program.nunique()*sum(frame.program==p)) for p in frame.program])

def bootstrap_program_accuracy(frame,predictions):
    # Resample independent programs, not correlated input variants.
    correct=np.asarray(predictions)==frame.label.to_numpy()
    values=np.array([correct[frame.program.to_numpy()==p].mean() for p in frame.program.unique()])
    rng=np.random.default_rng(42)
    samples=rng.choice(values,size=(1000,len(values)),replace=True).mean(axis=1)
    return dict(mean=float(values.mean()),lower=float(np.quantile(samples,.025)),upper=float(np.quantile(samples,.975)),unit='program',programs=len(values))

def make_pipeline(estimator):
    return Pipeline([('tfidf',TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True,max_features=5000,token_pattern=r'(?u)\b\w+\b')),('classifier',estimator)])

def reliability(y,probabilities,classes):
    targets=np.array([[int(label==c) for c in classes] for label in y])
    return {'log_loss':float(log_loss(y,probabilities,labels=list(classes))),'brier_multiclass':float(np.mean(np.sum((probabilities-targets)**2,axis=1)))}

def threshold_on_validation(y,probabilities,classes):
    scores=probabilities.max(axis=1); guesses=np.array(classes)[probabilities.argmax(axis=1)]
    options=[]
    for threshold in np.arange(.25,.951,.025):
        accepted=(scores>=threshold) & ((np.sort(probabilities,axis=1)[:,-1]-np.sort(probabilities,axis=1)[:,-2])>=.08)
        count=int(accepted.sum())
        accuracy=float((guesses[accepted]==np.array(y)[accepted]).mean()) if count else None
        options.append({'threshold':round(float(threshold),3),'coverage':float(accepted.mean()),'accuracy':accuracy})
    usable=[r for r in options if r['accuracy'] is not None and r['accuracy']>=.85]
    selected=max(usable,key=lambda r:r['coverage']) if usable else {'threshold':.95,'coverage':0,'accuracy':None}
    return selected,options

def train(dataset,output):
    root=Path(output);root.mkdir(parents=True,exist_ok=True)
    frame=pd.read_json(dataset,lines=True)
    splits={s:frame[frame.split==s].copy() for s in ['train','calibration','validation','test']}
    for i,a in enumerate(splits):
        for b in list(splits)[i+1:]:
            for key in ['program','source']:
                if set(splits[a][key])&set(splits[b][key]):raise ValueError(f'{key} leakage between {a} and {b}')
    tr,ca,va,te=[splits[s] for s in splits]
    classifiers={'Naive Bayes':MultinomialNB(alpha=.5),'Logistic regression':LogisticRegression(max_iter=2000,random_state=42),'SVM':SVC(kernel='linear',probability=True,random_state=42),'Random forest':RandomForestClassifier(n_estimators=160,random_state=42,n_jobs=1),'AdaBoost':AdaBoostClassifier(n_estimators=100,random_state=42)}
    rows=[];models={};labels=sorted(frame.label.unique())
    for name,estimator in classifiers.items():
        base=make_pipeline(estimator);base.fit(texts(tr),tr.label,classifier__sample_weight=weights(tr))
        calibrated=CalibratedClassifierCV(FrozenEstimator(base),method='sigmoid',cv=[(np.arange(len(ca)),np.arange(len(ca)))])
        calibrated.fit(texts(ca),ca.label,sample_weight=weights(ca))
        models[name]=(base,calibrated)
        pred=calibrated.predict(texts(te))
        rows.append(dict(model=name,validation=metrics(va.label,calibrated.predict(texts(va))),test=metrics(te.label,pred),program_accuracy=bootstrap_program_accuracy(te,pred),calibration= {'before':reliability(te.label,base.predict_proba(texts(te)),base.classes_),'after':reliability(te.label,calibrated.predict_proba(texts(te)),calibrated.classes_)}))
    winner=max(rows,key=lambda r:r['validation']['f1_macro'])['model']
    base,selected=models[winner]
    policy,curve=threshold_on_validation(va.label,selected.predict_proba(texts(va)),selected.classes_)
    vectorizer=base.named_steps['tfidf']
    bundle=dict(version=2,model=selected,base=base,threshold=policy['threshold'],overlap_threshold=.15,mode='traceback',model_name=winner)
    joblib.dump(bundle,root/'model.joblib')
    lookup=defaultdict(Counter)
    for row in tr.itertuples():lookup[row.exception][row.label]+=1
    majority=Counter(tr.label).most_common(1)[0][0]
    baseline=[lookup[e].most_common(1)[0][0] if e in lookup else majority for e in te.exception]
    ablations=[]
    for mode in ['exception','traceback','traceback_code']:
        pipeline=make_pipeline(LogisticRegression(max_iter=2000,random_state=42))
        pipeline.fit(texts(tr,mode),tr.label,classifier__sample_weight=weights(tr))
        ablations.append(dict(features=mode,model='Logistic regression (uncalibrated, fixed)',validation=metrics(va.label,pipeline.predict(texts(va,mode))),test=metrics(te.label,pipeline.predict(texts(te,mode)))))
    predictions=selected.predict(texts(te));probs=selected.predict_proba(texts(te));conf=probs.max(axis=1)
    accepted=(conf>=policy['threshold']) & ((np.sort(probs,axis=1)[:,-1]-np.sort(probs,axis=1)[:,-2])>=.08)
    errors=[]
    for j,(_,r) in enumerate(te.iterrows()):
        errors.append(dict(id=r.id,program=r.program,actual=r.label,predicted=str(predictions[j]),score=float(conf[j]),accepted=bool(accepted[j]),correct=bool(predictions[j]==r.label),traceback=r.traceback))
    report=dict(version=2,selected_model=winner,selection='Validation macro F1; calibration uses a separate program partition.',rows=rows,baselines={'majority':metrics(te.label,[majority]*len(te)),'exception_only':metrics(te.label,baseline)},ablations=ablations,counts={s:len(f) for s,f in splits.items()},program_counts={s:int(f.program.nunique()) for s,f in splits.items()},classes=labels,seed=42,selective={'threshold':policy['threshold'],'selection':'Maximum validation coverage at >=85% empirical accuracy; fallback threshold 0.95','validation_curve':curve,'test_coverage':float(accepted.mean()),'test_accuracy_accepted':float((predictions[accepted]==te.label.to_numpy()[accepted]).mean()) if accepted.any() else None},limitations=['48 authored synthetic programs, with shared mutation patterns; not a production corpus.','Calibration and validation contain only one program per class; uncertainty estimates are preliminary.','Program bootstrap intervals have only 12 test programs and are descriptive.','Unknown-exception and vocabulary guards do not detect every unsupported bug.','External QuixBugs tasks are algorithmic challenge bugs, not production incidents.'])
    (root/'metrics.json').write_text(json.dumps(report,indent=2))
    (root/'error_analysis.json').write_text(json.dumps(errors,indent=2))
    (root/'classification_report.json').write_text(json.dumps(classification_report(te.label,predictions,output_dict=True,zero_division=0),indent=2))
    pd.DataFrame([{'model':r['model'],**r['test']} for r in rows]).to_csv(root/'comparison.csv',index=False)
    for name,(_,model) in models.items():
        fig,ax=plt.subplots(figsize=(10,8));ConfusionMatrixDisplay(confusion_matrix(te.label,model.predict(texts(te)),labels=labels),display_labels=labels).plot(ax=ax,xticks_rotation=40,colorbar=False,cmap='Blues');ax.set_title(name+' — unseen programs');fig.tight_layout();fig.savefig(root/(name.lower().replace(' ','_')+'_confusion.png'),dpi=120);plt.close(fig)
    pca=PCA(n_components=2,random_state=42);pca.fit(vectorizer.transform(texts(tr)).toarray());coords=pca.transform(vectorizer.transform(texts(te)).toarray())
    fig,ax=plt.subplots(figsize=(10,6))
    for label in labels:
        mask=te.label.to_numpy()==label;ax.scatter(coords[mask,0],coords[mask,1],label=label,alpha=.7)
    ax.set(xlabel='PC1',ylabel='PC2',title='Unseen programs projected through training-fitted PCA');ax.legend(fontsize=8);fig.tight_layout();fig.savefig(root/'pca.png',dpi=120);plt.close(fig)
    return report

def predict(traceback,artifact):
    bundle=joblib.load(artifact)
    if not isinstance(bundle,dict):raise ValueError('Legacy model artifact: rerun training.')
    model=bundle['model'];text=normalize_traceback(traceback)
    scores=model.predict_proba([text])[0];order=np.argsort(scores)[::-1]
    vectorizer=bundle['base'].named_steps['tfidf'];tokens=set(vectorizer.build_analyzer()(text));overlap=len(tokens & set(vectorizer.vocabulary_))/max(1,len(tokens))
    exception=exception_name(text);reasons=[]
    if exception not in SUPPORTED:reasons.append('Exception is outside the trained taxonomy.')
    if overlap<bundle['overlap_threshold']:reasons.append('Too little vocabulary overlap with training data.')
    if scores[order[0]]-scores[order[1]]<.08:reasons.append('The two leading categories are too close to distinguish reliably.')
    if scores[order[0]]<bundle['threshold']:reasons.append('Score is below the validation-selected threshold.')
    # Contribution to linear/log-NB score, not a causal explanation or calibrated probability decomposition.
    features=[];clf=bundle['base'].named_steps['classifier'];matrix=vectorizer.transform([text]);class_index=list(bundle['base'].classes_).index(model.classes_[order[0]])
    coefficients=getattr(clf,'coef_',None)
    if coefficients is None and hasattr(clf,'feature_log_prob_'):
        coefficients=clf.feature_log_prob_-clf.feature_log_prob_.mean(axis=0)
    if coefficients is not None and getattr(coefficients,'shape',(0,))[0]==len(model.classes_):
        coefficients=coefficients.toarray() if hasattr(coefficients,'toarray') else coefficients
        values=matrix.toarray()[0]*coefficients[class_index];names=vectorizer.get_feature_names_out()
        features=[{'token':str(names[i]),'contribution':float(values[i])} for i in np.argsort(values)[::-1][:8] if values[i]>0]
    return dict(label=str(model.classes_[order[0]]),score=float(scores[order[0]]),ranking=[{'label':str(model.classes_[i]),'score':float(scores[i])} for i in order],decision='needs_review' if reasons else 'supported',reasons=reasons,threshold=bundle['threshold'],vocabulary_overlap=overlap,exception=exception,features=features,note='Sigmoid-calibrated on held-out programs. Scores and rejection rules remain imperfect; tests decide patch acceptance.')
