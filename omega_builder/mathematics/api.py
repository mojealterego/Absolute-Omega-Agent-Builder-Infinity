"""Allowlisted, offline mathematical computation; does not execute user code."""
from . import linear,logic,graph,probability,statistics,information
from .. import preprocessing, ml_validation, ml_embeddings, ml_visualization, ml_governance

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
    "statistics.spearman":(statistics.spearman,("x","y")),
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
    "preprocessing.pca_transform":(preprocessing.pca_transform,("matrix","model")),
    "validation.split_indices":(ml_validation.split_indices,("n","validation_ratio","test_ratio","seed","labels")),
    "validation.kfold_indices":(ml_validation.kfold_indices,("n","folds","seed","labels")),
    "validation.leave_one_out":(ml_validation.leave_one_out,("n",)),
    "validation.classification_report":(ml_validation.classification_report,("truth","predicted")),
    "validation.ks_distance":(ml_validation.ks_distance,("reference","current")),
    "validation.psi":(ml_validation.psi,("reference","current","bins")),
    "validation.smote_train":(ml_validation.smote_train,("matrix","labels","neighbors","seed")),
    "validation.random_undersample_train":(ml_validation.random_undersample_train,("matrix","labels","seed")),
    "validation.random_oversample_train":(ml_validation.random_oversample_train,("matrix","labels","seed")),
    "validation.numeric_noise_augment_train":(ml_validation.numeric_noise_augment_train,("matrix","std","seed")),
    "validation.synthetic_gaussian_reference":(ml_validation.synthetic_gaussian_reference,("means","standard_deviations","n","seed")),
    "validation.active_learning_uncertainty":(ml_validation.active_learning_uncertainty,("probabilities","top_k")),
    "embeddings.lda_fit":(ml_embeddings.lda_fit,("train_matrix","train_labels","components")),
    "embeddings.lda_transform":(ml_embeddings.lda_transform,("matrix","model")),
    "embeddings.tsne":(ml_embeddings.tsne_embedding,("matrix","dimensions","perplexity","seed")),
    "embeddings.umap":(ml_embeddings.umap_embedding,("matrix","dimensions","neighbors","seed")),
    "embeddings.autoencoder_fit":(ml_embeddings.autoencoder_fit,("train_matrix","latent_dim","epochs","rate","seed")),
    "embeddings.autoencoder_transform":(ml_embeddings.autoencoder_transform,("matrix","model")),
    "embeddings.autoencoder_reconstruct":(ml_embeddings.autoencoder_reconstruct,("matrix","model")),
    "visualization.histogram":(ml_visualization.histogram,("values","bins")),
    "visualization.boxplot_summary":(ml_visualization.boxplot_summary,("values",)),
    "visualization.scatter":(ml_visualization.scatter_points,("x","y")),
    "visualization.heatmap":(ml_visualization.heatmap_matrix,("rows",)),
    "governance.dataset_quality":(ml_governance.dataset_quality,("rows",)),
    "governance.split_overlap":(ml_governance.split_overlap,("train","validation","test")),
    "governance.weak_supervision":(ml_governance.weak_supervision,("rows","column","label_keywords")),
    "governance.classification_conflicts":(ml_governance.classification_conflicts,("features","labels")),
    "governance.concept_drift_report":(ml_governance.concept_drift_report,("previous_true","previous_pred","current_true","current_pred"))
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
            ml_validation.ValidationError,ml_embeddings.EmbeddingError,
            ml_governance.GovernanceError,
            OverflowError,ZeroDivisionError) as exc:
        raise MathAPIError(str(exc)) from exc
    if op=="linear.lu":
        return {"P":result[0],"L":result[1],"U":result[2],"relation":"P*A=L*U (floating-point)"}
    if op=="linear.qr":
        return {"Q":result[0],"R":result[1],"relation":"A=Q*R (floating-point)"}
    if op=="linear.svd":
        return {"U":result[0],"singular_values":result[1],"V_transpose":result[2]}
    return {"operation":op,"result":result}
