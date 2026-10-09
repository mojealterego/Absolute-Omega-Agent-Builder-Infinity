# Diagram przepływu: Cognitive Core ↔ Orchestrator ↔ Sandbox

Przepływ jest **schematem docelowym**, nie dowodem działającej infrastruktury. Jego maszynowo edytowalna wersja to [Cognitive-Core-Orchestrator-Sandbox.mmd](Cognitive-Core-Orchestrator-Sandbox.mmd).

```mermaid
flowchart LR
  U[Wybór użytkownika] --> V[Selection + walidacja]
  V --> O[Orchestrator / LangGraph lub inny]
  O --> C[Cognitive Core / LLM + pamięć]
  C --> O
  O --> G[Policy / adversarial / HITL]
  G --> S[Sandbox / narzędzia / MCP]
  S --> T[Wynik i telemetry]
  T --> O
  T --> F[MLOps / FinOps: koszty, błędy, latency]
  F --> R[Routing: Frontier ↔ Edge]
  R --> C
```

**Dane:** zatwierdzony kontrakt → stan zadania → wnioskowanie → decyzja narzędziowa → brama zabezpieczeń → sandbox → wynik z dowodem → aktualizacja pamięci i telemetrii.

**Kontrola:** brak nieograniczonego wykonywania, jawne uprawnienia, limity czasu/kosztu, brak wynoszenia sekretów, pełny ślad. Warstwy oznaczone jako docelowe wymagają adapterów i testów produkcyjnych.

**Blokada:** ZEUS ma jedynie kontrakt/specyfikację. Diagram nie stanowi polecenia utworzenia Zeusa.
