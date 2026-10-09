"""Bounded statistics, distribution laws and stochastic reference algorithms.

Estimates and Monte Carlo are not proofs. Rates/likelihoods use documented
parameterisations (Poisson lambda; Gamma shape+scale; Exp rate).
"""
from __future__ import annotations
from math import comb, erf, exp, fsum, isfinite, lgamma, log, pi, sqrt
from random import Random
from .probability import distribution, ProbabilityError


def _real(x):
    if type(x) not in (int, float):
        raise ProbabilityError("Expected numeric scalar, not bool")
    try:
        value = float(x)
    except (ValueError, OverflowError) as exc:
        raise ProbabilityError("Number not representable as finite float") from exc
    if not isfinite(value):
        raise ProbabilityError("Expected finite numeric scalar")
    return value


def _positive(x, name):
    value = _real(x)
    if value <= 0:
        raise ProbabilityError(name + " must be positive")
    return value


def _prob(x):
    value = _real(x)
    if not 0 <= value <= 1:
        raise ProbabilityError("Probability must be in [0,1]")
    return value


def _integer(x, minimum=0, maximum=100000):
    if type(x) is not int or not minimum <= x <= maximum:
        raise ProbabilityError("Integer value out of supported bounds")
    return x


def _sample(values, minimum=1):
    if not isinstance(values, (list, tuple)) or not minimum <= len(values) <= 100000:
        raise ProbabilityError("Sample length outside 1..100000")
    return [_real(x) for x in values]


def sample_mean(values):
    xs = _sample(values)
    return fsum(xs) / len(xs)


def sample_variance(values, ddof=1):
    xs = _sample(values, 2 if ddof else 1)
    if ddof not in (0, 1) or type(ddof) is not int or len(xs) <= ddof:
        raise ProbabilityError("Invalid degrees of freedom")
    mean = fsum(xs) / len(xs)
    return fsum((x-mean)**2 for x in xs) / (len(xs)-ddof)


def covariance(x, y, ddof=1):
    a, b = _sample(x), _sample(y)
    if len(a) != len(b) or type(ddof) is not int or ddof not in (0,1) or len(a) <= ddof:
        raise ProbabilityError("Samples must have same length and enough observations")
    mean_a, mean_b = fsum(a)/len(a), fsum(b)/len(b)
    return fsum((u-mean_a)*(v-mean_b) for u,v in zip(a,b))/(len(a)-ddof)


def pearson(x, y):
    """Pearson r. Zero-variance correlation is undefined, never silently 0."""
    a,b=_sample(x,2),_sample(y,2)
    if len(a)!=len(b):
        raise ProbabilityError("Samples have different lengths")
    av,bv=fsum(a)/len(a),fsum(b)/len(b)
    ax=[u-av for u in a]
    bx=[u-bv for u in b]
    den=sqrt(fsum(u*u for u in ax)*fsum(v*v for v in bx))
    if den == 0:
        raise ProbabilityError("Pearson undefined with constant data")
    return max(-1., min(1., fsum(u*v for u,v in zip(ax,bx))/den))


def bernoulli_pmf(k,p):
    k=_integer(k,0,1)
    p=_prob(p)
    return p if k==1 else 1-p


def binomial_pmf(k,n,p):
    n=_integer(n,0,10000)
    k=_integer(k,0,10000)
    p=_prob(p)
    if k>n:
        return 0.
    return comb(n,k)*p**k*(1-p)**(n-k)


def poisson_pmf(k,rate):
    k=_integer(k,0,100000)
    rate=_positive(rate,"Poisson rate")
    return exp(k*log(rate)-rate-lgamma(k+1))


def normal_cdf(x,mean=0,sd=1):
    return .5*(1+erf((_real(x)-_real(mean))/(_positive(sd,"Standard deviation")*sqrt(2))))


def exponential_pdf(x,rate):
    x=_real(x)
    rate=_positive(rate,"Exponential rate")
    return rate*exp(-rate*x) if x>=0 else 0.


def exponential_cdf(x,rate):
    x=_real(x)
    rate=_positive(rate,"Exponential rate")
    return -__import__("math").expm1(-rate*x) if x>=0 else 0.


def uniform_pdf(x,low,high):
    x,low,high=map(_real,(x,low,high))
    if high<=low:
        raise ProbabilityError("Uniform upper bound must exceed lower")
    return 1/(high-low) if low<=x<=high else 0.


def beta_pdf(x,alpha,beta):
    x=_real(x)
    alpha,beta=_positive(alpha,"Alpha"),_positive(beta,"Beta")
    if not 0<x<1:
        raise ProbabilityError("For beta_pdf only interior x in (0,1) is supported")
    return exp((alpha-1)*log(x)+(beta-1)*log(1-x)
               +lgamma(alpha+beta)-lgamma(alpha)-lgamma(beta))


def gamma_pdf(x,shape,scale):
    x=_real(x)
    shape,scale=_positive(shape,"Shape"),_positive(scale,"Scale")
    if x<0:
        return 0.
    if x==0:
        if shape>1: return 0.
        if shape==1: return 1/scale
        raise ProbabilityError("Gamma PDF diverges at x=0 when shape<1")
    return exp((shape-1)*log(x)-x/scale-lgamma(shape)-shape*log(scale))


def mle_bernoulli(observations):
    xs=_sample(observations)
    if any(x not in (0.,1.) for x in xs):
        raise ProbabilityError("Bernoulli observations must be 0 or 1")
    return fsum(xs)/len(xs)


def mle_gaussian(observations):
    xs=_sample(observations)
    mean=fsum(xs)/len(xs)
    var=fsum((x-mean)**2 for x in xs)/len(xs)
    return {"mean":mean,"variance_mle":var}


def map_bernoulli_beta(observations,alpha,beta):
    """Interior posterior mode for alpha_post,beta_post > 1; reject boundaries."""
    p=mle_bernoulli(observations)
    alpha,beta=_positive(alpha,"Alpha"),_positive(beta,"Beta")
    n=len(observations)
    successes=round(p*n)
    a,b=alpha+successes,beta+n-successes
    if a<=1 or b<=1:
        raise ProbabilityError("Posterior mode lies on boundary; use posterior mean")
    return (a-1)/(a+b-2)


def posterior_mean_bernoulli_beta(observations,alpha,beta):
    p=mle_bernoulli(observations)
    alpha,beta=_positive(alpha,"Alpha"),_positive(beta,"Beta")
    return (alpha+round(p*len(observations)))/(alpha+beta+len(observations))


def markov_step(state,transition):
    """State row-vector times row-stochastic transition matrix."""
    s=distribution(state)
    if not isinstance(transition,(list,tuple)) or len(transition)!=len(s):
        raise ProbabilityError("Transition matrix must match number of states")
    rows=[distribution(r) for r in transition]
    if any(len(r)!=len(s) for r in rows):
        raise ProbabilityError("Transition matrix must be square")
    output=[fsum(s[i]*rows[i][j] for i in range(len(s))) for j in range(len(s))]
    return output


def random_walk(steps,seed=0):
    """Seeded ±1 random walk starting at 0; toy model, not a finance forecaster."""
    steps=_integer(steps,0,100000)
    seed=_integer(seed,0,2147483647)
    rng=Random(seed)
    location=0
    path=[0]
    for _ in range(steps):
        location+=1 if rng.getrandbits(1) else -1
        path.append(location)
    return path


def monte_carlo_pi(samples,seed=0):
    """Bounded reproducible MC estimate (not guaranteed accuracy)."""
    samples=_integer(samples,1,1000000)
    seed=_integer(seed,0,2147483647)
    rng=Random(seed)
    hits=sum(1 for _ in range(samples) if rng.random()**2+rng.random()**2<=1.)
    return {"estimate":4*hits/samples,"samples":samples,"seed":seed}
