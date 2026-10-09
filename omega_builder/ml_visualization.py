"""Compute plot-ready descriptive summaries and optional real PNG plots.

No image synthesis or guesswork: actual user data points are plotted.
"""
from __future__ import annotations
from math import isfinite, ceil, floor
from .ml_validation import ValidationError, _numeric

def histogram(values,bins=10):
    values=_numeric(values)
    if type(bins) is not int or not 1<=bins<=100:
        raise ValidationError("Bins must be 1..100")
    left=min(values);right=max(values)
    if right==left:
        return {"counts":[len(values)],"edges":[left,right],"note":"constant sample"}
    width=(right-left)/bins
    counts=[0]*bins
    for value in values:
        index=min(bins-1,int((value-left)/width))
        counts[index]+=1
    return {"counts":counts,"edges":[left+width*i for i in range(bins)]+[right]}

def _quartile(a,fraction):
    index=(len(a)-1)*fraction
    lower=int(index);upper=min(lower+1,len(a)-1)
    return a[lower]+(a[upper]-a[lower])*(index-lower)

def boxplot_summary(values):
    a=sorted(_numeric(values))
    q1=_quartile(a,.25);q2=_quartile(a,.5);q3=_quartile(a,.75)
    iqr=q3-q1
    lower=q1-1.5*iqr;upper=q3+1.5*iqr
    inner=[v for v in a if lower<=v<=upper]
    return {"min":a[0],"q1":q1,"median":q2,"q3":q3,"max":a[-1],
            "whisker_low":inner[0],"whisker_high":inner[-1],
            "outlier_count":len(a)-len(inner),"n":len(a)}

def scatter_points(x,y):
    a=_numeric(x);b=_numeric(y)
    if len(a)!=len(b):
        raise ValidationError("Scatter x/y length mismatch")
    return {"x":a,"y":b,"n":len(a)}

def heatmap_matrix(rows):
    if not isinstance(rows,(list,tuple)) or not 1<=len(rows)<=1000:
        raise ValidationError("Heatmap dimensions out of bounds")
    data=[_numeric(row) for row in rows]
    cols=len(data[0])
    if any(len(row)!=cols for row in data):
        raise ValidationError("Ragged heatmap")
    return {"matrix":data,"min":min(min(row) for row in data),
            "max":max(max(row) for row in data)}

def render_png(plot_type,data,output_path):
    """Opt-in matplotlib. Caller must explicitly supply file path; NOT exposed via JSON."""
    if plot_type not in ("histogram","boxplot","scatter","heatmap"):
        raise ValidationError("Unsupported plot type")
    if not isinstance(output_path,str) or not output_path.lower().endswith(".png"):
        raise ValidationError("PNG file path required")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValidationError("PNG plotting requires pip install '.[visual]'") from exc
    fig,ax=plt.subplots()
    if plot_type=="histogram":
        _numeric(data)
        ax.hist(data,bins=10)
    elif plot_type=="boxplot":
        _numeric(data)
        ax.boxplot(data)
    elif plot_type=="scatter":
        if not isinstance(data,dict):
            raise ValidationError("Scatter requires x/y mapping")
        points=scatter_points(data.get("x"),data.get("y"))
        ax.scatter(points["x"],points["y"])
    else:
        matrix=heatmap_matrix(data)
        im=ax.imshow(matrix["matrix"],aspect="auto")
        fig.colorbar(im,ax=ax)
    try:
        fig.savefig(output_path,format="png",dpi=130,bbox_inches="tight")
    finally:
        plt.close(fig)
    return {"plot":plot_type,"file":output_path}
