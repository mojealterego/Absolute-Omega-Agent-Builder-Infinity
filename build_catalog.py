from __future__ import annotations
import json
import re
from pathlib import Path

root=Path(__file__).parent

def dump(file,data):
    (root/'catalog'/file).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n', encoding='utf8')

choices=[
('agent_code','Agent — Code','artifact',['code']),
('agent_nocode','Agent — No-Code','artifact',['nocode']),
('agent_hybrid','Agent — Hybrid','artifact',['hybrid']),
('meta_agent','Meta-agent','artifact',['code','nocode','hybrid']),
('agent_system','System agentowy','artifact',['code','nocode','hybrid']),
('agent_orchestration','Orkiestracja agentowa','artifact',['code','nocode','hybrid']),
('agent_swarm','Rój agentów','artifact',['code','nocode','hybrid']),
('agent_legion','Legion agentów','artifact',['code','nocode','hybrid']),
('framework_fixed','Framework — sztywny','framework_policy',['code','nocode','hybrid']),
('framework_mixed','Framework — mieszany','framework_policy',['code','nocode','hybrid'])
]
dump('build_types.json', {'schema_version':'1.0','readiness':'selection-only','build_types':[{'id':i,'label':l,'kind':k,'allowed_implementations':m,'generated_agent':False} for i,l,k,m in choices],'nocode_platforms':['n8n','Node-RED','Flowise','Dify','Langflow','Make','Zapier','Power Automate','Activepieces','Pipedream','Botpress','Voiceflow'],'framework_policy_note':'Sztywny = jeden wybrany framework; mieszany = co najmniej dwa jawnie wybrane; automatic wymaga późniejszego procesu doboru i weryfikacji.'})

groups={
'general': '''Python|JavaScript|TypeScript|Rust|Go|C|C++|C#|Java|Kotlin|Swift|Objective-C|Objective-C++|Dart|PHP|Ruby|Perl|R|Julia|MATLAB|GNU Octave|Scala|Groovy|Clojure|ClojureScript|F#|OCaml|Haskell|Elm|PureScript|Erlang|Elixir|Gleam|Lua|Luau|Zig|Nim|D|Ada|SPARK|Fortran|COBOL|Pascal|Object Pascal|Delphi|Free Pascal|BASIC|Visual Basic .NET|VBA|VBScript|PowerShell|Bash|Zsh|Fish|Tcl|Expect|AWK|Sed|Scheme|Racket|Common Lisp|Emacs Lisp|Guile|Forth|Factor|Smalltalk|Pharo|Self|Io|Prolog|Datalog|Mercury|Oz|Curry|Idris|Idris 2|Agda|Coq Gallina|Lean 4|Isabelle Isar|Standard ML|ReasonML|ReScript|Grain|Roc|Unison|Koka|Effekt|Pony|Crystal|V|Chapel|X10|Hack|Haxe|ActionScript|Wolfram Language|Maple|Maxima|GAP|SageMath|Magma|APL|J|K|Q|BQN|Uiua|Rexx|OpenEdge ABL|RPG IV|ABAP|Apex|X++|PeopleCode|M|Ring|Red|Rebol|Red/System|Icon|Unicon|Seed7|Limbo|Oberon|Modula-2|Modula-3|Component Pascal|Eiffel|Dylan|Fantøm|Boo|Squirrel|AngelScript|Monkey X|Neko|PicoLisp|Janet|Hy|NimScript|AutoHotkey|AutoIt|AutoLISP|Logo|Scratch|Snap!|Alice|Processing|Arduino Wiring''',
'data_dsl': '''SQL|PL/SQL|T-SQL|PL/pgSQL|HCL|Nix|Dhall|CUE|Jsonnet|Rego|GQL|Cypher|SPARQL|GraphQL|MQL4|MQL5|Pine Script|EasyLanguage|SAS|Stata|SPSS Syntax|GAMS|AMPL|MiniZinc|ZPL|Solidity|Vyper|Move|Cairo|Yul|Huff|Michelson|LIGO|Cadence|Clarity|Sway|Aiken|JCL|GDScript|GameMaker Language|UnrealScript|Verse|GLSL|HLSL|WGSL|Metal Shading Language|OpenCL C|CUDA C++|ISPC|Verilog|SystemVerilog|VHDL|Chisel|Bluespec SystemVerilog|SystemC|Faust|SuperCollider|Csound|Pure Data|OpenSCAD|POV-Ray SDL|PostScript|TeX|LaTeX|QML|XQuery|XPath|XSLT|TLA+|Alloy|Promela|P|Jenkins Pipeline|Earthly|Dockerfile|Make|CMake|Meson|Bazel Starlark|Gradle Kotlin DSL|Gradle Groovy DSL|AppleScript|JXA|Ink|Twine SugarCube|Inform 7|Ren'Py Script|BibTeX''',
'experimental': '''Brainfuck|Befunge|Piet|Whitespace|INTERCAL|LOLCODE|Ook!|Shakespeare Programming Language|Malbolge|Chef|ArnoldC|Rockstar|GolfScript|Jelly|Pyth|05AB1E|Hexagony|FRACTRAN|Unlambda|SKI Combinator Calculus'''
}
langs=[];seen=set()
for kind,raw in groups.items():
  for name in raw.split('|'):
    key=re.sub(r'[^a-z0-9]+','-',name.lower().replace('+','-plus-').replace('#','-sharp-')).strip('-')
    if key in seen: raise RuntimeError(f'duplicate language key: {key}')
    seen.add(key)
    langs.append({'id':key,'name':name,'family':kind,'status':'catalog_only','runtime_adapter':None,'validation':'not_executed'})
langs.sort(key=lambda x:x['id'])
assert len(langs)>=150,len(langs)
dump('languages.json', {'schema_version':'1.0','count':len(langs),'support_disclaimer':'Lista możliwości wyboru. Każdy wpis catalog_only nie oznacza działającego generatora, kompilatora ani wsparcia frameworka; wymaga adaptera i testów.', 'languages':langs})

framework_groups={
'agent_framework':'''LangGraph|LangChain|Microsoft AutoGen|CrewAI|Semantic Kernel|LlamaIndex|LlamaAgents|DSPy|OpenAI Agents SDK|OpenAI Swarm (legacy)|PydanticAI|Instructor|Haystack|Griptape|CAMEL|Mastra|Google ADK|Strands Agents|Agno|Smolagents|Langroid|Julep|Letta|AgentScope|BeeAI Framework|Atomic Agents|ElizaOS|VoltAgent|Semantic Router|TaskWeaver''',
'agent_implementation':'''AutoGPT|BabyAGI|Devin|SWE-agent|OpenHands|ChatDev|MetaGPT|Magentic-One|Voyager|Generative Agents|WebVoyager|Aider|Cline|Roo Code|OSCopilot|Data Interpreter|PandasAI|K8sGPT|PentestGPT''',
'orchestration_and_scaling':'''Ray|Temporal|Prefect|Dagster|Apache Airflow|Kubernetes|Dapr|NATS|Kafka|RabbitMQ|Redis Streams|Celery|OpenTelemetry|Prometheus|Grafana|Consul|Eureka''',
'edge_inference':'''llama.cpp|Ollama|LM Studio|TensorRT-LLM|MLX|vLLM|TGI|Triton Inference Server|ONNX Runtime|LiteRT|MLC LLM''',
'protocol':'''MCP|MCP Apps|Agent Protocol|A2A|FIPA-ACL|Eclipse Zenoh|OpenAPI|JSON Schema|OAuth 2.1|WebSocket|HTTP|gRPC|FTP|SFTP|SMBv2|SMBv3|SSH|TLS''',
'memory_retrieval':'''Letta memory|Neo4j|GraphRAG|RDF/OWL|Haystack RAG|PostgreSQL|SQLite|Qdrant|Weaviate|Milvus|FAISS|Chroma|LanceDB|Apache AGE''',
'security_evaluation':'''Garak|CyBench|Purple Llama|SWE-bench|WebArena|AgentBench|GAIA|OWASP LLM Top 10|Bandit|Semgrep|Trivy|gVisor|Firecracker|WASM|Open Policy Agent|ImandraX''',
'ide_and_nocode':'''Cursor|Windsurf|PearAI|Melty|n8n|Node-RED|Flowise|Dify|Langflow|Make|Zapier|Power Automate|Activepieces|Pipedream|Botpress|Voiceflow'''
}
frameworks=[];fseen=set()
for category,raw in framework_groups.items():
  for name in raw.split('|'):
    slug=re.sub(r'[^a-z0-9]+','-',name.lower()).strip('-')
    if slug in fseen: slug=category+'-'+slug
    fseen.add(slug)
    frameworks.append({'id':slug,'name':name,'category':category,'status':'candidate_unverified','integration':'not_connected','role':'catalogue_reference'})
frameworks.sort(key=lambda x:x['id'])
dump('frameworks.json',{'schema_version':'1.0','count':len(frameworks),'note':'Inventory of candidates, products, protocols and systems. Entry is not proof of runtime integration or license suitability. Category-specific choices need compatibility checks.', 'frameworks':frameworks})

capability_groups={
'memory': '''bitemporal-store|bitemporal-graph-memory|valid-time|transaction-time|point-in-time-recovery|working-memory|long-term-memory|semantic-memory|episodic-memory|procedural-memory|CoALA|G-Memory|SHIMI-index|holographic-memory|HDC-VSA|memory-paging|context-compression|memory-of-failures|RLAIF|federated-knowledge-graph|GraphRAG|RAG-2.0|temporal-RAG|concept-drift''',
'reasoning':'''ReAct|chain-of-thought-reasoning|tree-of-thoughts|Graph-of-Thoughts|decision-cycle|cognitive-modulation|reflexion|self-correction|retrospective-correction|self-consistency|multi-agent-debate|AB-MCTS|Bellman-MDP|Nash-equilibrium|R2-reasoning|R3-Titans|auto-CoT|meta-prompting|plan-and-solve|self-critique|formal-verification|ImandraX|uncertainty-estimation|confidence-gating''',
'evolution':'''AlphaEvolve|Darwin-Godel-Machine|mutation-engine|digital-genotype|mutation-loop|recursive-self-improvement|candidate-branch-sandbox|regression-comparison|evolutionary-scoring|shadow-deployment|A-B-testing|rollback|CEV-alignment|OESI|SEGPA|secure-enclave-attestation|adversarial-gating|synthetic-red-team''',
'neural_research':'''JEPA|SNN|Titans-neural-memory|deep-generative-models|neural-steering|HDC|R3Mem|Toolformer|distillation|DPO|RLAIF|federated-learning''',
'orchestration':'''event-driven-architecture|asynchronous-concurrency|DAG-planning|agent-registration|agent-communication|agent-delegation|service-discovery|orchestrator|task-queue|role-routing|agent-swarm|agent-legion|human-in-the-loop|budgeting|exponential-backoff-jitter|deadline-timeouts|load-shedding|graceful-degradation|canary|shadow-mode|mcp-gateway|agent-protocol|Zenoh|FIPA-ACL''',
'security':'''zero-trust-sandbox|prompt-injection-boundary|data-exfiltration-controls|secret-redaction|schema-enforcement|signed-artifacts|supply-chain-scanning|policy-approval|risk-tiering|rate-limiting|resource-limits|auditable-actions|human-authorization|network-egress-controls|hardware-attestation|cyber-security-audit''',
'product_and_business':'''BATNA|TCO|FinOps|MLOps|negotiation|stakeholder-management|conflict-resolution|technology-radar|critical-thinking|responsible-automation|cost-quality-latency-tradeoff|privacy-compliance|knowledge-consolidation|SLA-SLO|goal-optimization|risk-assessment'''
}
capabilities=[]
for category,raw in capability_groups.items():
  for name in raw.split('|'):
    if any(c['id'] == name.lower().replace(' ','-') for c in capabilities):
      continue
    capabilities.append({'id':name.lower().replace(' ','-'),'name':name,'category':category,'implementation_status':'requirements_only','validation':'not_implemented','notes':'Triage against existing OMEGA assets and primary sources before implementation.'})
dump('capabilities.json',{'schema_version':'1.0','capabilities':capabilities,'important_homonyms':{'DGM':['Darwin Gödel Machine/self-improving agent','Deep Generative Models: GAN/VAE/diffusion; DIFFERENT technology'], 'OESI':['User-defined, meaning not independently verified'], 'SEGPA':['User-defined, meaning not independently verified'], 'G-Memory':['Use the explicit graph interaction/query/insight hierarchy from OMEGA documentation; not a generic global cache'], 'SHIMI':['Semantic hierarchical indexing pattern; do not claim a verified SHIMI paper implementation']}})

dump('infrastructure.json',{'schema_version':'1.0','builder_output_targets':[{'id':n,'status':'requirements_only','security':'approval_required_before_external_write'} for n in ['agent','meta_agent','agent_system','agent_orchestrator','agent_swarm','agent_legion','skill','tool','hook','plugin','mcp_server','framework','sandbox','ftp_server','sftp_server','smbv2_server','smbv3_server','network_drive','agent_registry','agent_capability_profile','communication_fabric']], 'protocols':[
 {'id':'mcp','role':'model-to-tool transport / context interfaces','claim':'protocol only, not a security proof'},
 {'id':'zenoh','role':'low-latency pub/sub/query for distributed edge','claim':'No universal sub-ms guarantee, measure p50/p95/p99 in real topology'},
 {'id':'sftp','role':'encrypted file transfer over SSH','claim':'requires credential and path security'},
 {'id':'ftp','role':'unencrypted legacy file transfer','claim':'disabled by default for remote/public networks; require explicit approval and isolation'},
 {'id':'smbv2','role':'SMB-compatible file shares','claim':'legacy protocol; prefer SMBv3 for new network designs'},
 {'id':'smbv3','role':'encrypted-capable network shares','claim':'encryption and signing must be explicitly configured and tested'},
 {'id':'fipa_acl','role':'typed communicative acts among agents','claim':'message semantics need concrete implementations'},
 {'id':'agent_protocol','role':'agent task/step API','claim':'version and provider compatibility must be established'}
 ],'nonfunctional_targets':{'zenoh_latency_p99':'< 1 ms (aspiration only; not demonstrated)','availability':'SLO to be specified','security':'zero trust by default','cost':'FinOps budgets required','audit':'immutable evidence & data provenance','concurrency':'bounded queues, per-agent limits'}})

dump('zeus_contract.json',{'schema_version':'1.0','name':'AGENT ARCHITEKT OMEGA ZEUS INFINITY','implementation_status':'ON_HOLD_AWAITING_USER_MATERIAL','generated_artifacts':[],'agent_file_created':False,'priority':'First agent to be built after the user explicitly releases hold and supplies remaining source material','responsibilities':['architecture & requirements triage','agent/meta-agent/MAS/swarm/legion creation','skills/tools/hooks/plugins creation','MCP gateways and servers','FTP/SFTP/SMBv2/SMBv3 servers and network drives with security gates','framework selection, composition and new framework authoring','sandbox selection','orchestration and communication','registry with detailed descriptions, capabilities and provenance','tests/QA/adversarial gates','versions and evidence/rollback'],'hold_reason':'User explicitly instructed: do not create Zeus yet; more material forthcoming.','exit_criteria':['User explicit command to start Zeus creation','Remaining materials received and reviewed','Approved architecture and acceptance tests']})
print('languages',len(langs),'frameworks',len(frameworks),'capabilities',len(capabilities))
