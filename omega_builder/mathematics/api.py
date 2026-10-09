"""Allowlisted, offline mathematical computation; does not execute user code."""
from . import linear,logic,graph,probability

class MathAPIError(ValueError):
    pass

OPERATIONS = {
    "linear.add":(linear.add,("a","b")),
    "linear.multiply":(linear.mmul,("a","b")),
    "linear.transpose":(linear.transpose,("a",)),
    "linear.dot":(linear.dot,("a","b")),
    "linear.cross":(linear.cross,("a","b")),
    "linear.hadamard":(linear.hadamard,("a","b")),
    "linear.lu":(linear.lu,("a",)),
    "linear.qr":(linear.qr,("a",)),
    "linear.cholesky":(linear.cholesky,("a",)),
    "linear.determinant":(linear.determinant,("a",)),
    "linear.inverse":(linear.inverse,("a",)),
    "linear.solve":(linear.solve,("a","b")),
    "linear.solve_exact":(linear.solve_exact,("a","b")),
    "linear.trace":(linear.trace,("a",)),
    "linear.norm":(linear.norm,("a",)),
    "linear.distance":(linear.distance,("a","b")),
    "linear.cosine":(linear.cosine,("a","b")),
    "linear.svd":(linear.svd,("a",)),
    "logic.check_validity":(logic.check_validity,("formula",)),
    "logic.entails":(logic.entails,("premises","conclusion")),
    "graph.dijkstra":(graph.dijkstra,("adj","start","target")),
    "graph.topological_sort":(graph.topological_sort,("adj",)),
    "graph.laplacian":(graph.laplacian,("adj",)),
    "probability.bayes":(probability.bayes,("prior","likelihood_positive","likelihood_negative")),
    "probability.entropy":(probability.entropy,("probabilities",)),
    "probability.kl":(probability.kl,("p","q")),
    "probability.expectation":(probability.expectation,("values","probabilities")),
    "probability.variance":(probability.variance,("values","probabilities"))
}

def calculate(request):
    if not isinstance(request,dict) or set(request)!={"operation","args"}:
        raise MathAPIError("Request requires exactly: operation and args")
    op=request["operation"]
    if not isinstance(op,str) or op not in OPERATIONS:
        raise MathAPIError("Unsupported math operation")
    function,keys=OPERATIONS[op]
    kwargs=request["args"]
    if not isinstance(kwargs,dict) or set(kwargs)!=set(keys):
        raise MathAPIError("Wrong arguments: "+", ".join(keys))
    try:
        result=function(**kwargs)
    except (linear.MathError,logic.LogicError,graph.GraphError,
            probability.ProbabilityError,OverflowError,ZeroDivisionError) as exc:
        raise MathAPIError(str(exc)) from exc
    if op=="linear.lu":
        return {"P":result[0],"L":result[1],"U":result[2],"relation":"P*A=L*U (floating-point)"}
    if op=="linear.qr":
        return {"Q":result[0],"R":result[1],"relation":"A=Q*R (floating-point)"}
    if op=="linear.svd":
        return {"U":result[0],"singular_values":result[1],"V_transpose":result[2]}
    return {"operation":op,"result":result}
