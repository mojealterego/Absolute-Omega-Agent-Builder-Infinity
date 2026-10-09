"""Finite symbolic proof checking, never a claim of universal theorem proving.

A formula is an immutable tuple e.g. ('implies', ('var','p'), ('var','q')).
All validity claims are exhaustive ONLY over the declared finite domain.
"""
from itertools import product

class LogicError(ValueError):
    pass

def _variables(expr, depth=0):
    if depth > 32 or not isinstance(expr,(tuple,list)) or not expr:
        raise LogicError("Malformed formula or depth exceeded")
    op=expr[0]
    if op=="var" and len(expr)==2 and isinstance(expr[1],str) and expr[1]:
        return {expr[1]}
    if op=="const" and len(expr)==2 and type(expr[1]) is bool:
        return set()
    if op=="not" and len(expr)==2:
        return _variables(expr[1],depth+1)
    if op in ("and","or","xor","implies","iff") and len(expr)==3:
        return _variables(expr[1],depth+1)|_variables(expr[2],depth+1)
    raise LogicError("Unsupported logical operator")

def evaluate(expr,valuation):
    """Propositional Boolean formula with explicit, untrusted-data-safe grammar."""
    vars_=_variables(expr)
    if any(k not in valuation or type(valuation[k]) is not bool for k in vars_):
        raise LogicError("Missing or nonboolean valuation")
    def run(ex):
        op=ex[0]
        if op=="var":
            return valuation[ex[1]]
        if op=="const":
            return ex[1]
        if op=="not":
            return not run(ex[1])
        l=run(ex[1])
        r=run(ex[2])
        return {"and":lambda:l and r,"or":lambda:l or r,
                "xor":lambda:l != r,"implies":lambda:not l or r,
                "iff":lambda:l == r}[op]()
    return run(expr)

def check_validity(formula,max_vars=12):
    """Exhaustive finite Boolean assignments: valid, satisfiable, counterexample."""
    v=sorted(_variables(formula))
    if len(v)>max_vars:
        raise LogicError("Truth table combinatorial budget exceeded")
    satisfiable=False
    checked=0
    counterexample=None
    for values in product((False,True),repeat=len(v)):
        val=dict(zip(v,values))
        outcome=evaluate(formula,val)
        checked+=1
        satisfiable=satisfiable or outcome
        if not outcome and counterexample is None:
            counterexample=val
    return {"valid":counterexample is None,"satisfiable":satisfiable,
            "counterexample":counterexample,"assignments_checked":checked,
            "scope":"exhaustive_propositional_truth_table"}

def entails(premises,conclusion):
    """Finite Boolean semantic entailment: premises |= conclusion."""
    if not isinstance(premises,(list,tuple)):
        raise LogicError("Premises must be a list")
    formula=conclusion
    for premise in premises:
        formula=("implies",premise,formula)
    return check_validity(formula)

def finite_forall(domain,predicate):
    """Finite-domain quantifier; predicate is trusted caller logic, no eval."""
    domain=tuple(domain)
    if len(domain)>10000:
        raise LogicError("Domain too large")
    return all(bool(predicate(x)) for x in domain)

def finite_exists(domain,predicate):
    domain=tuple(domain)
    if len(domain)>10000:
        raise LogicError("Domain too large")
    return any(bool(predicate(x)) for x in domain)
