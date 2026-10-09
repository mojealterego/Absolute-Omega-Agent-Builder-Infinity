# Architektura docelowa — blueprint, nie wykonujący się system agentowy

## 1. Główne wybory

Warstwa wyboru (`omega_builder/selection.py`) udostępnia 10 żądanych opcji. Trzy pierwsze to sposób implementacji pojedynczego agenta, pięć kolejnych to organizacja pracy (meta-agent, system, orkiestracja, rój, legion), a dwie ostatnie dotyczą polityki doboru frameworka (sztywny/mieszany). Dla meta-agentów i wyższych topologii metoda implementacji Code/No-Code/Hybrid jest niezależną, jawną decyzją.

```
USER (wybór jednej z 10 opcji)
    │
    ▼
Selection Contract ────► katalog języków (257, lista bez adapterów)
    │                       katalog frameworków (141, bez połączeń)
    ▼
Verified Blueprint (nie agent, nie kod produkcyjny)
    │
    ▼
ZEUS ARCHITECT (SPEC ONLY; WSTRZYMANE)
    ├── requirements / framework advisor
    ├── project & artifact registry
    ├── builders Code / No-Code / Hybrid
    ├── meta-agent / MAS / swarm / legion topologies
    ├── skills / tools / hooks / plugins / MCP factory
    ├── communication & networking (MCP/A2A/FIPA/Zenoh/FTP/SFTP/SMB)
    ├── temporal + semantic + episodic + procedural memory
    ├── secure execution / evaluation
    └── promotion gates / evidence / rollback
```

## 2. Granice domeny (Clean Architecture)

| Obszar | Przyszły port | Potencjalny adapter (NIE podłączony) | Brama |
|---|---|---|---|
| Generowanie kodu | `CodeGenerator` | Python, TS, Rust, Go, pozostałe 253 języki przez przyszłe adaptery | kompilacja + testy |
| No-Code | `WorkflowExporter` | n8n, Node-RED, Flowise, Dify, Langflow i inne | walidacja w docelowej platformie |
| Framework | `FrameworkResolver` | LangGraph, AutoGen, CrewAI, Semantic Kernel, Google ADK, OpenAI Agents SDK, inne | sprawdzenie SDK i wersji |
| Orkiestracja | `AgentOrchestrator` | maszyna stanów / DAG / event bus / saga | limity zadań i powtarzalność |
| Komunikacja | `AgentTransport` | MCP, A2A, Zenoh, FIPA-ACL | authN/authZ, szyfrowanie, telemetry |
| Sieć | `FileServerPort` | SFTP, FTP, SMBv2/v3 | egress, host keys, ACL, kontrola portów |
| Pamięć | `TemporalMemory` | SQLite/Postgres bitemporal, CoALA, G-Memory, SHIMI, HDC | as-of / provenance / integrity |
| Inteligencja | `InferenceProvider` | llama.cpp, Ollama, vLLM, MLX, TensorRT, JEPA | health check i model provenance |
| Eksperymenty | `MutationEvaluator` | DGM/AlphaEvolve/AB-MCTS/adversarial eval | izolacja i niezmienny baseline |
| Formal verification | `ProofBackend` | ImandraX, Lean, Coq, TLA+ | osobne twierdzenia i dowody |
| Agent registry | `AgentRegistryRepository` | versioned JSON/SQL/knowledge graph | unikalność, status i audyt |

Żaden adapter nie jest uznany za „aktywny” przez samo wymienienie jego nazwy w rejestrze.

## 3. Topologie MAS

- **Meta-agent:** deleguje i monitoruje podległe role; bez nieograniczonego samorozmnażania.
- **System agentowy:** role i przepływy z kontraktami wejścia/wyjścia oraz ownerami stanu.
- **Orkiestracja:** graf stanu, saga lub kolejki, powtórzenia z limitem i odporność na zduplikowane zdarzenia.
- **Rój:** dynamicznie dobierani wykonawcy, ograniczony fan-out, backpressure, shutdown i koszt.
- **Legion:** wielopoziomowa federacja rojów, hierarchia delegowania, izolacja tenantów i audyt.
- **Framework sztywny:** dokładnie jedna wskazana biblioteka/podsystem i wyraźnie wskazany typ projektu.
- **Framework mieszany:** co najmniej dwa wskazane frameworki wraz z pomiarem kosztu ich integracji i granicą odpowiedzialności.

Rozwój roju nie oznacza automatycznie komunikacji all-to-all. Koszt `O(n²)` dotyczy konkretnych topologii pełnej wymiany, a nie dowolnego MAS.

## 4. Pamięć i oś czasu

Rekord bitemporalny powinien przechowywać `valid_from`, `valid_to`, `recorded_at`, `superseded_at`, treść, źródło, hash i uprawnienia; replay ma odzwierciedlać **wiedzę dostępną w danym czasie transakcyjnym**. PiTR wymaga trwałego logu zmian, checkpointów i procedury odtworzenia, a nie tylko wywołania `snapshot()`.

- Working Memory: stan zadania, budżet kontekstu, polityka wygasania.
- Episodic: uporządkowane zdarzenia i ślady zadań.
- Semantic: wiedza i semantyczna wyszukiwarka z pochodzeniem faktów.
- Procedural: sprawdzone umiejętności i kontrakty narzędzi.
- CoALA: wyraźne rozdzielenie pamięci i cyklu decyzyjnego.
- G-Memory: graf interakcji, pytań i wniosków w oparciu o potwierdzone źródła.
- SHIMI: hierarchiczny indeks semantyczny; nazwę traktować jako wymaganie badawcze.
- HDC: hiperektory/wielowymiarowe skojarzenia z mierzonymi kolizjami.
- GraphRAG / RAG: dowody, oceny trafności i cykliczna reindeksacja.

## 5. Bezpieczny cykl publikacji

`user intent → normalized contract → compatibility check → bounded proposal → sandbox → tests → security/evals → approval → commit main → CI → observed release → audit/rollback`

Stan `ON_HOLD` Zeusa przerwie łańcuch przed generacją plików wykonawczych niezależnie od powodzenia testów katalogu.
