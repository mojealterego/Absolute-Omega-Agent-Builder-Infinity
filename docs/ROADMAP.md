# Roadmap — Zero → Release

| Faza | Zakres | Status | Kryterium zakończenia |
|---|---|---|---|
| 0 | Repozytorium, menu 10 opcji, katalog 150+, baza dostarczonej wiedzy | **W tym wdrożeniu** | Testy przechodzą; repo main; Zeus zablokowany |
| 1 | Odebranie brakujących materiałów i ostateczny projekt Zeusa | **CZEKA NA UŻYTKOWNIKA** | Complete requirements, approved system architecture |
| 2 | **ZEUS jako pierwszy agent** — dopiero na nowe polecenie użytkownika | **ON HOLD** | Kod/SDK, testy, bezpieczeństwo, akceptacja |
| 3 | Walidatory języków i adaptery Code | **Plan** | Kompilacja i QA każdego obsługiwanego języka (osobny certyfikat) |
| 4 | No-Code/Hybrid: n8n, Node-RED, pozostałe środowiska | **Plan** | Provider-native load, round-trip, boundary tests |
| 5 | MAS / meta-agenci / roje / legiony | **Plan** | Właściciel stanu, backpressure, limits, failover |
| 6 | Skills/Tools/Hooks/Plugins/MCP/FTP/SFTP/SMB | **Plan** | Wersjonowanie, uprawnienia, audyt, sandbox i rollback |
| 7 | Bitemporal/CoALA/HDC/SHIMI/G-Memory/RAG | **Plan** | Point-in-time QA, provenance, retention |
| 8 | Ewolucja DGM, eksperymenty RSI/JEPA/SNN | **Badawcze** | Powtarzalne benchmarki, dowody eksperymentalne, izolacja |
| 9 | Rust + Zenoh i porównanie opóźnień | **Badawcze** | Środowisko testowe i p50/p95/p99, brak z góry obiecanej latencji |
| 10 | CI/CD, supply chain, security, model cards | **Plan** | End-to-end testy, security review, production readiness |

## Kontrakt zasady „najpierw Zeus”

W fazie 0 można rozwijać **infrastrukturę katalogu**, dokumentację i mechanizmy wyboru — to nie są agenty. Faza 2 jest pierwszym etapem budowy agenta dopiero po fazie 1 i potwierdzeniu użytkownika. Implementacja innych agentów nie wyprzedzi Zeusa bez późniejszej zmiany decyzji użytkownika.

## Zależności krytyczne

- Bez potwierdzonego adaptera nazwa frameworka pozostaje kandydatem, nie wywołaniem narzędzia.
- Bez wyników performance testów Zenoh `<1ms` jest celem, nie osiągnięciem.
- Nie ma definicji semantycznej części nazw badawczych (SEGPA/OESI); uzupełnić ze źródeł użytkownika.
- Wdrożenia FTP/SFTP/SMB potrzebują planu autoryzacji i parametrów sieciowych.
- Repozytorium pozostaje **jednogałęziowe: `main`**.

## Dodatkowe bramki Vol. 1 (2026-10-09)

| Kolejny krok | Status |
|---|---|
| MARS: rozstrzygnięcie jednoznacznego frameworka i licencji | `WAITING_USER_VARIANT` |
| Diagram i korekta zapisu Bellmana / FinOps | `DOCUMENTED` |
| TLA+ model i Alloy model: uruchomienie TLC/Alloy w CI | `MODELS_WRITTEN_RUN_NOT_VERIFIED` |
| Real-time token metering / budget router Frontier ↔ Edge | `REQUIREMENTS_ONLY` |
| HE / GPU TEE threat model i benchmark | `RESEARCH_ONLY` |
| Neuromorphic SNN + vector compute hardware benchmark | `RESEARCH_ONLY` |
| Przegląd i deduplikacja pełnego 793-stronicowego Vol. 1 | `PARTIAL_INTAKE` |
| Agent Architekt OMEGA ZEUS Infinity | **`ON_HOLD` — NIE TWORZYĆ** |

## Etap statystyki i danych — baza prac (2026-10-09)

| Obszar | Status |
|---|---|
| Korelacja, rozkłady, MLE/MAP, Markov, Monte Carlo, entropia warunkowa, MI, Huffman | `IMPLEMENTED_OFFLINE_AND_TESTED` po zielonym CI |
| Train-only fit/transform, IQR, one-hot, PCA opcjonalnie NumPy | `IMPLEMENTED_OFFLINE` (PCA wymaga NumPy) |
| SQLite: KV, graph edges, time series, vectors brute-force, provenance, bitemporal | `IMPLEMENTED_LOCAL_PROTOTYPE` |
| Data lakehouse ACID, obiektowy storage, GraphRAG, Qdrant, Neo4j, embedding generation | `NOT_IMPLEMENTED` |
| Monitoring drift, rozkłady wielowymiarowe, strumieniowe przetwarzanie Big Data | `NEXT_STAGE` |
| ZEUS | **`ON_HOLD_AWAITING_USER_MATERIAL`** |

## Etap ML Evaluation, Embedder i Data Governance

Dostarczono implementacje offline plus opcjonalne biblioteki rzeczywistych algorytmów: podziały i CV, diagnostyka dryfu, SMOTE na train, LDA, t-SNE, UMAP, autoenkoder NumPy, wykresy oraz prywatność i provenance. Status produkcyjnych endpointów danych: NIEGOTOWE. Pełen audyt: [ML_EVALUATION_GOVERNANCE.md](ML_EVALUATION_GOVERNANCE.md). Zeus ON HOLD.

## MCP Global Landscape — etap intake 2026-10-09

| Wymaganie | Stan |
|---|---|
| Normalizacja oficjalnego MCP Registry v0.1, kursory, deduplikacja, źródła | `OFFLINE_IMPLEMENTED` |
| 7-kryterialny przegląd ryzyka, import allowlisted schemas bez `tools/call` | `OFFLINE_IMPLEMENTED` |
| Audyt kodu, licencji, provenance; zewnętrzny scanner i egress policy | `NEXT_STAGE` |
| Realne połączenia, OAuth, produkcyjny Streamable HTTP, instalacja MCP | `NOT_IMPLEMENTED` |
| Ekonomiczne płatności L402, płatna aktywacja serwerów | `NOT_AUTHORIZED` |
| Katalogi Glama, Smithery, GitHub Registry, Hugging Face, LlamaHub, Composio | `RESEARCH_ONLY_UNVERIFIED_COUNTS` |
| AGENT ARCHITEKT OMEGA ZEUS INFINITY | `ON_HOLD_AWAITING_USER_MATERIAL` |

[Pełny audyt MCP](MCP_GLOBAL_LANDSCAPE_2026.md).
