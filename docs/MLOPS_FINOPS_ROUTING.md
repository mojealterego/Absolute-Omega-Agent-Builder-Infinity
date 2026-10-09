# MLOps, FinOps i dynamiczny routing Frontier ↔ Edge

## Zakres

Źródło PDF wymaga monitoringu FinOps/MLOps, TCO, A/B, shadow deployments i lokalnego fallbacku inferencji. Ta aktualizacja dodaje projekt rozszerzenia o budżetowanie **na podstawie rzeczywistych cen podanych przez operatora**, a nie niezweryfikowanych stawek producenta.

### Wymagany schemat zdarzenia metrycznego

| Pole | Wymaganie |
|---|---|
| `request_id`, `run_id`, `agent_id`, `model_id` | Powiązanie kosztu z wywołaniem, bez promptu i PII w logu |
| `input_tokens`, `output_tokens`, `cached_tokens` | Faktyczne zużycie od dostawcy, fallback do estymacji oznaczony jako szacunek |
| `unit_input_usd_per_million`, `unit_output_usd_per_million` | Wersjonowany cennik / konfiguracja użytkownika |
| `estimated_cost_usd`, `actual_cost_usd` | Oddzielenie estymacji od rozliczonego zużycia |
| `p50_ms`, `p95_ms`, `p99_ms`, `api_error_rate` | Monitorowanie SLO i degradacji |
| `quality_eval`, `drift_signal`, `fallback_reason` | Kontrola regresji i przyczyny routingu |

### Ograniczenia budżetu

Dla modelu `m`: `C_m = T_in * P_in(m) / 1e6 + T_out * P_out(m) / 1e6 + C_infra(m)`, gdzie `C_infra` obejmuje prąd, sprzęt, chmurę, amortyzację i utrzymanie dla Edge/On-Prem. Samo naliczenie `0 USD` za lokalne tokeny nie oznacza zerowego TCO.

Wybierz model minimalizujący `C_m` przy warunkach `Q_m >= Q_min`, `L_m <= L_max`, budżet, polityka prywatności, dostępność i zdrowie dostawcy. `Q_m` ma pochodzić z walidowanych benchmarków właściwej domeny, nie z losowego confidence score. Model nie spełniający wymagań nie może być użyty tylko dlatego, że jest tańszy.

### Fallback

- **Circuit breaker:** dla 429/5xx/timeout zastosować bounded retry z exponential backoff; nie retry 400/401 bez zmiany konfiguracji.
- **Frontier → Edge:** gdy API zawiedzie albo przekroczony zostanie budżet, przełączyć tylko na zdrowy lokalny model **spełniający próg jakości i uprawnienia**; w przeciwnym razie brak automatycznej odpowiedzi i eskalacja do operatora.
- **Edge → Frontier:** gdy lokalny model nie spełnia progu jakości lub limitu czasu i polityka danych pozwala na eksport.
- **Ochrona kosztów:** limit dzienny, na zadanie, na legiony; blokada gdy brak wystarczającego budget reserve, reconciliation po odpowiedzi.
- **MLOps:** health, drift, shadow traffic z anonimizacją, testy A/B, raporty błędów i zaobserwowany latency.

**Status:** specyfikacja i testowalny katalog; produkcyjny licznik tokenów, system billingowy, router żądań i modele nie są jeszcze podłączone.
