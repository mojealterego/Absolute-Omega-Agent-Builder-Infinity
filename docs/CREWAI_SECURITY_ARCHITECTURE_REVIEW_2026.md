# CrewAI: analiza architektury i zabezpieczenia kontrolne dla OMEGA Builder

Data przyjęcia: **2026-10-09**. Repozytorium: **Absolute-Omega-Agent-Builder-Infinity**, wyłącznie **main**.

## Materiał wejściowy i integralność

- Użytkownik przekazał 16-stronicowy dokument PDF: **Badanie Architektury i Bezpieczeństwa CrewAI (1).pdf**, tytuł wewnętrzny: *Projekt Skalowania Systemów Autonomicznych: Deterministyczna Architektura Wieloagentowa CrewAI*.
- SHA-256 przesłanego PDF: **f13ad99309535ef0ba2dda384a565edf2066bc51b97303af0b8d04b8f73ab0db**; rozmiar **412148** bajtów; 16 stron.
- Dokument nie został automatycznie skopiowany ani opublikowany w repozytorium. Ten plik dokumentuje wynik analizy i oddziela twierdzenia autora od potwierdzonych implementacji.

## Struktura raportu (według źródła)

1. **Faza 1 — Profil taktyczny i executive summary (str. 1–3):** argumentacja Enterprise i finansowa, teza o przewadze determinizmu CrewAI.
2. **Faza 2 — Architektura i stos technologiczny (str. 3–6):** różnica **Crews** i **Flows**; semantyczna pamięć, wagi similarity/recency/importance; stan Pydantic, UUID i trwałość, OpenTelemetry/OpenInference, adaptacja MCP.
3. **Faza 3 — Problem–rozwiązanie (str. 6–8):** ryzyko nieskończonych pętli, retries, przepalenie budżetu; deterministyczne limity w grafie kontroli.
4. **Faza 4 — Red teaming i bezpieczeństwo (str. 8–11):** opis PI-2.0 / tool poisoning, DNS rebinding i nieprawidłowego przekazywania tokenów OAuth (token passthrough).
5. **Faza 5 — Finansowanie i skalowalność (str. 11–13):** ceny, Enterprise TCO, ROI/payback, prognoza penetracji rynku.
6. **Bibliografia (str. 13–16):** źródła o CrewAI, narzędziach telemetrycznych, MCP, finansach i bezpieczeństwie.

## Rzeczywiście dodana warstwa kontrolna

| Plik | Wdrożona funkcja | Gwarancje i ograniczenia |
| --- | --- | --- |
| omega_builder/crew_flow_guard.py | Walidowany **acykliczny** graf kroków, bounded retries, limity liczby eventów i kosztów, deduplikacja receipt ID, deterministyczny replay stanu i skrót SHA-256 dziennika | **Offline**; brak wywołań Agent/Crew, LLM, MCP, procesów i płatności. Koszt wyłącznie na podstawie wartości dostarczonych przez wywołującego; nie jest billable reconciliation. |
| omega_builder/crew_flow_guard.py:tool_intent | Allowlista narzędzi per etap, SHA-256 pełnych argumentów, dla mutacji jawnie dopasowany digest zadeklarowanej akceptacji | Nie uwierzytelnia użytkownika ani podpisu HITL. Status tylko **eligible_for_separate_executor**. Nie jest działającym systemem autoryzacji enterprise. |
| omega_builder/crew_memory.py | Ranking kandydata po cosinusie, recency half-life i zadeklarowanej wadze importance; limit top-k, izolacja scope i odrzucenie przyszłych rekordów | Bez prawdziwego modelu embeddingów, pamięci długoterminowej, konsolidacji, LLM, automatycznego zapominania czy audytu źródeł. Zwraca identyfikatory i metryki, **nie treść potencjalnie wstrzykniętych instrukcji**. |
| omega_builder/mcp_registry.py | Wcześniej istniejące przeglądanie niezaufanych schematów MCP oraz ocena ryzyka źródeł | Bez uruchamiania dowolnego zewnętrznego kodu lub nadawania uprawnień. |
| omega_builder/edge/mutation_gate.py | Wcześniejsza kontrola manifestu mutacji | Bez wykonywania kodu; nie dowodzi alignment. |
| tests/test_crewai_controls.py | Jednostkowa ewaluacja grafów, pętli, kosztów, tool allowlist, scope i jakości wyników | Nie są to end-to-end testy CrewAI ani testy z prawdziwym LLM/MCP. |

## Krytyczne rozróżnienia dla architektury

- **Flows ograniczają ścieżkę wywołań**, ale nie czynią probabilistycznego modelu deterministycznym, prawdziwym ani wolnym od halucynacji.
- **Pydantic** pomaga z typowaniem i walidacją wejścia; nie oznacza izolacji bezpieczeństwa, autentyczności poświadczeń czy braku ryzyka SQL/command injection.
- **UUID** identyfikuje instancję przepływu; samo UUID nie szyfruje stanu ani nie zapewnia bezpiecznego odtwarzania po awarii klastra.
- **SQLiteFlowPersistence** może utrzymywać lokalne checkpointy; nie implikuje replikacji, HA, transakcyjnego exactly-once lub odporności na utratę hosta.
- **OpenTelemetry/OpenInference** daje narzędzia observability, ale samo włączenie telemetry nie stanowi automatycznej certyfikacji SOC 2, zgodności GDPR ani dowodu integralności wszystkich zdarzeń. Logowanie treści promptów i tokenów stwarza ryzyko wycieku PII i sekretów.
- **Transport stdio nie jest automatycznie najbezpieczniejszy**: proces serwera posiada uprawnienia konta uruchamiającego; niezweryfikowany lokalny pakiet może być znacznie bardziej ryzykowny niż prawidłowo izolowana usługa zdalna.
- **MCPServerAdapter/DSL**: to zewnętrzny integrator SDK; wyrażenia mcps=[...] muszą posiadać rzeczywistą konfigurację i polityki zaufania. Bezpieczne wykonanie wymaga sprawdzenia uprawnień **przy każdym tools/call**.
- **DNS rebinding:** wymaga ochrony serwera (Host/Origin, polityki sieci, auth), klienta (egress, rozwiązywanie DNS, redirecty) i aktualnych poprawek; sprawdzenie stringa URL nie wystarczy.
- **Token passthrough:** token musi być skierowany do właściwego resource/audience, z rozdzieleniem uprawnień i bez przekazywania tokenu klienta do dowolnego MCP proxy.
- **HITL:** porównanie hasha argumentów w module planowania **nie jest jeszcze autoryzacją**. Produkcja wymaga podpisanego, autentycznego, jednokrotnego approval z zakresem operacji, TTL i tenant ID.
- **TCO, udziały Fortune 500, liczba wykonań, oszczędności i deklaracje TRL9**: traktujemy jako **twierdzenia z raportu, a nie niezależnie potwierdzone dowody**. Nie powielamy prognoz o gwarantowanym ROI.

## Zewnętrzny punkt odniesienia (oddzielony od treści użytkownika)

Oficjalna dokumentacja CrewAI opisuje @start, @listen, @router, typowane stany Pydantic i opcjonalne @persist. Integrację narzędzi MCP zapewnia adapter/DSL; obsługa narzędzi nie oznacza automatycznej integracji wszystkich prymitywów zasobów i promptów.

- https://docs.crewai.com/en/concepts/flows
- https://docs.crewai.com/en/mcp/overview
- https://docs.crewai.com/en/mcp/security
- https://docs.crewai.com/en/concepts/memory

## Do zrobienia — dowody integracyjne

1. **P0:** przypięcie wersji CrewAI, licencji i zależności, import smoke na wspieranym Pythonie, Pydantic/Flow persistence test w izolowanym procesie, testy bramek tenant/role; po zakończeniu status adaptera może zostać zmieniony z reference na verified.
2. **P1:** interfejs do prawdziwego CrewAI Flow z persistent checkpointing, dedupe w bazie oraz odtwarzanie po awarii, retry/backoff z per-tool timeout i circuit breaker.
3. **P1:** testy supply-chain MCP, red-team prompt injection, DNS rebinding, obsługa auth audience oraz transakcyjny HITL podpisywany zewnętrznym kluczem.
4. **P2:** opcjonalne OTel/OpenInference do zatwierdzonego backendu z redakcją danych, propagation trace IDs, kosztami modelu na podstawie rzeczywistego billing API; możliwość wyłączenia eksportu.
5. **P2:** retriever z modelem embeddingowym, wersjonowaniem rekordów, kontrolą tenancy i timestampów, pomiar recall@k, p95 i odporności na poisoning.
6. **P3:** bezpieczne CrewAI↔MCP pod kontrolą jawnych uprawnień, w sandboxie, z niezależnymi benchmarkami jakości i regresją kosztową.

**AGENT ARCHITEKT OMEGA ZEUS INFINITY: ON_HOLD_AWAITING_USER_MATERIAL.** Nie generowano agenta ani uruchomionego systemu CrewAI.
