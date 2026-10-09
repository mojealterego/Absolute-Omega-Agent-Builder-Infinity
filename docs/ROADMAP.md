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
