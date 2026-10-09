"""Bounded numerical calculus, finite differences and composite Simpson quadrature.

Numerical derivatives are estimates with truncation/roundoff error, NOT proofs.
"""
from math import isfinite, sqrt

class CalculusError(ValueError):
    pass

def num(x):
    if type(x) not in (float,int) or not isfinite(float(x)):
        raise CalculusError("Expected finite real")
    return float(x)

def _call(f,x):
    return num(f(x))

def derivative(f,x,h=1e-5):
    x,h=num(x),num(h)
    if h<=0:
        raise CalculusError("Positive step required")
    return (_call(f,x+h)-_call(f,x-h))/(2*h)

def gradient(f,x,h=1e-5):
    x=[num(v) for v in x]
    if not 1<=len(x)<=32:
        raise CalculusError("Expected dimension 1..32")
    h=num(h)
    if h<=0:
        raise CalculusError("Positive step required")
    g=[]
    for i in range(len(x)):
        plus=x[:];minus=x[:]
        plus[i]+=h;minus[i]-=h
        g.append((_call(f,plus)-_call(f,minus))/(2*h))
    return g

def jacobian(f,x,h=1e-5):
    x=[num(v) for v in x]
    if not 1<=len(x)<=32 or num(h)<=0:
        raise CalculusError("Invalid dimensions or step")
    baseline=[num(v) for v in f(x)]
    if not 1<=len(baseline)<=32:
        raise CalculusError("Output dimension out of bounds")
    rows=[[] for _ in baseline]
    for i in range(len(x)):
        plus=x[:];minus=x[:]
        plus[i]+=h;minus[i]-=h
        a,b=[num(v) for v in f(plus)],[num(v) for v in f(minus)]
        if len(a)!=len(b) or len(a)!=len(rows):
            raise CalculusError("Inconsistent output shape")
        for j in range(len(rows)):
            rows[j].append((a[j]-b[j])/(2*h))
    return rows

def hessian(f,x,h=1e-4):
    """Central second-order differences including symmetric mixed partials."""
    x=[num(v) for v in x]
    n=len(x);h=num(h)
    if not 1<=n<=20 or h<=0:
        raise CalculusError("Invalid dimensions or step")
    center=_call(f,x)
    out=[[0.]*n for _ in range(n)]
    for i in range(n):
        plus=x[:];minus=x[:]
        plus[i]+=h;minus[i]-=h
        out[i][i]=(_call(f,plus)-2*center+_call(f,minus))/h**2
        for j in range(i+1,n):
            vals=[]
            for si,sj in ((1,1),(1,-1),(-1,1),(-1,-1)):
                point=x[:];point[i]+=si*h;point[j]+=sj*h
                vals.append(_call(f,point))
            out[i][j]=(vals[0]-vals[1]-vals[2]+vals[3])/(4*h*h)
            out[j][i]=out[i][j]
    return out

def integrate_simpson(f,a,b,intervals=100):
    a,b=num(a),num(b)
    if type(intervals) is not int or intervals<2 or intervals>100000 or intervals%2:
        raise CalculusError("Simpson rule requires even intervals 2..100000")
    step=(b-a)/intervals
    total=_call(f,a)+_call(f,b)
    for i in range(1,intervals):
        total+=(4 if i%2 else 2)*_call(f,a+i*step)
    return step*total/3

def optimize_descent(f,start,rate=0.01,max_steps=100,tol=1e-6):
    """Bounded gradient descent; never declares global optimality."""
    x=[num(v) for v in start]
    rate,tol=num(rate),num(tol)
    if rate<=0 or tol<=0 or type(max_steps) is not int or not 1<=max_steps<=10000:
        raise CalculusError("Invalid optimizer settings")
    prev=_call(f,x)
    for step in range(max_steps):
        g=gradient(f,x)
        magnitude=sqrt(sum(z*z for z in g))
        if magnitude<tol:
            return {"x":x,"loss":prev,"steps":step,"status":"stationary_estimate"}
        # Armijo-like backtracking rejects uphill/unbounded moves.
        alpha=rate
        accepted=False
        for _ in range(24):
            trial=[v-alpha*d for v,d in zip(x,g)]
            try:
                new=_call(f,trial)
            except (CalculusError,OverflowError):
                new=float("inf")
            if new <= prev-1e-4*alpha*magnitude**2:
                x,prev=trial,new
                accepted=True
                break
            alpha*=0.5
        if not accepted:
            return {"x":x,"loss":prev,"steps":step,"status":"stalled"}
    return {"x":x,"loss":prev,"steps":max_steps,"status":"budget_exhausted"}
