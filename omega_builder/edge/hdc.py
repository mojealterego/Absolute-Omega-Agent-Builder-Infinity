"""Deterministic bipolar HDC/VSA baseline plus optional torchhd path.

Use simple single-key bindings to avoid claiming exact retrieval from a noisy
multi-binding associative memory. torchhd cosine scores are approximate.
"""
from math import fsum,sqrt
from random import Random


class HDCError(ValueError):
    pass


def _dimension(dim):
    if type(dim) is not int or not 16<=dim<=100000:
        raise HDCError("HDC dimension must be 16..100000")
    return dim


def bipolar_vector(dim,seed):
    _dimension(dim)
    if type(seed) is not int or not 0<=seed<=2147483647:
        raise HDCError("Seed out of range")
    rng=Random(seed)
    return [1 if rng.getrandbits(1) else -1 for _ in range(dim)]


def bipolar_bind(a,b):
    if not isinstance(a,(list,tuple)) or not isinstance(b,(list,tuple)) or len(a)!=len(b):
        raise HDCError("Same-sized bipolar vectors required")
    _dimension(len(a))
    if any(type(v) is not int or v not in (-1,1) for v in list(a)+list(b)):
        raise HDCError("Elements must be exactly +/-1")
    return [x*y for x,y in zip(a,b)]


def bipolar_similarity(a,b):
    # Cosine similarity of bipolar vectors exactly equals normalized dot.
    return sum(bipolar_bind(a,b))/len(a)


def reference_associative_retrieval(dim=10000,seed=5):
    """Single key/value bind + inverse gives an exact retrieval in bipolar VSA."""
    _dimension(dim)
    key=bipolar_vector(dim,seed)
    value=bipolar_vector(dim,seed+1)
    stored=bipolar_bind(key,value)
    retrieved=bipolar_bind(stored,key)
    return {"backend":"python_bipolar_reference",
            "dimensions":dim,"recovery_similarity":bipolar_similarity(retrieved,value),
            "exact_single_pair_recovery":retrieved==value}


def torchhd_associative_demo(dim=10000,seed=5):
    """Actual torchhd operations. Cosine ranking is diagnostic, not guarantee."""
    _dimension(dim)
    if type(seed) is not int or not 0<=seed<=2147483647:
        raise HDCError("Seed out of range")
    try:
        import torch
        import torchhd
    except ImportError as exc:
        raise HDCError("Install optional torch/torchhd: pip install '.[hdc]'") from exc
    gen=torch.Generator(device="cpu").manual_seed(seed)
    keys=torchhd.random(2,dim,generator=gen)
    vals=torchhd.random(2,dim,generator=gen)
    # A known-correct table maps keys[0]->vals[0], keys[1]->vals[1].
    table=torchhd.hash_table(keys,vals)
    query=torchhd.bind(torchhd.inverse(keys[0]),table)
    similarity=torchhd.cosine_similarity(query,vals).detach().cpu().tolist()
    return {"backend":"torchhd","dimensions":dim,"similarity":similarity,
            "best_match":int(max(range(len(similarity)),key=lambda i:similarity[i])),
            "expected_match":0,"approximate":True}
