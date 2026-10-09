"""Allowlisted, offline mathematical computation; does not execute user code."""
from . import linear,logic,graph,probability,statistics,information
from .. import preprocessing

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
    "probability.variance":(probability.variance,("values","probabilities")),
    "statistics.pearson":(statistics.pearson,("x","y")),
    "statistics.covariance":(statistics.covariance,("x","y")),
    "statistics.sample_mean":(statistics.sample_mean,("values",)),
    "statistics.sample_variance":(statistics.sample_variance,("values",)),
    "statistics.bernoulli_pmf":(statistics.bernoulli_pmf,("k","p")),
    "statistics.binomial_pmf":(statistics.binomial_pmf,("k","n","p")),
    "statistics.poisson_pmf":(statistics.poisson_pmf,("k","rate")),
    "statistics.normal_cdf":(statistics.normal_cdf,("x",)),
    "statistics.exponential_pdf":(statistics.exponential_pdf,("x","rate")),
    "statistics.exponential_cdf":(statistics.exponential_cdf,("x","rate")),
    "statistics.uniform_pdf":(statistics.uniform_pdf,("x","low","high")),
    "statistics.beta_pdf":(statistics.beta_pdf,("x","alpha","beta")),
    "statistics.gamma_pdf":(statistics.gamma_pdf,("x","shape","scale")),
    "statistics.mle_gaussian":(statistics.mle_gaussian,("observations",)),
    "statistics.mle_bernoulli":(statistics.mle_bernoulli,("observations",)),
    "statistics.map_bernoulli_beta":(statistics.map_bernoulli_beta,("observations","alpha","beta")),
    "statistics.posterior_mean_bernoulli_beta":(statistics.posterior_mean_bernoulli_beta,("observations","alpha","beta")),
    "statistics.markov_step":(statistics.markov_step,("state","transition")),
    "statistics.random_walk":(statistics.random_walk,("steps","seed")),
    "statistics.monte_carlo_pi":(statistics.monte_carlo_pi,("samples","seed")),
    "information.conditional_entropy":(information.conditional_entropy_y_given_x,("joint",)),
    "information.mutual_information":(information.mutual_information,("joint",)),
    "information.joint_entropy":(information.joint_entropy,("joint",)),
    "information.snr_db":(information.signal_to_noise_db,("signal_power","noise_power")),
    "information.shannon_hartley":(information.shannon_hartley,("bandwidth_hz","snr_linear")),
    "information.huffman_codes":(information.huffman_codes,("symbol_counts",)),
    "information.huffman_encode":(information.huffman_encode,("symbols","codes")),
    "information.huffman_decode":(information.huffman_decode,("bits","codes")),
    "preprocessing.deduplicate":(preprocessing.deduplicate_rows,("rows",)),
    "preprocessing.fit_numeric":(preprocessing.fit_numeric,("rows","column")),
    "preprocessing.transform_numeric":(preprocessing.transform_numeric,("rows","model")),
    "preprocessing.one_hot_fit":(preprocessing.one_hot_fit,("rows","column")),
    "preprocessing.one_hot_transform":(preprocessing.one_hot_transform,("rows","model")),
    "preprocessing.iqr_bounds":(preprocessing.iqr_bounds,("values",)),
    "preprocessing.outlier_flags":(preprocessing.outlier_flags,("values","bounds")),
    "preprocessing.pca_fit":(preprocessing.pca_fit,("matrix","n_components")),
    "preprocessing.pca_transform":(preprocessing.pca_transform,("matrix","model"))
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
            probability.ProbabilityError,preprocessing.PreprocessingError,
            OverflowError,ZeroDivisionError) as exc:
        raise MathAPIError(str(exc)) from exc
    if op=="linear.lu":
        return {"P":result[0],"L":result[1],"U":result[2],"relation":"P*A=L*U (floating-point)"}
    if op=="linear.qr":
        return {"Q":result[0],"R":result[1],"relation":"A=Q*R (floating-point)"}
    if op=="linear.svd":
        return {"U":result[0],"singular_values":result[1],"V_transpose":result[2]}
    return {"operation":op,"result":result}
