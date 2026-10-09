# Formalna weryfikacja i model checking: TLA+ / Alloy

## Model problemu

Podstawowym zagrożeniem dla rojów jest przypisanie jednego zadania wielu wykonawcom, zakleszczenie kolejki, zgubiona odpowiedź i niespójny commit. Dodano dwa modele referencyjne:

- `specs/SwarmMailbox.tla` + `specs/SwarmMailbox.cfg`: stan `queued / leased / done`, atomowe claim/complete/release, ograniczona liczba zasobów.
- `specs/SwarmMailbox.als`: relacyjny, statyczny niezmiennik „jedno zadanie — najwyżej jeden wykonawca” i „jeden wykonawca — najwyżej jedno zadanie”.

### Własności i zakres

| Własność | Sformalizowana | TLC / Alloy uruchomione? |
|---|---|---|
| TypeOK, exclusive task lease, worker capacity | Tak | **Nie: zależności TLC i Alloy nie są podłączone do CI** |
| Brak zakleszczenia w modelu małej kolejki | Tak, TLA+ | Nie |
| Fairness / eventual completion przy awarii sieci | Wymaga dalszego modelu | Nie |
| Exactly-once side effects / Byzantine consensus | **Nieobjęte** | Nie |

Dodano także offline `omega_builder/protocol_model.py` eksplorujący skończony graf stanów ze sprawdzaniem lease/owner/worker i wykrywaniem deadlock; testy nie zastępują TLC/Alloy.

Model checking udowadnia własności tylko wobec jawnie zapisanej specyfikacji, ograniczeń i eksplorowanych stanów, **nie** oznacza matematycznego dowodu braku wszystkich błędów w produkcyjnym roju.

Przed dopuszczeniem do wdrożenia: uruchomić TLC i Alloy, sprawdzić zakres domen (minimum 2 task, 2 workers, rozłączne żądania), zapisać counterexamples i sha narzędzia. Następnie chaos tests i wyścigi na realnych kolejach RPC, w tym retries, late callbacks, egress i cancellation. Dopiero wtedy aktualizować status integracji.

Powiązanie z Zeusem: pozostaje planem walidacji przyszłego agenta, **nie jest jego implementacją**.
