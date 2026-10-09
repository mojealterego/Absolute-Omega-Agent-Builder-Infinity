# Globalny Krajobraz MCP — warstwa discovery i bezpiecznego przyjęcia

**Data przyjęcia materiału: 2026-10-09.** Projekt: Absolute-Omega-Agent-Builder-Infinity; tylko gałąź \`main\`. **Zeus wstrzymany.**

## 1. Źródła, a realny stan

Ten dokument rozróżnia **twierdzenia ze źródła użytkownika**, **odrębnie sprawdzone oficjalne dokumentacje protokołów** oraz **fizycznie wdrożone fragmenty repozytorium**. Wielkości i statystyki komercyjne z raportu nie były potwierdzane audytem API tych platform. Wpis do katalogu nie oznacza uruchomienia integracji.

| Twierdzenie z dostarczonego raportu | Weryfikacja |
|---|---|
| 52 102 / 52 539 serwerów MCP na GitHub (99,16%) | \`USER_REPORTED_NOT_INDEPENDENTLY_VERIFIED\`; nie wnioskować o całej populacji repozytoriów. |
| Glama 97 619 serwerów, 28 614 konektorów, 953 010 tools | \`USER_REPORTED_NOT_INDEPENDENTLY_VERIFIED\`; inny mianownik i metoda niż oficjalne registry. |
| mcp.so ~21 tys.; PulseMCP ~16 tys.; mcp.directory ~3 tys.; Smithery ~2 tys.; Top MCPs ~280 | \`USER_REPORTED_NOT_INDEPENDENTLY_VERIFIED\`; rejestry nakładają się i nie są zsumowaną unikalną populacją. |
| Composio 1519 toolkitów; Hugging Face 3,13 mln modeli, 1,08 mln datasets, 1,49 mln Spaces | \`USER_REPORTED_NOT_INDEPENDENTLY_VERIFIED\`; liczby mogą się zmieniać i nie są miarą liczby niezależnych agentów. |
| Composio: case studies, cenniki, SOC/ISO; Top MCPs: punktacja 7 kryteriów | \`USER_REPORTED_NOT_INDEPENDENTLY_VERIFIED\`. Nasza poniższa rubryka **nie** jest algorytmem Top MCPs. |
| GitHub Agentic Workflows: \`mcp-servers\` dla command/container/url/registry | \`OFFICIAL_DOCUMENTATION_CHECKED\`, URL: https://github.github.com/gh-aw/guides/mcps/ |
| Oficjalny MCP Registry, API \`GET /v0.1/servers\` | \`OFFICIAL_DOCUMENTATION_CHECKED\`, URL: https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/api/official-registry-api.md |
| Oficjalny MCP 2026-07-28 (tools/resources/prompts + Streamable HTTP) | \`OFFICIAL_DOCUMENTATION_CHECKED\`, URL: https://modelcontextprotocol.io/specification/2026-07-28 |
| GitLab MCP cursor pagination | \`OFFICIAL_DOCUMENTATION_CHECKED\`, URL: https://docs.gitlab.com/user/model_context_protocol/mcp_server_tools/ |

Weryfikację nazw i raportowane wielkości źródeł przechowuje \`catalog/mcp_ecosystem_sources.json\`. Katalog klasyfikuje Glama, mcp.so, PulseMCP, mcp.directory, Smithery, Top MCPs, GitHub MCP Registry, a także Composio, Nango, Merge, Arcade, Pipedream, Zapier, Cerbos, Hugging Face, smolagents, LlamaIndex/LlamaHub. **Żadne z tych źródeł nie zostało przez ten import automatycznie podłączone ani uruchomione.**

## 2. Ważna korekta transportów

W dostarczonym opracowaniu zdalny MCP opisano przede wszystkim jako \`HTTP+SSE\`. To historyczna wersja: zastąpiona przez **Streamable HTTP** od 2025-03-26. W aktualnym opublikowanym profilu **2026-07-28** Streamable HTTP działa przez endpoint **POST**; opcjonalne SSE stanowi strumień odpowiedzi dla poszczególnego żądania, zaś stary GET strumieniowy i protokolarne sesje zostały usunięte w tej rewizji. Profil 2025-11-25 używał POST/GET; implementacje negocjują wersje i w razie potrzeby obsługują wcześniejsze profile. Komunikacja lokalna \`stdio\` nadal pozostaje standardowym transportem.

Referencje:
- https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/transports/streamable-http.mdx
- https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-11-25/basic/transports.mdx

Rejestr nie instaluje kodu. \`registry\` w GitHub Agentic Workflows jest metadanymi pochodzenia; nie wymusza automatycznej weryfikacji ani nie zapewnia ochrony zewnętrznego serwera. OAuth/OIDC nie są magiczną barierą — wymagają właściwego audytorium tokenu, egzekwowania najmniejszych uprawnień i odrębnej konfiguracji.

## 3. Wdrożenie: MCP Registry Discovery & Admission (OFFLINE)

Źródło: \`omega_builder/mcp_registry.py\` (Python stdlib, brak połączeń sieciowych).

Działania:
- Normalizowanie oficjalnego API \`/v0.1/servers\`: rekord \`{server: {...}, _meta: {...}}\` i dane \`server.json\`.
- Walidacja nazw/version, jawnych wersji pakietów, SHA256 metadanych, repozytoriów HTTPS i remote endpointów; brak aktywnego rozwiązywania DNS.
- Zwrot niezmodyfikowanego \`metadata.nextCursor\` (stronicowanie), deduplikacja po \`name + version\`; w przypadku konfliktu metadanych — błąd.
- Wyliczanie adresu oficjalnego API z parametrami \`search\`, \`version=latest\`, \`updated_since\`, \`cursor\`, **bez wykonywania GET**.
- **Siedmiokryterialna, własna** punktacja 0–100: tożsamość publishera, przegląd źródeł, licencja, przypięta wersja, skan bezpieczeństwa, sandbox, ograniczenie uprawnień. Deklaracje ocen są wejściem od użytkownika; zero automatycznego zaufania nawet przy 100 pkt.
- Ładowanie tylko jawnie wskazanych opisów i struktur JSON Schema narzędzi, z budżetem rozmiaru; \`plan_tool_descriptors\` nigdy nie wykonuje \`tools/call\`.
- Rozróżnienie \`active\`, \`deprecated\`, \`deleted\`, \`unknown\`; starsze/deleted odrzucane nawet przy maksymalnej ocenie.

**Brak funkcji instalującej serwer, pobierającej pakiety, podpisującej OAuth, zakładającej konta, uruchamiającej dowolny proces, autoryzującej płatności, wprowadzającej klucze API czy synchronizującej rejestry w tle.**

### Komendy

~~~bash
python -m omega_builder mcp-sources
python -m omega_builder mcp-registry-url --search filesystem
python -m omega_builder mcp-registry-url --updated-since 2026-10-09T00:00:00Z
python -m omega_builder mcp-intake examples/mcp_registry_page.json
python -m omega_builder mcp-assess examples/mcp_candidate_review.json
python -m omega_builder mcp-tool-plan examples/mcp_tool_plan.json
python -m unittest discover -s tests -v
~~~

Wszystkie trzy pliki \`examples/mcp_*.json\` są **syntetycznymi danymi testowymi**. Nie stanowią rzeczywistego wyniku aktualnego skanowania 97 tys. serwerów.

## 4. Ryzyka i priorytety rozwojowe

**Supply chain**: złośliwy wpis do katalogu / typosquatting, nieprzypięty pakiet, podmiana repozytorium lub release, utrata kontroli nad domeną. Konieczne jest weryfikowanie wydawcy, przypięcie digestów oraz ponowne sprawdzanie metadanych bezpośrednio przed uruchomieniem.

**MCP prompt injection**: nazwy, opisy narzędzi i wyniki zasobów są niezaufane. Katalog zachowuje wyłącznie opisowe metadane; rzeczywisty executor musi przestrzegać uprawnień przy **każdym** wywołaniu, nie jedynie podczas discovery.

**Transport**: HTTPS nie chroni automatycznie przed SSRF / DNS rebinding / przekazaniem bearer tokenu do obcego odbiorcy. Kontrolowany endpoint, audience/resource binding, allowlisted egress, rewizja redirectów i izolacja sieci muszą być w osobnym produkcyjnym kliencie MCP.

**OAuth**: integracje typu Composio/Nango/Arcade są kandydatami przyszłych adapterów. Nie przechowujemy w repozytorium sekretów ani tokenów. Wystawienie ich do logów i narzędzi modelu byłoby niedopuszczalne.

**Ekonomia M2M i L402**: automatyczne odblokowanie płatnych API stablecoinami jest **poza zakresem**. W przyszłości wymagany byłby osobny cennik, limity, audyt, jawne zatwierdzenie wydatku, zgodność prawna i ochrona przed nadużyciem.

**RAG / Hugging Face / LlamaIndex / smolagents**: do rozważenia adaptery do danych/modeli, ale bez traktowania liczby modeli czy Spaces jako potwierdzenia jakości, licencji lub uprawnień. Dla RAG niezbędne punktowe odniesienia do dokumentów, provenance, izolacja tenantów, pomiar recall/latencji i polityka retencji.

**GitHub/GitLab**: przyszły skaner musi respektować kursory po stronie API, limity wywołań i uprawnienia; nigdy nie zakładać, że pusta strona oznacza koniec przy \`hasNextPage=true\`.

### Status

| Komponent | Status |
|---|---|
| Lokalne snapshoty, normalizacja, ranking, page cursor, plan schematów | \`IMPLEMENTED_OFFLINE\` |
| CLI, źródłowy katalog i testy błędów walidacji | \`IMPLEMENTED\` |
| Real-time crawling Glama, PulseMCP, GitHub Registry, Hugging Face | \`NOT_CONNECTED\` |
| Remote MCP Streamable HTTP 2026-07-28 client / hostowany MCP server | \`NOT_IMPLEMENTED\` |
| Instalator kontenerów i code-scan supply-chain | \`NOT_IMPLEMENTED\` |
| OAuth/PKCE/OIDC delegated access, token refresh, per-tool execution scopes | \`REQUIRES_CONNECTORS_AND_SECURITY_REVIEW\` |
| SaaS billing i agentowe zakupy L402 | \`DENIED_NO_BUDGET_OR_APPROVAL\` |
| AGENT ARCHITEKT OMEGA ZEUS INFINITY | **\`ON_HOLD_AWAITING_USER_MATERIAL\`** |

Repozytorium rozwijamy wyłącznie na \`main\`; import katalogu nie odblokowuje agenta Zeus.
