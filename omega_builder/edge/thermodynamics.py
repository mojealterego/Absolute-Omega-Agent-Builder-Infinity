"""Ising-chain Gibbs CPU reference and optional actual THRML/JAX interface.

Reference sampler updates spins with conditional heat-bath probabilities.
This is NOT an Extropic TSU hardware connection.
"""
from math import exp, isfinite
from random import Random


class ThermodynamicError(ValueError):
    pass


def _validate(n, coupling, beta, warmup, samples, seed):
    if type(n) is not int or not 2<=n<=128:
        raise ThermodynamicError("Expected 2..128 spins")
    if any(type(v) not in (int,float) or not isfinite(float(v)) for v in (coupling,beta)):
        raise ThermodynamicError("Coupling and beta must be finite")
    if beta<=0 or abs(coupling)>10 or beta>100:
        raise ThermodynamicError("Parameter bounds exceeded")
    for value,lo,hi,name in ((warmup,0,10000,"warmup"),(samples,1,5000,"samples"),
                             (seed,0,2147483647,"seed")):
        if type(value) is not int or not lo<=value<=hi:
            raise ThermodynamicError(f"Invalid {name}")


def ising_energy(spins,coupling=0.5,beta=1.0):
    """Energy of chain with spins encoded as ±1; beta included in energy."""
    if not isinstance(spins,(list,tuple)) or not 2<=len(spins)<=128 or any(type(s) is not int or s not in (-1,1) for s in spins):
        raise ThermodynamicError("Spins must be +/-1 integers")
    if any(type(v) not in (int,float) or not isfinite(float(v)) for v in (coupling,beta)):
        raise ThermodynamicError("Invalid Ising parameters")
    return -float(beta)*float(coupling)*sum(a*b for a,b in zip(spins,spins[1:]))


def cpu_gibbs_reference(n=5,coupling=0.5,beta=1.0,warmup=100,samples=100,seed=42):
    """Actual seeded Ising-chain heat-bath sampling, returned as +/-1 spins."""
    _validate(n,coupling,beta,warmup,samples,seed)
    random=Random(seed)
    spins=[1 if random.getrandbits(1) else -1 for _ in range(n)]
    out=[]
    for sweep in range(warmup+samples):
        # Red/black colouring: neighbours cannot occupy the same update block.
        for parity in (0,1):
            for i in range(parity,n,2):
                neighbour=(spins[i-1] if i>0 else 0)+(spins[i+1] if i+1<n else 0)
                field=2*float(beta)*float(coupling)*neighbour
                # Overflow-safe sigmoid(field).
                if field>=0:
                    p=1/(1+exp(-field))
                else:
                    e=exp(field)
                    p=e/(1+e)
                spins[i]=1 if random.random()<p else -1
        if sweep>=warmup:
            out.append(spins[:])
    return {"backend":"cpu_gibbs_reference","spins":out,"n":n,"samples":samples,
            "seed":seed,"hardware_accelerated":False}


def run_thrml_ising_chain(n=5,coupling=0.5,beta=1.0,warmup=100,samples=100,seed=42):
    """Real THRML IsingSamplingProgram. Python-JAX backend; no TSU claim.

    Mirrors THRML quickstart, including the *required* state_clamp=[] and
    nodes_to_sample=[Block(nodes)] parameters omitted in user's snippet.
    """
    _validate(n,coupling,beta,warmup,samples,seed)
    try:
        import jax
        import jax.numpy as jnp
        from thrml import SpinNode, Block, SamplingSchedule, sample_states
        from thrml.models import IsingEBM,IsingSamplingProgram,hinton_init
    except ImportError as exc:
        raise ThermodynamicError("Requires optional JAX and THRML (pip install '.[thermodynamic]')") from exc
    nodes=[SpinNode() for _ in range(n)]
    edges=[(nodes[i],nodes[i+1]) for i in range(n-1)]
    model=IsingEBM(nodes,edges,jnp.zeros((n,)),
                   jnp.ones((n-1,))*coupling,jnp.array(beta))
    free_blocks=[Block(nodes[::2]),Block(nodes[1::2])]
    program=IsingSamplingProgram(model,free_blocks,clamped_blocks=[])
    initial_key,sampling_key=jax.random.split(jax.random.key(seed),2)
    init_state=hinton_init(initial_key,model,free_blocks,())
    schedule=SamplingSchedule(n_warmup=warmup,n_samples=samples,steps_per_sample=2)
    actual=sample_states(sampling_key,program,schedule,init_state,[],[Block(nodes)])
    # Expose the numeric result as an opaque tensor converted into JSON-ready
    # shape. THRML returns a list of sampled Block states.
    return {"backend":"jax_thrml","sample_blocks":[jax.device_get(a).tolist() for a in actual],
            "samples_requested":samples,"hardware_attested":False,
            "note":"JAX runtime, not evidence of a physical thermodynamic coprocessor"}
