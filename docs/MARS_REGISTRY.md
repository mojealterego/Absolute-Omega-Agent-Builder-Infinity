# MARS — rozróżnienie wariantów i warunki integracji

**Status: zarejestrowano w katalogu; NIE podłączono ani nie uruchomiono MARS.**

Skrót **MARS** nie jest jednoznaczny. Przekazany `AGENT BUILDER VOL 1.PDF` (793 strony) nie identyfikuje konkretnego produktu MARS; ciąg „MARS” jako samodzielny termin w ekstrakcji PDF nie wystąpił. Repozytorium nie może bez zgody użytkownika zastąpić tej nazwy przypadkowym projektem.

| Kandydat (osobny ID wyboru) | Udokumentowana funkcja | Status |
|---|---|---|
| `mars-modular-agent-reflective-search` | Modular Agent with Reflective Search: budżetowy MCTS, dekompozycja i pamięć porównawczych refleksji. Źródło: https://github.com/jfc43/MARS | `candidate_unverified` |
| `mars-multi-agent-research-system` | Multi-Agent Research System: workflow badawcze oparte na współpracy agentów, planowaniu i ewaluacji. Źródło: https://github.com/mars-fabric/MARS | `candidate_unverified` |
| `mars-modular-agent-runtime-system` | Modular Agent Runtime System: eksperymentalny runtime agentów ze stanem trwałym. Źródło: https://github.com/tejassinghbhati/MARS | `candidate_unverified` |

### Połączenie z Builderem

Wymagania integracyjne: wykrywanie wersji SDK, przegląd licencji, kontrakt wejścia/wyjścia, model izolacji, import bez wykonywania niezaufanego kodu, testy deterministyczne i regresyjne, konfiguracja providerów. Wybór bez jawnie wskazanego wariantu ma zakończyć się komunikatem o niejednoznaczności, **bez automatycznego instalowania MARS**.

Każda pozycja została dodana do `catalog/frameworks.json`; zatem można ją wybrać jako **projektowany framework**, ale nie otrzymuje statusu `verified_adapter`. Żadna funkcja MARS nie jest tutaj reklamowana jako produkcyjnie działająca.

Powiązanie planowane: adapter MARS → wspólny kontrakt Build Selection → Cognitive Core / Orchestrator / Sandbox → ocena i telemetria FinOps, gdy zostanie zaakceptowana konkretna implementacja.
