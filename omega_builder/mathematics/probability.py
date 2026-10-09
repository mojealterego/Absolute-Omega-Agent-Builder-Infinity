"""Auditable discrete probability and information theory primitives."""
from math import log, sqrt, isfinite, fsum

class ProbabilityError(ValueError):
    pass

def _finite(x):
    if type(x) not in (float,int) or not isfinite(float(x)):
        raise ProbabilityError("Not a finite number")
    return float(x)

def distribution(weights,tol=1e-9):
    if not isinstance(weights,(tuple,list)) or not 1<=len(weights)<=100000:
        raise ProbabilityError("Nonempty probability vector required")
    p=[_finite(x) for x in weights]
    if any(x<0 for x in p) or abs(fsum(p)-1.)>tol:
        raise ProbabilityError("Probabilities must sum to one")
    return p

def bayes(prior,likelihood_positive,likelihood_negative):
    """P(H|E) for binary H, two likelihoods P(E|H), P(E|not H)."""
    p,a,b=map(_finite,(prior,likelihood_positive,likelihood_negative))
    if any(x<0 or x>1 for x in (p,a,b)):
        raise ProbabilityError("Expected probabilities in [0,1]")
    evidence=p*a+(1-p)*b
    if evidence==0:
        raise ProbabilityError("Cannot condition on zero-probability evidence")
    return p*a/evidence

def conditional(p_a_and_b,p_b):
    ab,b=map(_finite,(p_a_and_b,p_b))
    if b<=0 or b>1 or ab<0 or ab>b:
        raise ProbabilityError("Invalid event probabilities")
    return ab/b

def expectation(values,probabilities):
    p=distribution(probabilities)
    if len(values)!=len(p):
        raise ProbabilityError("Dimension mismatch")
    return fsum(_finite(v)*pr for v,pr in zip(values,p))

def variance(values,probabilities):
    mean=expectation(values,probabilities)
    p=distribution(probabilities)
    return fsum(pr*(_finite(v)-mean)**2 for v,pr in zip(values,p))

def entropy(probabilities,base=2):
    p=distribution(probabilities)
    base=_finite(base)
    if base<=0 or base==1:
        raise ProbabilityError("Invalid logarithm base")
    return -fsum(x*log(x,base) for x in p if x>0)

def cross_entropy(p,q,base=2):
    p,q=distribution(p),distribution(q)
    if len(p)!=len(q):
        raise ProbabilityError("Dimension mismatch")
    if any(x>0 and y==0 for x,y in zip(p,q)):
        return float("inf")
    return -fsum(x*log(y,base) for x,y in zip(p,q) if x>0)

def kl(p,q,base=2):
    p,q=distribution(p),distribution(q)
    if len(p)!=len(q):
        raise ProbabilityError("Dimension mismatch")
    if any(x>0 and y==0 for x,y in zip(p,q)):
        return float("inf")
    return fsum(x*log(x/y,base) for x,y in zip(p,q) if x>0)

def normal_pdf(x,mean=0,sd=1):
    x,mean,sd=map(_finite,(x,mean,sd))
    if sd<=0:
        raise ProbabilityError("Standard deviation must be positive")
    return 1/(sd*sqrt(2*3.141592653589793))*__import__("math").exp(-.5*((x-mean)/sd)**2)
