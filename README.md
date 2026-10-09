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
- **141** nazw frameworków, protokołów, produktów i środowisk: kandydaci (`candidate_unverified`), a nie aktywne integracje.
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

## Podstawa i licencje

Nie ma kopiowanych obcych kodów lub modeli. Spis nazw technologii służy wyłącznie ewidencji wymagań. Wersje, licencje, aktywne biblioteki, kompilatory, sprzęt i uprawnienia trzeba sprawdzić przed produkcyjną integracją. Repozytorium rozwijane jest wyłącznie na `main`.
