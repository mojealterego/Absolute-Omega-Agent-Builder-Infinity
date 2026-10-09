"""Reference numerical and exact linear algebra (small, bounded matrices).

Floating-point routines are NOT formal proofs. For exact rational Ax=b use
solve_exact() with fractions; results include a checked algebraic certificate.
Production large-scale SVD needs NumPy (optional math extra).
"""
from fractions import Fraction
from math import isfinite, sqrt, fsum
from typing import Sequence


class MathError(ValueError):
    pass


def scalar(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise MathError("Expected a finite real scalar")
    try:
        y = float(x)
    except (OverflowError, ValueError) as exc:
        raise MathError("Scalar out of floating point range") from exc
    if not isfinite(y):
        raise MathError("Nonfinite scalar")
    return y


def vec(v):
    if not isinstance(v, (tuple, list)) or not 1 <= len(v) <= 64:
        raise MathError("Expected vector of 1..64 elements")
    return [scalar(x) for x in v]


def mat(a):
    if not isinstance(a, (tuple, list)) or not 1 <= len(a) <= 64:
        raise MathError("Expected 1..64 rows")
    if not isinstance(a[0], (tuple, list)) or not 1 <= len(a[0]) <= 64:
        raise MathError("Expected 1..64 columns")
    n = len(a[0])
    if any(not isinstance(row, (tuple, list)) or len(row) != n for row in a):
        raise MathError("Ragged matrix")
    return [[scalar(x) for x in row] for row in a]


def square(a):
    a = mat(a)
    if len(a) != len(a[0]):
        raise MathError("Square matrix required")
    return a


def identity(n):
    if type(n) is not int or not 1 <= n <= 64:
        raise MathError("Identity dimension out of bounds")
    return [[float(i == j) for j in range(n)] for i in range(n)]


def transpose(a):
    return [list(row) for row in zip(*mat(a))]


def add(a, b):
    a, b = mat(a), mat(b)
    if (len(a), len(a[0])) != (len(b), len(b[0])):
        raise MathError("Dimension mismatch")
    return [[x + y for x, y in zip(p, q)] for p, q in zip(a, b)]


def hadamard(a, b):
    a, b = mat(a), mat(b)
    if (len(a), len(a[0])) != (len(b), len(b[0])):
        raise MathError("Dimension mismatch")
    return [[x * y for x, y in zip(p, q)] for p, q in zip(a, b)]


def mmul(a, b):
    a, b = mat(a), mat(b)
    if len(a[0]) != len(b):
        raise MathError("Inner dimension mismatch")
    return [[fsum(x * y for x, y in zip(row, col)) for col in zip(*b)]
            for row in a]


def trace(a):
    a = square(a)
    return fsum(a[i][i] for i in range(len(a)))


def dot(a, b):
    a, b = vec(a), vec(b)
    if len(a) != len(b):
        raise MathError("Different vector lengths")
    return fsum(x * y for x, y in zip(a, b))


def cross(a, b):
    a, b = vec(a), vec(b)
    if len(a) != 3 or len(b) != 3:
        raise MathError("Cross product requires 3D vectors")
    return [a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0]]


def norm(a, kind=2):
    a = vec(a)
    if kind == 1:
        return fsum(abs(x) for x in a)
    if kind == 2:
        return sqrt(fsum(x*x for x in a))
    if kind in ("inf", float("inf")):
        return max(abs(x) for x in a)
    raise MathError("Only L1, L2 and Linf norms supported")


def distance(a, b, kind=2):
    a, b = vec(a), vec(b)
    if len(a) != len(b):
        raise MathError("Different dimensions")
    return norm([x-y for x, y in zip(a, b)], kind)


def cosine(a, b):
    a, b = vec(a), vec(b)
    if len(a) != len(b):
        raise MathError("Different dimensions")
    denom = norm(a) * norm(b)
    if denom == 0:
        raise MathError("Undefined for a zero vector")
    return max(-1., min(1., dot(a, b)/denom))


def lu(a, eps=1e-12):
    """PA=LU, partial row pivoting. Returns (P,L,U)."""
    a = square(a)
    n = len(a)
    u = [row[:] for row in a]
    p, low = identity(n), identity(n)
    scale = max(abs(x) for row in u for x in row)
    if scale == 0:
        raise MathError("Singular matrix")
    for k in range(n):
        pivot_row = max(range(k, n), key=lambda r: abs(u[r][k]))
        if abs(u[pivot_row][k]) <= eps*scale:
            raise MathError("Singular or numerically ill-conditioned matrix")
        if pivot_row != k:
            u[k], u[pivot_row] = u[pivot_row], u[k]
            p[k], p[pivot_row] = p[pivot_row], p[k]
            for j in range(k):
                low[k][j], low[pivot_row][j] = low[pivot_row][j], low[k][j]
        for i in range(k+1, n):
            f = u[i][k]/u[k][k]
            low[i][k] = f
            u[i][k] = 0.
            for j in range(k+1, n):
                u[i][j] -= f*u[k][j]
    return p, low, u


def determinant(a):
    a = square(a)
    if len(a) == 1:
        return a[0][0]
    try:
        p, _, u = lu(a)
    except MathError as exc:
        if "Singular" in str(exc):
            return 0.0
        raise
    # permutation determinant is +1 or -1, exact integer via permutation parity
    seq = [row.index(1.) for row in p]
    flips = sum(seq[i] > seq[j] for i in range(len(seq)) for j in range(i+1,len(seq)))
    det = -1. if flips % 2 else 1.
    for i in range(len(u)):
        det *= u[i][i]
    return det


def solve(a, b):
    p, low, upper = lu(a)
    b = vec(b)
    n = len(p)
    if len(b) != n:
        raise MathError("Right hand dimension mismatch")
    pb = [dot(row, b) for row in p]
    y = [0.]*n
    for i in range(n):
        y[i] = pb[i] - fsum(low[i][j]*y[j] for j in range(i))
    x = [0.]*n
    for i in range(n-1, -1, -1):
        x[i] = (y[i] - fsum(upper[i][j]*x[j] for j in range(i+1,n))) / upper[i][i]
    return x


def inverse(a):
    a = square(a)
    n = len(a)
    return transpose([solve(a, b) for b in identity(n)])


def qr(a):
    """Thin Householder QR for real m>=n; returns Q (m*n) and R (n*n)."""
    a = mat(a)
    m, n = len(a), len(a[0])
    if m < n:
        raise MathError("Thin QR requires rows >= columns")
    r = [row[:] for row in a]
    q = identity(m)
    for k in range(n):
        x = [r[i][k] for i in range(k,m)]
        length = sqrt(fsum(z*z for z in x))
        if length < 1e-13:
            raise MathError("Rank deficient: cannot build full-column Q")
        alpha = -length if x[0] >= 0 else length
        x[0] -= alpha
        den = sqrt(fsum(z*z for z in x))
        v = [z/den for z in x]
        for j in range(k,n):
            proj = 2*fsum(v[i-k]*r[i][j] for i in range(k,m))
            for i in range(k,m):
                r[i][j] -= proj*v[i-k]
        for i in range(m):
            proj = 2*fsum(q[i][k+t]*v[t] for t in range(m-k))
            for t in range(m-k):
                q[i][k+t] -= proj*v[t]
    return [row[:n] for row in q], [row[:n] for row in r[:n]]


def cholesky(a, tol=1e-12):
    """A=LL^T for a real symmetric positive definite A."""
    a = square(a)
    n = len(a)
    if any(abs(a[i][j]-a[j][i]) > tol * max(1.,abs(a[i][j]),abs(a[j][i]))
           for i in range(n) for j in range(n)):
        raise MathError("Not symmetric")
    low = [[0.]*n for _ in range(n)]
    for i in range(n):
        for j in range(i+1):
            t = a[i][j] - fsum(low[i][k]*low[j][k] for k in range(j))
            if i == j:
                if t <= tol:
                    raise MathError("Not positive definite")
                low[i][j] = sqrt(t)
            else:
                low[i][j] = t/low[j][j]
    return low


def symmetric(a, tol=1e-12):
    a = square(a)
    return all(abs(a[i][j]-a[j][i]) <= tol for i in range(len(a)) for j in range(len(a)))


def orthogonal(a, tol=1e-10):
    a = square(a)
    prod = mmul(transpose(a),a)
    ident = identity(len(a))
    return all(abs(prod[i][j]-ident[i][j]) <= tol for i in range(len(a))
               for j in range(len(a)))


def diagonal(a):
    a = square(a)
    return all(a[i][j] == 0 for i in range(len(a)) for j in range(len(a)) if i != j)


def svd(a):
    """Actual thin SVD using optional NumPy LAPACK; no fake fallback."""
    a = mat(a)
    try:
        import numpy as np
    except ImportError as exc:
        raise MathError("SVD requires optional 'math' extra: pip install '.[math]'") from exc
    u,s,vt = np.linalg.svd(np.asarray(a,dtype=float),full_matrices=False)
    return u.tolist(),s.tolist(),vt.tolist()


def solve_exact(a, b):
    """Rational Gauss-Jordan. Returns a machine-checkable equality witness."""
    if not isinstance(a,(list,tuple)) or not 1 <= len(a) <= 16:
        raise MathError("Rational solve: 1..16 rows")
    n = len(a)
    if any(not isinstance(r,(tuple,list)) or len(r) != n for r in a):
        raise MathError("Rational solve: square matrix required")
    if not isinstance(b,(list,tuple)) or len(b)!=n:
        raise MathError("Rational solve: b dimension")
    def fr(v):
        if isinstance(v,bool) or not isinstance(v,(int,str,Fraction)):
            raise MathError("Exact entries must be integers or rational strings")
        try:
            return Fraction(v)
        except (TypeError,ValueError,ZeroDivisionError) as exc:
            raise MathError("Not a rational value") from exc
    a0=[[fr(x) for x in row] for row in a]
    b0=[fr(x) for x in b]
    aug=[row[:] + [rhs] for row,rhs in zip(a0,b0)]
    for k in range(n):
        p=next((i for i in range(k,n) if aug[i][k]),None)
        if p is None:
            raise MathError("Singular: no unique rational solution")
        aug[k],aug[p]=aug[p],aug[k]
        div=aug[k][k]
        aug[k]=[v/div for v in aug[k]]
        for i in range(n):
            if i==k:
                continue
            f=aug[i][k]
            aug[i]=[z-f*x for z,x in zip(aug[i],aug[k])]
    x=[row[-1] for row in aug]
    if any(sum(v*y for v,y in zip(row,x)) != rhs for row,rhs in zip(a0,b0)):
        raise AssertionError("Exact certificate did not verify")
    return {"solution":[str(v) for v in x], "certificate":"A*x == b in rational arithmetic",
            "verified":True, "proof_scope":"provided finite rational system"}
