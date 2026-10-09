"""Data-quality, privacy and fairness diagnostics; no compliance certification."""
from __future__ import annotations
from collections import Counter,defaultdict
import hashlib
import hmac
import json
import re

class GovernanceError(ValueError):
    pass

def _json(value):
    try:
        data=json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False,ensure_ascii=False)
    except (ValueError,TypeError) as exc:
        raise GovernanceError("Expected finite JSON-compatible data") from exc
    if len(data)>1_000_000:
        raise GovernanceError("JSON object is too large")
    return data

def fingerprint(value):
    """SHA-256 for provenance/deduplication; not encryption or pseudonymization."""
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()

def dataset_quality(rows):
    if not isinstance(rows,(list,tuple)) or not 1<=len(rows)<=100000 or any(not isinstance(row,dict) for row in rows):
        raise GovernanceError("Expected 1..100000 record mappings")
    columns=sorted({key for row in rows for key in row})
    if len(columns)>1000 or any(not isinstance(key,str) for key in columns):
        raise GovernanceError("Invalid or excessive column names")
    unique=Counter(_json(row) for row in rows)
    return {"rows":len(rows),"columns":columns,
            "missing_counts":{key:sum(row.get(key) is None for row in rows) for key in columns},
            "duplicate_rows":sum(n-1 for n in unique.values()),
            "unique_rows":len(unique),"scope":"descriptive_only"}

def split_overlap(train,validation,test):
    """Potential exact-content leakage; same-content rows may legitimately recur."""
    groups=(train,validation,test)
    if any(not isinstance(items,(tuple,list)) for items in groups) or sum(map(len,groups))>100000:
        raise GovernanceError("Expected 3 bounded datasets")
    a,b,c=(set(_json(row) for row in items) for items in groups)
    result={"train_validation":len(a&b),"train_test":len(a&c),
            "validation_test":len(b&c)}
    return {"overlap_by_content":result,"potential_leakage":any(result.values())}

def weak_supervision(rows,column,label_keywords):
    """Deterministic literal keyword labeller; ambiguous/unmatched items abstain."""
    if not isinstance(rows,(list,tuple)) or len(rows)>100000 or not isinstance(column,str) or not column:
        raise GovernanceError("Invalid rows or column")
    if not isinstance(label_keywords,dict) or not 1<=len(label_keywords)<=100:
        raise GovernanceError("Expected label-to-keywords mapping")
    rules={}
    for label,words in label_keywords.items():
        if not isinstance(label,str) or not label or not isinstance(words,(list,tuple)) or not words:
            raise GovernanceError("Invalid rule")
        if any(not isinstance(w,str) or not w or len(w)>128 for w in words):
            raise GovernanceError("Keywords must be short literals")
        rules[label]=[w.casefold() for w in words]
    predicted=[]
    for row in rows:
        if not isinstance(row,dict) or not isinstance(row.get(column),str):
            raise GovernanceError("Text field missing")
        value=row[column].casefold()
        matches=[label for label,keywords in rules.items()
                 if any(token in value for token in keywords)]
        predicted.append(matches[0] if len(matches)==1 else None)
    return {"labels":predicted,"abstentions":predicted.count(None),
            "method":"literal_keyword_weak_supervision_not_snorkel"}

def pseudonymize(value,key,namespace="omega"):
    """Deterministic HMAC pseudonym. Key MUST be stored outside the repository."""
    if not isinstance(value,str) or not 1<=len(value)<=10000:
        raise GovernanceError("Identifier must be string")
    if not isinstance(key,bytes) or len(key)<16:
        raise GovernanceError("Secret must be >=16 bytes")
    if not isinstance(namespace,str) or not 1<=len(namespace)<=128:
        raise GovernanceError("Namespace invalid")
    return hmac.new(key,(namespace+"\x00"+value).encode("utf-8"),hashlib.sha256).hexdigest()

def redact_common_identifiers(text):
    """Best-effort masking, NOT GDPR anonymization or comprehensive PII scanning."""
    if not isinstance(text,str) or len(text)>1000000:
        raise GovernanceError("Text is too large")
    email=re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")
    eleven=re.compile(r"(?<!\d)\d{11}(?!\d)")
    return eleven.sub("[11_DIGITS]",email.sub("[EMAIL]",text))

def binary_group_metrics(y_true,y_pred,groups,positive=1,min_size=5):
    """Observed selection rates, TPR/FPR and gap, not normative/causal fairness."""
    if any(not isinstance(arr,(tuple,list)) for arr in (y_true,y_pred,groups)):
        raise GovernanceError("Lists required")
    if not 1<=len(y_true)<=100000 or len(y_true)!=len(y_pred) or len(y_true)!=len(groups):
        raise GovernanceError("Inconsistent data lengths")
    if type(min_size) is not int or not 2<=min_size<=10000:
        raise GovernanceError("Invalid group suppression threshold")
    partitions=defaultdict(list)
    for idx,group in enumerate(groups):
        if not isinstance(group,str) or not group:
            raise GovernanceError("Group ID must be string")
        partitions[group].append(idx)
    if not 2<=len(partitions)<=100:
        raise GovernanceError("At least 2 groups required")
    metrics={}
    for group,idxs in sorted(partitions.items()):
        if len(idxs)<min_size:
            raise GovernanceError("Group too small: report suppressed")
        positives=sum(y_true[i]==positive for i in idxs)
        negatives=len(idxs)-positives
        tp=sum(y_true[i]==positive and y_pred[i]==positive for i in idxs)
        fp=sum(y_true[i]!=positive and y_pred[i]==positive for i in idxs)
        metrics[group]={"count":len(idxs),"selection_rate":(tp+fp)/len(idxs),
                        "tpr":tp/positives if positives else None,
                        "fpr":fp/negatives if negatives else None}
    rates=[v["selection_rate"] for v in metrics.values()]
    return {"groups":metrics,"selection_rate_gap":max(rates)-min(rates),
            "scope":"diagnostic_only_no_fairness_certification"}

def classification_conflicts(features,labels):
    """Detect exact duplicate feature rows with conflicting labels only."""
    if not isinstance(features,(tuple,list)) or not isinstance(labels,(tuple,list)):
        raise GovernanceError("Data must be lists")
    if not 1<=len(features)<=100000 or len(features)!=len(labels):
        raise GovernanceError("Length mismatch")
    seen=defaultdict(set)
    for x,label in zip(features,labels):
        if type(label) not in (int,str,bool):
            raise GovernanceError("Labels must be scalars")
        seen[_json(x)].add((type(label).__name__,label))
    return {"conflicting_rows":sum(len(v)>1 for v in seen.values()),
            "scope":"weak_data_poisoning_signal_only"}

def concept_drift_report(previous_true,previous_pred,current_true,current_pred):
    """Performance monitoring requires *labelled* data; detects change, not cause."""
    from .ml_validation import classification_report
    try:
        a=classification_report(previous_true,previous_pred)
        b=classification_report(current_true,current_pred)
    except ValueError as exc:
        raise GovernanceError(str(exc)) from exc
    return {"old_accuracy":a["accuracy"],"new_accuracy":b["accuracy"],
            "accuracy_delta":b["accuracy"]-a["accuracy"],
            "old_macro_f1":a["macro_f1"],"new_macro_f1":b["macro_f1"],
            "scope":"observed_accuracy_drift_not_causal_inference"}
