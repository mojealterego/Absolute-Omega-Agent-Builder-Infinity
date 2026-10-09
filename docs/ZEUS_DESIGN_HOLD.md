# ZEUS INFINITY — SPECYFIKACJA WSTRZYMANA

**Decyzja nadrzędna użytkownika (2026-10-09): NIE TWORZYĆ JESZCZE AGENTA ZEUS, ponieważ będą dostarczone kolejne materiały.**

Stan: `ON_HOLD_AWAITING_USER_MATERIAL`.

## Miejsce w docelowej architekturze

Pierwszym tworzonym agentem wykonawczym projektu ma być **AGENT ARCHITEKT OMEGA ZEUS INFINITY**. Będzie koordynować tworzenie: agentów Code/No-Code/Hybrid, meta-agentów, systemów wieloagentowych, orkiestracji, rojów, legionów, skills, tools, hooks, pluginów, serwerów MCP, gatewayów MCP, serwerów FTP/SFTP, udostępnień SMBv2/SMBv3 i dysków sieciowych. Ma utrzymywać rejestr agentów, ról, uprawnień, frameworków, zależności, umiejętności i dowodów wykonania.

## Zakres przyszłych interfejsów (wymagania, nie kod)

1. `ArchitectureIntake`: wymagania, cel, wybór typu systemu, ograniczenia, koszt, urządzenie, polityka prywatności.
2. `FrameworkAdvisor`: wykrywanie faktycznych kompetencji i dobór `fixed` / `mixed` / `automatic`; raport zgodności język–framework–runtime.
3. `ArtifactFactory`: sterowane kontraktami wytwarzanie Agentów, Skills, Tools, Hooks, Plugins, MCP, frameworków, sandboxów i konektorów plikowych.
4. `AgentRegistry`: identyfikator, szczegółowy opis, wersja, właściciel, narzędzia, umiejętności, protokoły, profil zagrożeń, zależności i status testów.
5. `CommunicationFabric`: połączenia agent–agent, pub/sub, request/reply, backpressure, idempotency, tracing, ewentualnie Zenoh.
6. `SecureExecution`: izolacja, least privilege, allowlisted egress, SFTP/SMB3 hardening, autoryzacja operacji wysokiego ryzyka.
7. `EvidenceGate`: testy, evale, synthetic red team w uprawnionej piaskownicy, rejestr wyników, rollback, polityki publikacji.
8. `MemoryPlane`: bitemporalny zapis i replay, pamięć robocza/epizodyczna/proceduralna/semantyczna, retrieval z pochodzeniem danych.
9. `EvolutionPlane`: dopiero po potwierdzeniu testów, approval gate, audyt mutacji, porównania baseline i rollback.

## Dane nadal potrzebne przed odblokowaniem

- Dalsze materiały, zapowiedziane przez użytkownika.
- Zatwierdzony zakres pierwszej wersji Zeusa i docelowy model uprawnień.
- Docelowe środowiska wykonania (Android, web, cloud, desktop, edge), modele i infrastruktura.
- Mapowanie, które frameworki mają być realnie podłączone, a które tylko ewidencjonowane.
- Akceptacja kryteriów jakości, bezpieczeństwa i testów.
- **Oddzielne, wyraźne polecenie utworzenia Zeusa.**

## Blokada wykonawcza

`catalog/zeus_contract.json` jest tylko specyfikacją. Testy kontrolują jego stan `ON_HOLD_AWAITING_USER_MATERIAL` i brak `AGENT.md`. Żadne generowanie pliku Zeusa, aktywacja procesu lub deploy nie może być domniemanym skutkiem polecenia importu materiałów.
