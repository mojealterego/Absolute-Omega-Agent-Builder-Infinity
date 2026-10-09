"""Opt-in real ML algorithms. No pretend t-SNE/UMAP/autoencoder stubs.

LDA is supervised; its fitted projection can transform future samples.
t-SNE/UMAP below are exploratory *fit_transform* algorithms; embeddings
must never be mistaken for out-of-sample model evaluation without a protocol.
"""
from __future__ import annotations
from collections import Counter
from math import isfinite

class EmbeddingError(ValueError):
    pass

def _matrix(data,minimum=3,max_rows=2000,max_features=256):
    if not isinstance(data,(list,tuple)) or not minimum<=len(data)<=max_rows:
        raise EmbeddingError("Number of observations outside supported range")
    width=None
    output=[]
    for row in data:
        if not isinstance(row,(list,tuple)) or not 1<=len(row)<=max_features:
            raise EmbeddingError("Matrix must be rectangular with bounded dimensions")
        if width is None:
            width=len(row)
        if len(row)!=width:
            raise EmbeddingError("Ragged feature matrix")
        values=[]
        for item in row:
            if type(item) not in (int,float) or not isfinite(float(item)):
                raise EmbeddingError("Expected finite numerical features")
            values.append(float(item))
        output.append(values)
    return output

def _integer(value,minimum,maximum,name):
    if type(value) is not int or not minimum<=value<=maximum:
        raise EmbeddingError(f"{name} must be int in [{minimum}, {maximum}]")
    return value

def _numpy():
    try:
        import numpy as np
    except ImportError as exc:
        raise EmbeddingError("Requires pip install '.[math]' (NumPy)") from exc
    return np

def lda_fit(train_matrix, train_labels, components=1):
    """Fit Fisher Linear Discriminant on TRAIN exclusively."""
    data=_matrix(train_matrix,minimum=4)
    if not isinstance(train_labels,(list,tuple)) or len(train_labels)!=len(data):
        raise EmbeddingError("LDA labels must match training observations")
    if any(type(label) not in (str,int,bool) for label in train_labels):
        raise EmbeddingError("LDA labels must be scalar categorical")
    counts=Counter((type(item).__name__,item) for item in train_labels)
    if not 2<=len(counts)<=32 or min(counts.values())<2:
        raise EmbeddingError("LDA requires >=2 classes with >=2 observations each")
    _integer(components,1,min(len(counts)-1,len(data[0])),"components")
    try:
        from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    except ImportError as exc:
        raise EmbeddingError("LDA requires pip install '.[ml]' (scikit-learn)") from exc
    import numpy as np
    estimator=LinearDiscriminantAnalysis(n_components=components,solver="svd")
    try:
        estimator.fit(np.asarray(data),list(train_labels))
    except (ValueError, TypeError) as exc:
        raise EmbeddingError(str(exc)) from exc
    mean=estimator.xbar_.tolist()
    basis=estimator.scalings_[:,:components].T.tolist()
    return {"fit_scope":"training_only","mean":mean,"components":basis,
            "classes":[str(x) for x in estimator.classes_],
            "fit_rows":len(data),"method":"sklearn_linear_discriminant_svd"}

def lda_transform(matrix,model):
    """Transform with the fitted TRAIN LDA basis; do not refit test data."""
    if not isinstance(model,dict) or model.get("fit_scope")!="training_only":
        raise EmbeddingError("Expected fitted train-only LDA model")
    means=model.get("mean")
    basis=model.get("components")
    if not isinstance(means,list) or not means or not isinstance(basis,list) or not basis:
        raise EmbeddingError("Invalid LDA model")
    data=_matrix(matrix,minimum=1,max_rows=100000)
    if len(data[0])!=len(means) or any(not isinstance(vec,list) or len(vec)!=len(means) for vec in basis):
        raise EmbeddingError("Inconsistent LDA dimensions")
    return [[sum((x-float(mu))*float(w) for x,mu,w in zip(row,means,vec))
             for vec in basis] for row in data]

def tsne_embedding(matrix,dimensions=2,perplexity=5.0,seed=0):
    """Run real sklearn t-SNE; *not* a fitted reusable feature transformer."""
    data=_matrix(matrix,minimum=4,max_rows=2000)
    _integer(dimensions,1,3,"dimensions")
    _integer(seed,0,2147483647,"seed")
    if type(perplexity) not in (int,float) or not isfinite(float(perplexity)):
        raise EmbeddingError("Perplexity must be finite")
    if not 1<=perplexity<len(data):
        raise EmbeddingError("Perplexity must be 1 <= p < n")
    try:
        from sklearn.manifold import TSNE
    except ImportError as exc:
        raise EmbeddingError("t-SNE requires pip install '.[ml]'") from exc
    try:
        result=TSNE(n_components=dimensions,perplexity=float(perplexity),init="random",
                    learning_rate="auto",max_iter=500,random_state=seed).fit_transform(data)
    except (TypeError,ValueError) as exc:
        raise EmbeddingError(str(exc)) from exc
    return {"embedding":result.tolist(),"method":"sklearn_tsne",
            "scope":"exploratory_fit_transform_only","seed":seed}

def umap_embedding(matrix,dimensions=2,neighbors=10,seed=0):
    """Run real umap-learn UMAP (optional package); no global-distance guarantee."""
    data=_matrix(matrix,minimum=4,max_rows=2000)
    _integer(dimensions,1,10,"dimensions")
    _integer(neighbors,2,len(data)-1,"neighbors")
    _integer(seed,0,2147483647,"seed")
    try:
        import umap
    except ImportError as exc:
        raise EmbeddingError("UMAP requires pip install '.[umap]' (umap-learn)") from exc
    try:
        model=umap.UMAP(n_components=dimensions,n_neighbors=neighbors,
                        random_state=seed,transform_seed=seed)
        coords=model.fit_transform(data)
    except (TypeError,ValueError) as exc:
        raise EmbeddingError(str(exc)) from exc
    return {"embedding":coords.tolist(),"method":"umap_learn",
            "scope":"exploratory_fit_transform_only","seed":seed}

def autoencoder_fit(train_matrix,latent_dim=2,epochs=100,rate=0.01,seed=0):
    """Actual bounded 1-hidden-layer tanh autoencoder trained with full-batch GD.

    Educational numerical baseline for normalized numerical inputs; no SOTA,
    no feature semantic guarantee. No automatic deployment or model mutation.
    """
    data=_matrix(train_matrix,minimum=4,max_rows=5000,max_features=64)
    d=len(data[0])
    _integer(latent_dim,1,d-1,"latent_dim")
    _integer(epochs,1,500,"epochs")
    _integer(seed,0,2147483647,"seed")
    if type(rate) not in (int,float) or not isfinite(float(rate)) or not 0<rate<=0.1:
        raise EmbeddingError("Learning rate must be in (0,0.1]")
    np=_numpy()
    x=np.asarray(data,dtype=np.float64)
    n=x.shape[0]
    if np.max(np.abs(x))>1000:
        raise EmbeddingError("Normalize features before training the reference autoencoder")
    rng=np.random.default_rng(seed)
    w1=rng.normal(0,0.1,(d,latent_dim))
    b1=np.zeros(latent_dim)
    w2=rng.normal(0,0.1,(latent_dim,d))
    b2=np.zeros(d)
    for _ in range(epochs):
        latent=np.tanh(x@w1+b1)
        prediction=latent@w2+b2
        error=prediction-x
        doutput=2*error/(n*d)
        gw2=latent.T@doutput
        gb2=doutput.sum(axis=0)
        dhidden=(doutput@w2.T)*(1-latent*latent)
        gw1=x.T@dhidden
        gb1=dhidden.sum(axis=0)
        gradients=(gw1,gb1,gw2,gb2)
        norm=np.sqrt(sum(float(np.sum(g*g)) for g in gradients))
        if not np.isfinite(norm):
            raise EmbeddingError("Unstable optimization / non-finite gradient")
        factor=min(1.,10./max(norm,1e-12))
        w1-=rate*factor*gw1
        b1-=rate*factor*gb1
        w2-=rate*factor*gw2
        b2-=rate*factor*gb2
    loss=float(np.mean((np.tanh(x@w1+b1)@w2+b2-x)**2))
    if not isfinite(loss):
        raise EmbeddingError("Autoencoder failed to converge to finite result")
    return {"fit_scope":"training_only","method":"numpy_tanh_autoencoder",
            "weights_enc":w1.tolist(),"bias_enc":b1.tolist(),
            "weights_dec":w2.tolist(),"bias_dec":b2.tolist(),
            "train_mse":loss,"epochs":epochs,"seed":seed,"fit_rows":n}

def autoencoder_transform(matrix,model):
    if not isinstance(model,dict) or model.get("fit_scope")!="training_only" or model.get("method")!="numpy_tanh_autoencoder":
        raise EmbeddingError("Not a fitted autoencoder model")
    np=_numpy()
    x=np.asarray(_matrix(matrix,minimum=1,max_rows=100000,max_features=64))
    w=np.asarray(model["weights_enc"],dtype=float)
    b=np.asarray(model["bias_enc"],dtype=float)
    if w.ndim!=2 or x.shape[1]!=w.shape[0] or b.shape!=(w.shape[1],) or not np.isfinite(w).all() or not np.isfinite(b).all():
        raise EmbeddingError("Invalid autoencoder dimensions or values")
    return np.tanh(x@w+b).tolist()

def autoencoder_reconstruct(matrix,model):
    np=_numpy()
    z=np.asarray(autoencoder_transform(matrix,model),dtype=float)
    w=np.asarray(model.get("weights_dec"),dtype=float)
    b=np.asarray(model.get("bias_dec"),dtype=float)
    if w.ndim!=2 or w.shape[0]!=z.shape[1] or b.shape!=(w.shape[1],) or not np.isfinite(w).all() or not np.isfinite(b).all():
        raise EmbeddingError("Invalid autoencoder decoder")
    return (z@w+b).tolist()
