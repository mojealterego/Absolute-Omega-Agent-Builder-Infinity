"""Reproducible supervised ML evaluation, resampling and drift diagnostics.

Strict separation: original sample indices define disjoint partitions, and
resampling/feature fitting MUST only be applied to the resulting train set.
This module does not run models or fit on test sets.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from bisect import bisect_right
from hashlib import sha256
import json
from math import fsum, isfinite, log
from random import Random


class ValidationError(ValueError):
    pass


def _int(value, lo, hi, what):
    if type(value) is not int or not lo <= value <= hi:
        raise ValidationError(f"{what} must be integer in [{lo}, {hi}]")
    return value


def _ratio(value, name):
    if type(value) not in (int, float) or not isfinite(float(value)) or not 0 <= value < 1:
        raise ValidationError(f"{name} must be finite in [0,1)")
    return float(value)


def _labels(labels, n):
    if labels is None:
        return None
    if not isinstance(labels, (list, tuple)) or len(labels) != n:
        raise ValidationError("Stratification labels must match number of samples")
    if any(type(label) not in (int, str, bool) for label in labels):
        raise ValidationError("Class labels must be strings, integers or booleans")
    return labels


def _allocate(partition, val_ratio, test_ratio):
    # Every represented class has at least one train, validation, test example
    # if both latter ratios are nonzero; otherwise fail closed.
    n = len(partition)
    requested = 1 + bool(val_ratio) + bool(test_ratio)
    if n < requested:
        raise ValidationError("Not enough observations per class to populate all splits")
    val_n = max(1, round(n * val_ratio)) if val_ratio else 0
    test_n = max(1, round(n * test_ratio)) if test_ratio else 0
    if val_n + test_n >= n:
        raise ValidationError("Not enough observations for nonempty training split")
    return (partition[:n-val_n-test_n],
            partition[n-val_n-test_n:n-test_n] if test_n else partition[n-val_n:],
            partition[n-test_n:] if test_n else [])


def split_indices(n, validation_ratio=0.2, test_ratio=0.2, seed=0, labels=None):
    """Disjoint original-index split. Never returns a learned transformer."""
    _int(n, 3, 100000, "n")
    _int(seed, 0, 2147483647, "seed")
    val, test = _ratio(validation_ratio, "validation_ratio"), _ratio(test_ratio, "test_ratio")
    if val + test >= 1:
        raise ValidationError("Train ratio must be positive")
    label_values = _labels(labels, n)
    rng = Random(seed)
    groups = defaultdict(list)
    if label_values is None:
        groups["__all__"] = list(range(n))
    else:
        for idx, label in enumerate(label_values):
            groups[(type(label).__name__, label)].append(idx)
    train, validation, holdout = [], [], []
    for key in sorted(groups, key=str):
        segment = groups[key][:]
        rng.shuffle(segment)
        a, b, c = _allocate(segment, val, test)
        train.extend(a)
        validation.extend(b)
        holdout.extend(c)
    rng.shuffle(train); rng.shuffle(validation); rng.shuffle(holdout)
    assert len(set(train) | set(validation) | set(holdout)) == n
    assert not (set(train) & set(validation) or set(train) & set(holdout)
                or set(validation) & set(holdout))
    return {"train": train, "validation": validation, "test": holdout,
            "seed": seed, "stratified": label_values is not None}


def kfold_indices(n, folds=5, seed=0, labels=None):
    """All test folds disjoint. Stratification requires >=folds per class."""
    _int(n, 2, 100000, "n")
    _int(folds, 2, n, "folds")
    _int(seed, 0, 2147483647, "seed")
    label_values = _labels(labels, n)
    rng = Random(seed)
    groups = defaultdict(list)
    if label_values is None:
        groups["__all__"] = list(range(n))
    else:
        for idx, label in enumerate(label_values):
            groups[(type(label).__name__, label)].append(idx)
    buckets = [[] for _ in range(folds)]
    for key in sorted(groups, key=str):
        idxs = groups[key][:]
        if len(idxs) < folds:
            raise ValidationError("Each stratified class needs >=folds observations")
        rng.shuffle(idxs)
        for j, idx in enumerate(idxs):
            buckets[j % folds].append(idx)
    output = []
    all_idx = set(range(n))
    for subset in buckets:
        if not subset:
            raise ValidationError("Empty test fold")
        test = sorted(subset)
        output.append({"train": sorted(all_idx - set(subset)), "test": test})
    assert sorted(x for part in output for x in part["test"]) == list(range(n))
    return output


def leave_one_out(n):
    _int(n, 2, 1000, "n")
    all_idx = list(range(n))
    return [{"train": all_idx[:i]+all_idx[i+1:], "test":[i]} for i in range(n)]


def classification_report(truth, predicted):
    """Macro metrics are averages over all observed classes, even if absent in preds."""
    if not isinstance(truth,(list,tuple)) or not isinstance(predicted,(list,tuple)):
        raise ValidationError("Lists of class labels required")
    if not 1 <= len(truth) <= 100000 or len(truth) != len(predicted):
        raise ValidationError("Inconsistent number of labels")
    for label in list(truth)+list(predicted):
        if type(label) not in (int, str, bool):
            raise ValidationError("Class labels must be scalar")
    classes = sorted(set(truth) | set(predicted), key=lambda x:(str(type(x)),str(x)))
    if len(classes)>1000:
        raise ValidationError("Too many classes")
    # Accumulate O(n + C^2), never scan all observations for every cell.
    index={label:i for i,label in enumerate(classes)}
    cm=[[0 for _ in classes] for _ in classes]
    for observed,expected in zip(truth,predicted):
        cm[index[observed]][index[expected]]+=1
    details=[]
    for index,c in enumerate(classes):
        tp=cm[index][index]
        support=sum(cm[index])
        predicted_count=sum(row[index] for row in cm)
        recall=tp/support if support else 0.
        precision=tp/predicted_count if predicted_count else 0.
        f1=2*precision*recall/(precision+recall) if precision+recall else 0.
        details.append({"label":c, "support":support, "precision":precision,
                        "recall":recall, "f1":f1})
    macro=lambda key: fsum(row[key] for row in details)/len(details)
    return {"classes":classes,"confusion_matrix":cm,
            "accuracy":sum(a==b for a,b in zip(truth,predicted))/len(truth),
            "balanced_accuracy":macro("recall"),
            "macro_f1":macro("f1"),"per_class":details}


def _numeric(values):
    if not isinstance(values,(list,tuple)) or not 1<=len(values)<=100000:
        raise ValidationError("Expected nonempty numeric array up to 100000")
    result=[]
    for value in values:
        if type(value) not in (int,float) or not isfinite(float(value)):
            raise ValidationError("All numeric values must be finite")
        result.append(float(value))
    return result


def ks_distance(reference,current):
    """Two-sample empirical Kolmogorov–Smirnov D, no p-value claim."""
    a,b=sorted(_numeric(reference)),sorted(_numeric(current))
    points=sorted(set(a)|set(b))
    return max(abs(bisect_right(a,x)/len(a)-bisect_right(b,x)/len(b))
               for x in points)


def psi(reference,current,bins=10):
    """Population Stability Index with reference-quantile binning.

    PSI is a heuristic drift signal, not a p-value. Repeated quantiles collapse
    to unique boundaries; Laplace-like additive smoothing avoids log(0).
    """
    a,b=sorted(_numeric(reference)),_numeric(current)
    _int(bins,2,50,"bins")
    boundaries=sorted(set(a[min(len(a)-1,round(len(a)*i/bins))] for i in range(1,bins)))
    width=len(boundaries)+1
    ca=Counter(bisect_right(boundaries,x) for x in a)
    cb=Counter(bisect_right(boundaries,x) for x in b)
    pa=[(ca[j]+.5)/(len(a)+.5*width) for j in range(width)]
    pb=[(cb[j]+.5)/(len(b)+.5*width) for j in range(width)]
    return {"psi":fsum((v-u)*log(v/u) for u,v in zip(pa,pb)),
            "bin_boundaries":boundaries,"smoothed":True,
            "scope":"heuristic_covariate_drift_only"}


def smote_train(matrix, labels, neighbors=3, seed=0):
    """Binary-class SMOTE interpolation on TRAIN data only, with seeded RNG.

    Euclidean distance without feature normalization; callers MUST scale
    numeric training features before resampling, never fit on validation/test.
    """
    data = matrix
    if not isinstance(data,(list,tuple)) or not 4<=len(data)<=5000:
        raise ValidationError("SMOTE accepts 4..5000 training rows")
    if not isinstance(labels,(list,tuple)) or len(labels)!=len(data):
        raise ValidationError("Labels length mismatch")
    if any(type(label) not in (str,int,bool) for label in labels):
        raise ValidationError("Only categorical class labels supported")
    cols=None;rows=[]
    for row in data:
        v=_numeric(row)
        if cols is None:
            cols=len(v)
        if len(v)!=cols or cols>256:
            raise ValidationError("SMOTE expects consistent <=256 dimensions")
        rows.append(v)
    groups=defaultdict(list)
    for idx,label in enumerate(labels):
        groups[(type(label).__name__,label)].append(idx)
    if len(groups)!=2:
        raise ValidationError("This implementation requires binary classes")
    majority=max(groups.values(),key=len)
    minority=min(groups.values(),key=len)
    _int(neighbors,1,20,"neighbors"); _int(seed,0,2147483647,"seed")
    if len(minority)<neighbors+1:
        raise ValidationError("Minority support must exceed number of neighbors")
    if len(minority)==len(majority):
        return {"X":rows,"y":list(labels),"synthetic":0,"fit_scope":"training_only"}
    rng=Random(seed)
    out=rows[:];y=list(labels)
    while len(out)-len(rows)<len(majority)-len(minority):
        source=rng.choice(minority)
        near=sorted((fsum((rows[source][d]-rows[j][d])**2 for d in range(cols)),j)
                    for j in minority if j!=source)
        other=rng.choice([j for _,j in near[:neighbors]])
        alpha=rng.random()
        out.append([a+alpha*(b-a) for a,b in zip(rows[source],rows[other])])
        y.append(labels[source])
    return {"X":out,"y":y,"synthetic":len(out)-len(rows),
            "fit_scope":"training_only"}


def active_learning_uncertainty(probabilities,top_k=10):
    """Rank unlabelled class-probability rows by entropy (not calibrated confidence)."""
    from .mathematics.probability import distribution, entropy, ProbabilityError
    if not isinstance(probabilities,(list,tuple)) or not 1<=len(probabilities)<=10000:
        raise ValidationError("Expected 1..10000 probability rows")
    _int(top_k,1,10000,"top_k")
    try:
        ranked=[{"index":j,"entropy_bits":entropy(distribution(row))}
                for j,row in enumerate(probabilities)]
    except ProbabilityError as exc:
        raise ValidationError(str(exc)) from exc
    return sorted(ranked,key=lambda o:(-o["entropy_bits"],o["index"]))[:top_k]
