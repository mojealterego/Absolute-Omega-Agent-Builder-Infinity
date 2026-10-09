# Mathematical Reasoning Core — Bloki V–VIII

Status: DZIAŁAJĄCE PRYMITYWY offline, nie agent Zeus i nie samodzielna inteligencja AGI/ASI. Stan Zeusa: ON_HOLD_AWAITING_USER_MATERIAL.

## Funkcjonalność

| Moduł | Używane prymitywy | Gwarancje |
|---|---|---|
| Algebra liniowa V | mat, vec, iloczyny, transpozycja, determinant, LU z pivoting, QR Householder, Cholesky, solve/inverse, norma L1/L2/Linf, cosine, cross/dot, symetria/ortogonalność/diagonalność | Realne obliczenia float, testowane powrotne relacje PA≈LU, A≈QR i A≈LLᵀ. |
| Algebra dokładna V | solve_exact, Fraction | Weryfikacja dokładnej równości Ax=b na podanych skończonych ułamkach; nie jest to dowód dowolnego programu. |
| SVD V | svd przez numpy.linalg.svd | Działa po instalacji opcjonalnego pakietu math. Bez NumPy jawny błąd, nigdy imitacja wyniku. |
| Rachunek VI | pochodne centralne, gradient, hesjan, jakobian, Simpson, bounded gradient descent | Przybliżenie numeryczne; nie obiecuje globalnego optimum. |
| Logika VII | AND/OR/NOT/XOR/IMPLIES/IFF, tautologia, kontrprzykład, wynikanie, finite forall/exists | Tablice prawdy wyczerpująco dla <=12 zmiennych; dokładny dowód jedynie w przyjętej semantyce i skończonej domenie. |
| Grafy VII | Dijkstra, topo sort, wykrywanie cykli, laplasjan grafu | Bounded graf, wagi nieujemne, osobne sprawdzanie DAG. |
| Prawdopodobieństwo VIII | Bayes, conditional, expectation, variance, Shannon entropy, cross entropy, KL, Gauss PDF | Walidacja rozkładów i argumentów. |

## Jak używać

Przykład CLI:

    python -m omega_builder math-ops
    python -m omega_builder math examples/math_exact_linear.json
    python -m omega_builder math examples/math_propositional_validity.json
    python -m unittest discover -s tests -v
    pip install '.[math]'  # NumPy SVD

Przykład biblioteczny:

    from omega_builder.mathematics import linear, logic
    result=linear.solve_exact([[2,1],[1,-1]],[1,0])
    assert result["verified"] and result["solution"]==["1/3","1/3"]
    assert logic.check_validity(("or",("var","p"),("not",("var","p"))))["valid"]

Przy integracji z przyszłym DGM biblioteka może weryfikować konkretnie sformułowane warunki algebraiczne i skończone modele logiczne. Nie weryfikuje dowolnego kodu, bezpieczeństwa mutacji, aksjomatów CEV, ani uniwersalnej zgodności wartości człowieka. Takie dowody wymagają osobnych formalnych specyfikacji i narzędzi Lean, Z3, Coq, TLA+ oraz własnych testów.

Implementacja celowo limituje rozmiary danych (64×64 dla float, 16×16 dla exact, 12 zmiennych w logicznym truth-table i 1000 węzłów w grafie). Brak dostępu do sieci. Komendy z JSON działają wyłącznie z listy dozwolonych operacji.

Uściślenia merytoryczne: DAG to graf skierowany acykliczny, nie każdy graf skierowany. QR factorization nie oznacza gotowego iteracyjnego algorytmu wartości własnych. Rzeczywiste zabezpieczenia DGM i decyzje o wdrażaniu muszą być poza tym modułem.

## Aktualizacja: statystyka, teoria informacji i preprocessing

Dołączono moduły `statistics.py`, `information.py` i `preprocessing.py` oraz offline `storage.py`. Interfejs JSON udostępnia wybrane wywołania przez `python -m omega_builder math-ops`. SQLite jest dostępny jedynie przez Python API. Szczegóły i ograniczenia w [STATISTICS_DATA_ENGINEERING.md](STATISTICS_DATA_ENGINEERING.md).
