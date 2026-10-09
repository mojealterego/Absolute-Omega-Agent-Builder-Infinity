# ABSOLUTE OMEGA AGENT BUILDER ∞

**Etap 0 — przyjęcie wiedzy i kontrakt wyboru. Agent ARCHITEKT OMEGA ZEUS INFINITY nie został utworzony.**

Repozytorium zawiera działającą, lokalną warstwę **wyboru rodzaju projektu**, rejestry techniczne oraz udokumentowane wymagania. Aktualny kod waliduje konfigurację i wystawia wyłącznie `selection_blueprint_only`. **Nie uruchamia agentów, nie trenuje modeli, nie instaluje serwerów ani nie wykonuje kodu użytkownika.**

## Menu główne

| Numer | Rodzaj projektu | Klucz API |
|---:|---|---|
| 1 | Agent Code | `agent_code` |
| 2 | Agent No-Code | `agent_nocode` |
| 3 | Agent Hybrid | `agent_hybrid` |
| 4 | Meta-agent | `meta_agent` |
| 5 | System agentowy | `agent_system` |
| 6 | Orkiestracja agentowa | `agent_orchestration` |
| 7 | Rój agentów | `agent_swarm` |
| 8 | Legion agentów | `agent_legion` |
| 9 | Framework sztywny — jeden | `framework_fixed` |
| 10 | Framework mieszany — wiele | `framework_mixed` |

Dla każdej kategorii, zgodnie z dozwolonym trybem, użytkownik wybiera Code / No-Code / Hybrid, język (jeśli kod), platformę No-Code (jeżeli dotyczy), politykę frameworków `automatic` / `fixed` / `mixed` i docelowy typ projektu. Wybór frameworka z kategorii transportowej, protokołów lub IDE nie potwierdza jego przydatności do kodowania agentów; dobór i zgodność będą walidowane w późniejszych etapach.

## Liczby katalogowe (a nie gotowe implementacje)

- **10** opcji głównego menu.
- **257** nazw języków, dialektów i DSL do wyboru (`catalog_only`). Żadnego z tych 257 adapterów kompilacji nie uznano za zaimplementowany tylko na podstawie wpisu na liście.
- **144** nazw frameworków, protokołów, produktów i środowisk: kandydaci (`candidate_unverified`), a nie aktywne integracje.
- **133** unikalne wymagania funkcjonalne, poznawcze, ewolucyjne, bezpieczeństwa i biznesowe.
- Wstępna specyfikacja **Zeusa** z blokadą implementacji do czasu przekazania brakującego materiału i wyraźnego polecenia użytkownika.

## Szybki start (Python 3.11+, bez zewnętrznych pakietów)

```bash
python -m omega_builder menu
python -m omega_builder languages --count
python -m omega_builder frameworks --category agent_framework
python -m omega_builder catalog-audit
python -m omega_builder validate examples/agent-code.json
python -m omega_builder select --build-type agent_code --implementation code --language rust --framework-mode fixed --framework langgraph --output /tmp/omega-selection.json
python -m unittest discover -s tests -v
```

Dla No-Code:

```bash
python -m omega_builder select --build-type agent_nocode --implementation nocode --nocode-platform n8n
```

Dla frameworka mieszanego:

```bash
python -m omega_builder select --build-type framework_mixed --target-build-type agent_system --implementation code --language python --framework-mode mixed --framework langgraph --framework crewai
```

## Zasada priorytetowa: Zeus pozostaje na wstrzymaniu

Użytkownik zażądał, aby **Zeus był pierwszym projektowanym agentem** po skompletowaniu materiału, oraz jednocześnie zakazał jego przedwczesnego tworzenia. W tym repo jest tylko **specyfikacja kontraktu `catalog/zeus_contract.json`** i dokumentacja (`docs/ZEUS_DESIGN_HOLD.md`). Nie ma pliku AGENT.md, modelu Zeusa, serwera Zeusa, promptu wdrożeniowego ani runtime'u Zeusa. Nie odblokowywać automatycznie po CI.

## Dokumentacja

- [`docs/KNOWLEDGE_INTAKE_2026-10-09.md`](docs/KNOWLEDGE_INTAKE_2026-10-09.md) — normalizacja dostarczonej obszernej wiedzy i klasyfikacja technologii.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — moduły i kontrakty przyszłego systemu.
- [`docs/ZEUS_DESIGN_HOLD.md`](docs/ZEUS_DESIGN_HOLD.md) — obowiązki, brakujące materiały i formalna blokada tworzenia.
- [`docs/REALITY_AUDIT.md`](docs/REALITY_AUDIT.md) — twierdzenia ryzykowne, rozróżnienie wzorców od implementacji, luki dostarczonego przykładu kodu.
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — kolejne etapy do zatwierdzenia.

## Aktualizacja Vol. 1: MARS / Cognitive Core / Formal / FinOps

- [Źródło Vol. 1 i manifest integralności](docs/VOL1_SOURCE_MANIFEST.md) — 793 strony PDF dostarczone przez użytkownika.
- [MARS: trzy różne projekty, bez automatycznego utożsamiania](docs/MARS_REGISTRY.md) — 3 pozycje dodane do katalogu frameworków, **bez podłączonych adapterów**.
- [Diagram Cognitive Core → Orchestrator → Sandbox](docs/architecture/ARCHITECTURE_FLOW.md) i [plik Mermaid](docs/architecture/Cognitive-Core-Orchestrator-Sandbox.mmd).
- [MLOps / FinOps / kosztowe przełączanie Frontier ↔ Edge](docs/MLOPS_FINOPS_ROUTING.md).
- [Formal model checking (TLA+ + Alloy)](docs/FORMAL_VERIFICATION.md) — modele źródłowe, bez uruchomionych narzędzi TLC/Alloy.
- [Szyfrowanie homomorficzne / GPU / enklawy](docs/SECOPS_HOMOMORPHIC_ENCLAVES.md).
- [Architektura SNN + HDC / wektorowa](docs/NEUROMORPHIC_SNN_VECTOR.md).
- [Poprawiona notacja matematyczna i formatowanie](docs/MATH_NOTATION_AND_FORMAT.md).

**Stan projektu:** dalsze materiały przyjmowane, Zeus nadal `ON_HOLD_AWAITING_USER_MATERIAL`. Każde dopisanie MARS, modelu formalnego czy narzędzi badawczych oznacza rejestrację architektury, nie utworzenie agenta.

## Podstawa i licencje

Nie ma kopiowanych obcych kodów lub modeli. Spis nazw technologii służy wyłącznie ewidencji wymagań. Wersje, licencje, aktywne biblioteki, kompilatory, sprzęt i uprawnienia trzeba sprawdzić przed produkcyjną integracją. Repozytorium rozwijane jest wyłącznie na `main`.


## Referencyjne moduły kontrolne (offline, bez Agent/Zeus runtime)

- `omega_builder/finops.py` — testowalny kosztowy wybór providerów Frontier/Edge z fail-closed oraz rejestrowaniem zużycia na podstawie podanych cen; **bez połączenia z API lub billingiem**.
- `omega_builder/protocol_model.py` — eksploracja ograniczonego grafu stanów przydziałów, brak podwójnego lease i brak terminalnego deadlock w modelu; **nie zastępuje uruchomienia TLC/Alloy**.
- `tests/test_volume1.py` — testy MARS, Zeusa, FinOps i referencyjnego modelu.

Ważne: dane o jakości i p95 mają pochodzić z pomiarów właściwych dla domeny. Model odrzuca niedopuszczalne API i nie emuluje prawdziwego dostawcy.

## Mathematical Reasoning Core — Bloki V–VIII

Zaaplikowano działającą lokalną bibliotekę matematyczną (algebra liniowa, rozkłady LU/QR/Cholesky, precyzyjne układy wymierne, ograniczona logika formalna, grafy, statystyka i analiza numeryczna). SVD wymaga zainstalowanego NumPy.

Szczegóły, ograniczenia, przykłady i definicje gwarancji: [docs/MATHEMATICAL_REASONING_CORE.md](docs/MATHEMATICAL_REASONING_CORE.md).

Uruchomienie: python -m omega_builder math-ops; python -m omega_builder math examples/math_exact_linear.json.

Żadnego automatycznego tworzenia ani uruchamiania agenta Zeus. ON HOLD.

## Uzupełnienie VIII / Data Engineering — statystyka, informacja, preprocessing, magazyn lokalny

- `omega_builder/mathematics/statistics.py`: rzeczywiste PMF/PDF, estymatory MLE/MAP, korelacja, kowariancja, Markov, Monte Carlo.
- `omega_builder/mathematics/information.py`: H(Y|X), I(X;Y), pojemność Shannon–Hartley, SNR, kodek Huffmana.
- `omega_builder/preprocessing.py`: imputacja i standaryzacja **fit tylko na treningowym**, one-hot, deduplikacja, IQR, PCA (NumPy).
- `omega_builder/storage.py`: lokalny SQLite dla JSON key–value, relacji, wektorowego cosine scan, szeregów czasowych, rodowodu i bitemporal facts; **nie jest to produkcyjny Data Lakehouse, Neo4j ani Qdrant**.
- [Dokumentacja i przykłady](docs/STATISTICS_DATA_ENGINEERING.md). Matematyczne API jest wyłącznie offline i jawnie ograniczone.

**Zeus nadal `ON_HOLD_AWAITING_USER_MATERIAL`.**

## ML Evaluation + Embeddings + Governance (2026-10-09)

Kolejny etap Bloków IX/X działa **bez tworzenia Zeusa**.

- [Dokumentacja](docs/ML_EVALUATION_GOVERNANCE.md): train/validation/test z rozłącznymi indeksami, K-fold, Leave-One-Out, próbki warstwowe, raport metryk, treningowe SMOTE, KS/PSI drift, ranking active learning.
- **LDA**: prawdziwy supervised Linear Discriminant Analysis z `scikit-learn` (opcjonalne `pip install '.[ml]'`). Projekcja nowych danych oparta wyłącznie na parametrach fit z treningu.
- **t-SNE/UMAP**: prawdziwe implementacje `scikit-learn` / `umap-learn`, wyłącznie exploratory fit_transform; nie mają obietnicy zachowania globalnych odległości.
- **Autoenkoder**: bounded shallow NumPy neural autoencoder uczony przez backpropagation z pełnym batch; opcjonalne `pip install '.[math]'`. Nie jest model produkcyjny.
- **Wykresy**: realne podsumowania histogram, boxplot, scatter, heatmap i opcjonalny zapis PNG przez `matplotlib`.
- **Quality + Security**: analiza braków/duplikatów, treściowego leakage, kontrolowane słabe etykietowanie, HMAC pseudonimizacja (sekret poza repo), maskowanie wybranych identyfikatorów, proste diagnostyki różnic między grupami i sprzeczności etykiet. Nie jest to gwarancja RODO ani pełnej anonimowości.

**Zeus nadal wstrzymany.**
