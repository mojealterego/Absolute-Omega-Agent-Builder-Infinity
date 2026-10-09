"""Composite memory retrieval with strict scope isolation (CPU reference).

No LLM encoding, auto-consolidation, automatic forgetting or persistence.
A relevance score is NOT a guarantee of correctness or safe provenance.
"""
from __future__ import annotations
from math import exp, fsum, isfinite, sqrt
import re

class MemoryScoreError(ValueError):
    pass

ID=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")

def _vector(value):
    if not isinstance(value,(tuple,list)) or not 1<=len(value)<=4096:
        raise MemoryScoreError("Vector dimension limit: 1..4096")
    try:
        vector=[float(x) for x in value if type(x) in (int,float)]
    except (ValueError,OverflowError) as exc:
        raise MemoryScoreError("Malformed numeric vector") from exc
    if len(vector)!=len(value) or not all(isfinite(v) and abs(v)<=1e10 for v in vector):
        raise MemoryScoreError("Invalid vector elements")
    norm=sqrt(fsum(x*x for x in vector))
    if norm==0 or not isfinite(norm):
        raise MemoryScoreError("Zero/nonfinite vector norm")
    return vector,norm

def rank_memories(query,entries,*,scope,now_ms,
                  half_life_ms=86400000,weights=(.5,.3,.2),limit=10):
    """Rank same-scope observations: semantic + recency + importance.

    Similarity uses (cosine+1)/2; recency is exp(-ln(2)*age/half_life).
    Importance is caller-declared on [0,1] (not independently validated).
    """
    needle,norm=_vector(query)
    if not isinstance(entries,(tuple,list)) or len(entries)>5000:
        raise MemoryScoreError("Max 5000 records per retrieval")
    if not isinstance(scope,str) or not ID.fullmatch(scope):
        raise MemoryScoreError("Explicit scope required")
    if type(now_ms) is not int or now_ms<0 or type(half_life_ms) is not int or half_life_ms<1:
        raise MemoryScoreError("Invalid time parameters")
    if type(limit) is not int or not 1<=limit<=100:
        raise MemoryScoreError("Top-k must be 1..100")
    if not isinstance(weights,(list,tuple)) or len(weights)!=3:
        raise MemoryScoreError("Expected 3 scoring weights")
    if any(type(w) not in (int,float) or not isfinite(float(w)) or w<0 for w in weights):
        raise MemoryScoreError("Weights must be nonnegative and finite")
    if abs(fsum(weights)-1)>1e-9:
        raise MemoryScoreError("Weight sum must be one")
    ranked=[]
    seen=set()
    for entry in entries:
        if not isinstance(entry,dict) or set(entry)!={"id","scope","source","recorded_ms","importance","vector"}:
            raise MemoryScoreError("Record missing provenance, scope or shape")
        ident,record_scope,source=entry["id"],entry["scope"],entry["source"]
        if not isinstance(ident,str) or not ID.fullmatch(ident) or ident in seen:
            raise MemoryScoreError("Duplicate or malformed memory ID")
        seen.add(ident)
        if not isinstance(record_scope,str) or not ID.fullmatch(record_scope) or not isinstance(source,str) or not ID.fullmatch(source):
            raise MemoryScoreError("Bad scope/source metadata")
        recorded=entry["recorded_ms"]
        if type(recorded) is not int or recorded<0:
            raise MemoryScoreError("recorded_ms must be non-negative integer")
        imp=entry["importance"]
        if type(imp) not in (int,float) or not isfinite(float(imp)) or not 0<=imp<=1:
            raise MemoryScoreError("Importance must be [0,1]")
        data,data_norm=_vector(entry["vector"])
        if len(data)!=len(needle):
            raise MemoryScoreError("Incompatible vector dimension")
        if record_scope!=scope or recorded>now_ms:
            continue
        dot=fsum(a*b for a,b in zip(needle,data))/(norm*data_norm)
        cosine=max(-1.,min(1.,dot))
        semantic=(cosine+1)/2
        recency=exp(-.6931471805599453*(now_ms-recorded)/half_life_ms)
        value=weights[0]*semantic+weights[1]*recency+weights[2]*imp
        ranked.append({"id":ident,"source":source,"scope":record_scope,
                       "score":value,"semantic":semantic,"recency":recency,
                       "declared_importance":imp,"source_verified":False})
    ranked.sort(key=lambda row:(-row["score"],row["id"]))
    return {"results":ranked[:limit],"evaluated":len(ranked),
            "scores_are":"HEURISTIC_UNVERIFIED_NOT_FACT_CHECKED",
            "external_text_emitted":False}
