# Edge Fabric: Mojo, THRML/JAX, Lean 4, Zenoh, TorchHD

Status: **reference implementations + opt-in library adapters; NOT deployed hardware.** Project: Absolute-Omega-Agent-Builder-Infinity. Branch: main. Zeus remains ON_HOLD_AWAITING_USER_MATERIAL.

## Layer contracts

| Layer | Source | Reality/evidence |
|---|---|---|
| Cognitive tensor | `omega_builder/edge/tensor_core.py` | CPU float32 contiguous `array('f')`, length <=1,000,000; dimensional and finite validation, staged atomic updates. |
| Mojo | `examples/mojo/cognitive_tensor.mojo` | Mojo reference rewritten to modern `out self`/`mut self`, `List[Float32]`; UNCOMPILED on GitHub CI (Mojo SDK absent). No reference to non-existent `Tensor(dim)`. |
| Physical routing | `hardware_dispatch_plan` | Photonic Passage L20 and ICE40 FPGA return `UNAVAILABLE` (no SDK, entitlement, attestation, driver, serial link, telemetry or power measurements). |
| Thermodynamics | `omega_builder/edge/thermodynamics.py` | Real seeded Ising chain CPU heat-bath Gibbs reference, energy `-beta*J*Σ s_i*s_(i+1)`. Optional real `thrml`/`jax` run with odd/even blocks and complete documented sampling call. NO TSU connectivity. |
| Hyperdimensional VSA | `omega_builder/edge/hdc.py` | Reproducible bipolar bind/unbind and exact single-pair retrieval; optional `torchhd.random`, `hash_table`, `inverse`, `bind`, cosine similarity (approximate multi-pair retrieval). |
| Communication | `omega_builder/edge/mesh.py` | Opt-in Zenoh 1.x session, specific allowlisted telemetry topic, HMAC-SHA256 message, freshness/replay checks; no remote code execution and no implicit socket creation. Network ACL, encryption and identity remain infrastructure tasks. |
| Safety evidence | `omega_builder/edge/mutation_gate.py` | HMAC-signed manifest, SHA-256 artifact/base hashes, tests/scanner/flag/score filters. Only `ELIGIBLE_FOR_SEPARATE_HUMAN_DEPLOYMENT`; NEVER executes a mutation. Self-reported metadata must be independently audited. |
| Formal property | `specs/MutationGate.lean` | Lean 4 proof source models declared predicate; excludes false safety flag, low score, failed tests and scan from that predicate. **Not yet compiled/checked by Lean mathlib CI**. |

## Install

~~~sh
python -m unittest discover -s tests -v
pip install '.[thermodynamic]' # JAX/THRML, backend support subject to platform
pip install '.[hdc]'           # torch, torchhd
pip install '.[mesh]'          # eclipse-zenoh (import zenoh)
~~~

Optional runtime paths are lazily imported. Standard CI exercises the pure-Python reference (does not install THRML/JAX, TorchHD or Zenoh). A dedicated optional CI matrix with pinned builds and real devices is required before claiming hardware acceleration or production readiness.

## Real reference usage

~~~python
from omega_builder.edge.tensor_core import TensorBank, hardware_dispatch_plan
from omega_builder.edge.thermodynamics import cpu_gibbs_reference
from omega_builder.edge.hdc import reference_associative_retrieval
from omega_builder.edge.mesh import sign_event, verify_event, ReplayGuard

state=TensorBank(8)
state.update([1.]*8)
print(state.snapshot())                           # CPU, float32
print(hardware_dispatch_plan(1,8))                 # UNAVAILABLE
print(cpu_gibbs_reference(samples=5,seed=42))      # CPU Gibbs
print(reference_associative_retrieval(dim=1000))   # bipolar VSA

key=b'your-runtime-secret-at-least-32-bytes!'
event=sign_event('omega/edge/state/node_1','state',{'phase':'idle'},key)
print(verify_event(event,key,replays=ReplayGuard()))
~~~

Zenoh networking requires `permit_network=True` and separately supplied production Zenoh config/peer identity/ACL. Sign events for **telemetry, state, status** only; received payloads are passive DATA, never source code or a task launcher.

## Rigor and correction of supplied snippets

- **Mojo**: modern constructors use `out self`, mutators `mut self`. A tensor type must be imported from its *actual* package and initialized with DType/shape; the proposed `from Tensor import Tensor`/`Tensor(dim)` is not a generic supported API.
- **THRML**: missing node initialization, incorrectly formatted block list and incomplete `sample_states(..., [], [Block(nodes)])` call were corrected against upstream. THRML is a JAX sampling library, not proof of TSU silicon access.
- **Lean**: a theorem saying a predicate is equivalent to its literal definition is tautological and does not establish machine safety; proofs here establish only algebraic limits of the specified predicate. `sorry`/proof holes are not permitted; actual Lean compiler execution remains required.
- **Zenoh**: not an OSI Layer 2 replacement. End-to-end security, message ordering, p95 latency and delivery require real deployment verification. No measured zero-overhead guarantee.
- **HDC**: `torchhd.hash_table(keys,values)` requires aligned vectors. Binding is model-dependent; bundling many pairs yields approximate, noisy retrieval, not general reasoning.
- **Hardware**: Passage L20 6.4 Tbps / FPGA speed, energy and silicon endpoints are **UNVERIFIED**, cannot be inferred from print statements. No device launched, connected or reconfigured.

## Gates before real integration

1. Pin a supported Mojo compiler version and compile/test example in a dedicated job.
2. Install and test optional JAX/THRML, TorchHD and Zenoh versions in a separate environment, record dependency hashes and end-to-end benchmarks.
3. Configure encrypted, authenticated Zenoh transport, peer ACL, durable replay controls and message budgets.
4. Install Lean 4 + mathlib via pinned `lake` manifest, execute theorems and check the gate against real policy and implementation.
5. Connect photonic/FPGA only after hardware discovery, attested firmware/driver support, explicit user approval and safe rollback. Never infer device presence.

ZEUS IS ON HOLD. This is a component library, not an autonomous agent or self-evolution executor.
