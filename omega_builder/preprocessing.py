"""Train-only fitting and deterministic transforms. No automatic model training."""
from __future__ import annotations
from math import isfinite, fsum, sqrt
from statistics import median


class PreprocessingError(ValueError):
    pass


def _finite(x):
    if type(x) not in (int,float):
        raise PreprocessingError("Expected finite numeric value")
    x=float(x)
    if not isfinite(x):
        raise PreprocessingError("NaN and infinity are prohibited")
    return x


def _rows(rows):
    if not isinstance(rows,(list,tuple)) or not 1<=len(rows)<=100000:
        raise PreprocessingError("Expected 1..100000 observations")
    if any(not isinstance(row,dict) for row in rows):
        raise PreprocessingError("Rows must be dictionaries")
    return rows


def deduplicate_rows(rows):
    """Stable structural deduplication; preserves original order, does not modify input."""
    import json
    rows=_rows(rows)
    seen=set();out=[]
    for row in rows:
        try:
            key=json.dumps(row,sort_keys=True,ensure_ascii=False,allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise PreprocessingError("Only JSON-compatible, finite rows supported") from exc
        if key not in seen:
            seen.add(key)
            out.append(dict(row))
    return out


def fit_numeric(rows,column,fill_strategy="median"):
    """Fit numeric imputation and Z-score transform on TRAIN rows only."""
    rows=_rows(rows)
    if not isinstance(column,str) or not column:
        raise PreprocessingError("Column name is required")
    if fill_strategy not in ("median","mean"):
        raise PreprocessingError("Only median/mean imputation supported")
    values=[_finite(row[column]) for row in rows if row.get(column) is not None]
    if not values:
        raise PreprocessingError("Training set has no nonmissing values")
    fill=median(values) if fill_strategy=="median" else fsum(values)/len(values)
    complete=[fill if row.get(column) is None else _finite(row[column]) for row in rows]
    mean=fsum(complete)/len(complete)
    sd=sqrt(fsum((v-mean)**2 for v in complete)/len(complete))
    return {"column":column,"impute":float(fill),"mean":mean,"std":sd,
            "scale":sd if sd>0 else 1.,"constant":sd==0,
            "fit_rows":len(rows),"fit_scope":"training_only"}


def transform_numeric(rows,model):
    rows=_rows(rows)
    if not isinstance(model,dict) or set(model)!={"column","impute","mean","std","scale","constant","fit_rows","fit_scope"}:
        raise PreprocessingError("Invalid fitted numeric transform")
    col=model["column"]
    if not isinstance(col,str) or not col or model["fit_scope"]!="training_only":
        raise PreprocessingError("Invalid fit model")
    fill,mean,scale=(_finite(model[x]) for x in ("impute","mean","scale"))
    if scale<=0:
        raise PreprocessingError("Scale must be positive")
    return [((fill if row.get(col) is None else _finite(row[col]))-mean)/scale for row in rows]


def one_hot_fit(rows,column):
    rows=_rows(rows)
    if not isinstance(column,str) or not column:
        raise PreprocessingError("Column is required")
    values=[]
    for row in rows:
        value=row.get(column)
        if not isinstance(value,str):
            raise PreprocessingError("Only non-null string categorical values are supported")
        values.append(value)
    return {"column":column,"categories":sorted(set(values)),"fit_scope":"training_only"}


def one_hot_transform(rows,model):
    rows=_rows(rows)
    if not isinstance(model,dict) or set(model)!={"column","categories","fit_scope"}:
        raise PreprocessingError("Invalid categorical model")
    cats=model["categories"]
    if (not isinstance(cats,list) or not cats or
        not all(isinstance(v,str) for v in cats) or cats!=sorted(set(cats))
        or model["fit_scope"]!="training_only"):
        raise PreprocessingError("Invalid category list")
    out=[]
    for row in rows:
        v=row.get(model["column"])
        if v not in cats:
            raise PreprocessingError("Unknown category: fail closed")
        out.append([int(v==category) for category in cats])
    return {"categories":cats[:],"vectors":out}


def iqr_bounds(values):
    xs=sorted(_finite(v) for v in values)
    if not 4<=len(xs)<=100000:
        raise PreprocessingError("IQR requires at least four observations")
    def quantile(q):
        pos=(len(xs)-1)*q
        low=int(pos)
        high=min(low+1,len(xs)-1)
        return xs[low]+(xs[high]-xs[low])*(pos-low)
    q1,q3=quantile(.25),quantile(.75)
    spread=q3-q1
    return {"q1":q1,"q3":q3,"lower":q1-1.5*spread,"upper":q3+1.5*spread}


def outlier_flags(values,bounds):
    if not isinstance(bounds,dict) or "lower" not in bounds or "upper" not in bounds:
        raise PreprocessingError("Missing IQR bounds")
    lower,upper=_finite(bounds["lower"]),_finite(bounds["upper"])
    if lower>upper:
        raise PreprocessingError("Invalid IQR bounds")
    return [not lower<=_finite(v)<=upper for v in values]


def pca_fit(matrix,n_components):
    """PCA learned on training matrix only; optional NumPy SVD backend."""
    if type(n_components) is not int or n_components<=0:
        raise PreprocessingError("Expected positive number of components")
    try:
        import numpy as np
    except ImportError as exc:
        raise PreprocessingError("PCA requires pip install '.[math]'") from exc
    try:
        x=np.asarray(matrix,dtype=float)
    except (ValueError,TypeError) as exc:
        raise PreprocessingError("Expected rectangular numerical matrix") from exc
    if x.ndim!=2 or not 2<=x.shape[0]<=10000 or not 1<=x.shape[1]<=256:
        raise PreprocessingError("PCA input must be 2..10000 rows and 1..256 columns")
    if not np.isfinite(x).all() or n_components>min(x.shape):
        raise PreprocessingError("Nonfinite data or too many components")
    means=x.mean(axis=0)
    _,s,vt=np.linalg.svd(x-means,full_matrices=False)
    variances=s*s/(x.shape[0]-1)
    total=float(variances.sum())
    ratio=(variances[:n_components]/total).tolist() if total else [0.]*n_components
    return {"mean":means.tolist(),"components":vt[:n_components].tolist(),
            "explained_variance_ratio":ratio,"fit_rows":int(x.shape[0]),
            "fit_scope":"training_only"}


def pca_transform(matrix,model):
    """Project test data with unchanged training eigenvectors; pure-Python evaluation."""
    if not isinstance(model,dict) or model.get("fit_scope")!="training_only":
        raise PreprocessingError("Invalid fitted PCA")
    means=model.get("mean");basis=model.get("components")
    if not isinstance(means,list) or not means or not isinstance(basis,list) or not basis:
        raise PreprocessingError("Missing PCA basis")
    means=[_finite(v) for v in means]
    if len(means)>256 or any(not isinstance(v,list) or len(v)!=len(means) for v in basis):
        raise PreprocessingError("Inconsistent PCA dimensions")
    if not isinstance(matrix,(tuple,list)) or not 1<=len(matrix)<=100000:
        raise PreprocessingError("Invalid projection inputs")
    out=[]
    for row in matrix:
        if not isinstance(row,(tuple,list)) or len(row)!=len(means):
            raise PreprocessingError("Projection dimensionality mismatch")
        xs=[_finite(v)-m for v,m in zip(row,means)]
        out.append([fsum(x*_finite(w) for x,w in zip(xs,vec)) for vec in basis])
    return out
