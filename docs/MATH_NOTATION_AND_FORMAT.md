# Spójna notacja matematyczna i format tabel (Vol. 1)

Oryginalny PDF ma 793 strony i zachowuje się jako **niezmieniona dokumentacja źródłowa**. Niniejszy plik jest **kanoniczną poprawką formatowania w repozytorium**, bez niszczenia cytatów z PDF.

## 1. Równanie Bellmana (dla ustalonej polityki)

$$
V^{\pi}(s)=\sum_{a}\pi(a\mid s)\left[R(s,a)+\gamma\sum_{s'}P(s'\mid s,a)V^{\pi}(s')\right].
$$

- `V^{\pi}(s)`: wartość oczekiwanego zdyskontowanego zwrotu przy polityce `\pi`.
- `\pi(a\mid s)`: prawdopodobieństwo wyboru akcji `a` w stanie `s`.
- `R(s,a)`: oczekiwana nagroda natychmiastowa; `\gamma\in[0,1)` jest czynnikiem dyskontowym.
- `P(s'\mid s,a)`: prawdopodobieństwo przejścia do `s'` po podjęciu `a`.

## 2. Koszt routingu modelu

$$
C(m)=\frac{t_{\rm in}\,p_{\rm in}(m)+t_{\rm out}\,p_{\rm out}(m)}{10^6}+c_{\rm infra}(m),
\quad m^*=\arg\min_{m\in\mathcal F}C(m)
$$

Zbiór dopuszczalny `\mathcal F` uwzględnia jakość, latency, zdrowie usług, budżet i politykę lokalizacji danych.

## 3. Pozostałe notacje

- Cosine similarity: `\operatorname{cos}(x,y)=(x\cdot y)/(\|x\|\|y\|)` tylko dla wektorów niezerowych.
- Głosowanie większościowe: `\hat y=\arg\max_y\sum_{i=1}^k\mathbb 1[y_i=y]`.
- Bizantyjska tolerancja błędów `N\ge 3f+1` jest własnością **konkretnych protokołów i założeń**, nie automatycznie wszystkich rojów.
- LangGraph: graf może mieć cykle; **DAG** oznacza graf acykliczny.
- Zenoh `p99<1 ms` to cel pomiarowy, nie gwarancja.

## 4. Konwencja nagłówków

- Jeden `#` na dokument, główne sekcje `##`, podsekcje `###`; nie restartować numeracji `1.` bez identyfikatora rozdziału.
- W każdej tabeli nagłówki w pojedynczym wierszu, równa liczba komórek we wszystkich wierszach, status realizacji w oddzielnej kolumnie.
- Zewnętrzny produkt ≠ framework SDK ≠ wzorzec ≠ realny runtime. Stosować pole `status`.
- Matematyka blokowa w `$$...$$`, zmienne inline w `$...$`.

Źródło: strony 1–19 dokumentu wejściowego, m.in. Bellman na s. 4, MLOps s. 16, SNN s. 13.
