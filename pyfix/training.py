"""Validation-selected models; untouched test split and simple baselines."""
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
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, ConfusionMatrixDisplay, classification_report
from .dataset import normalize_traceback

def metrics(y, p):
    precision, recall, f1, _ = precision_recall_fscore_support(y, p, average='macro', zero_division=0)
    return dict(accuracy=accuracy_score(y,p), precision_macro=precision, recall_macro=recall, f1_macro=f1)

def train(dataset, output):
    root = Path(output); root.mkdir(parents=True, exist_ok=True)
    frame = pd.read_json(dataset, lines=True)
    splits = {s: frame[frame.split == s] for s in ['train','validation','test']}
    for a,b in [('train','validation'),('train','test'),('validation','test')]:
        if set(splits[a].family) & set(splits[b].family):
            raise ValueError('Family leakage detected')
        if set(splits[a].traceback) & set(splits[b].traceback):
            raise ValueError('Duplicate traceback leakage detected')
    tr, va, te = (splits[s] for s in ['train','validation','test'])
    classifiers = {'Naive Bayes':MultinomialNB(alpha=.5), 'Logistic regression':LogisticRegression(max_iter=1500,random_state=42), 'SVM':SVC(kernel='linear',probability=True,random_state=42), 'Random forest':RandomForestClassifier(n_estimators=150,class_weight='balanced',random_state=42,n_jobs=1), 'AdaBoost':AdaBoostClassifier(n_estimators=100,random_state=42)}
    rows, models = [], {}
    labels = sorted(frame.label.unique())
    for name, estimator in classifiers.items():
        model = Pipeline([('tfidf',TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True,max_features=4000,token_pattern=r'(?u)\b\w+\b')),('classifier',estimator)])
        model.fit(tr.traceback,tr.label)
        models[name] = model
        rows.append(dict(model=name,validation=metrics(va.label,model.predict(va.traceback)),test=metrics(te.label,model.predict(te.traceback))))
    winner = max(rows,key=lambda row:row['validation']['f1_macro'])['model']
    selected = models[winner]
    # Winner remains trained on train only so displayed test scores match artifact.
    joblib.dump(selected,root/'model.joblib')
    lookup = defaultdict(Counter)
    for row in tr.itertuples(): lookup[row.exception][row.label] += 1
    majority = Counter(tr.label).most_common(1)[0][0]
    predictions = [lookup[e].most_common(1)[0][0] if e in lookup else majority for e in te.exception]
    baselines = {'majority':metrics(te.label,[majority]*len(te)), 'exception_only':metrics(te.label,predictions)}
    report = dict(selected_model=winner,selection='Highest validation macro F1; test untouched during selection',rows=rows,baselines=baselines,counts={s:len(f) for s,f in splits.items()},classes=labels,seed=42,limitations=['Synthetic mutations; six expression families per class only.', 'Held-out families improve evaluation but do not establish real-world generalisation.', 'Probabilities are model scores, not calibrated guarantees.', 'Tracebacks can be ambiguous; tests determine patch acceptance.'])
    (root/'metrics.json').write_text(json.dumps(report,indent=2))
    pd.DataFrame([{'model':r['model'],**r['test']} for r in rows]).to_csv(root/'comparison.csv',index=False)
    (root/'classification_report.json').write_text(json.dumps(classification_report(te.label,selected.predict(te.traceback),output_dict=True,zero_division=0),indent=2))
    for name, model in models.items():
        fig, ax = plt.subplots(figsize=(10,8))
        ConfusionMatrixDisplay(confusion_matrix(te.label,model.predict(te.traceback),labels=labels),display_labels=labels).plot(ax=ax,xticks_rotation=40,colorbar=False,cmap='Blues')
        ax.set_title(name+' — held-out families'); fig.tight_layout()
        fig.savefig(root/(name.lower().replace(' ','_')+'_confusion.png'),dpi=130); plt.close(fig)
    # Bounded dense PCA is descriptive only, never fed to MultinomialNB.
    vectorizer = selected.named_steps['tfidf']
    pca = PCA(n_components=2,random_state=42)
    pca.fit(vectorizer.transform(tr.traceback).toarray())
    coords = pca.transform(vectorizer.transform(te.traceback).toarray())
    fig,ax = plt.subplots(figsize=(10,6))
    for label in labels:
        mask = te.label.to_numpy() == label
        ax.scatter(coords[mask,0],coords[mask,1],label=label,alpha=.65)
    ax.set(xlabel='Principal component 1',ylabel='Principal component 2',title='Test tracebacks projected onto training-fitted PCA')
    ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(root/'pca.png',dpi=140); plt.close(fig)
    return report

def predict(traceback, artifact):
    model = joblib.load(artifact) # Load only your own trusted artifact.
    text = normalize_traceback(traceback)
    scores = model.predict_proba([text])[0]
    order = np.argsort(scores)[::-1]
    return {'label':str(model.classes_[order[0]]), 'score':float(scores[order[0]]), 'ranking':[{'label':str(model.classes_[i]),'score':float(scores[i])} for i in order], 'note':'Model scores are not calibrated confidence; unsupported bugs may be misclassified.'}
