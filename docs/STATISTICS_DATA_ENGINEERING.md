# Statystyka, teoria informacji i Data Engineering — etap praktyczny

## Dostarczone implementacje (rzeczywiste, offline)

| Dziedzina | Implementacja | Ograniczenia / jednostki |
|---|---|---|
| Korelacja / kowariancja | Pearson (undefined przy stałym wektorze), sample covariance, sample variance, MLE momentów | Tylko finitywne float, próba ograniczona |
| Rozkłady | Bernoulli, binomial, Poisson, Gauss CDF + dotychczasowa PDF, Exponential PDF/CDF, Uniform PDF, Beta PDF, Gamma PDF | Gamma(shape, scale), Exp(rate), Poisson(rate); Beta tylko wnętrze (0,1) |
| Estymacja | MLE Bernoulli i Gaussian; beta-binomial posterior mean i MAP mode | Posterior mode może leżeć na brzegu; wtedy jawny błąd zamiast nieprawidłowej formuły |
| Stochastyka | Markov row-stochastic transition, deterministycznie seedowany random walk i Monte Carlo pi | Monte Carlo daje estymatę, nie dowód ani prognozę rynkową |
| Informacja | H(Y|X), I(X;Y), H(X,Y), Shannon–Hartley, SNR dB, Huffman encode/decode | Joint PMF sumuje się do 1; pojemność wymaga modelu kanału AWGN; bitstream nie zawiera automatycznie kodbook |
| Preprocessing | fit_numeric / transform_numeric, one-hot fit/transform, outlier flags IQR, deduplicate | Fit na zbiorze treningowym. Nie usuwa automatycznie istotnych anomalii |
| PCA | `preprocessing.pca_fit`, `pca_transform`, prawdziwe NumPy SVD | `pip install '.[math]'`; fit tylko train; projekcja test bez ponownego fit |
| SQLite | KV, graf relacji, series, cosine-search po jawnych wektorach, lineage, bitemporal events | Lokalny węzeł, wyłącznie SQL SQLite; nie jest to NoSQL distributed, ANN, GraphDB ani Lakehouse |

## Przykłady

CLI (tylko operacje z allowlisty, bez `eval`):

~~~bash
python -m omega_builder math-ops
python -m omega_builder math examples/statistics_binomial.json
python -m omega_builder math examples/information_mutual.json
python -m unittest discover -s tests -v
~~~

API Pythona:

~~~python
from omega_builder.mathematics import statistics as s, information as info
from omega_builder import preprocessing as pre
from omega_builder.storage import SQLiteKnowledgeStore

assert abs(s.binomial_pmf(2, 3, .5) - .375) < 1e-12
assert abs(info.mutual_information([[.5,0],[0,.5]]) - 1) < 1e-12
train = [{"x":1}, {"x":3}, {"x":None}]
model = pre.fit_numeric(train,"x")
z_test = pre.transform_numeric([{"x":5}],model)  # NO leakage: fitted only on train
with SQLiteKnowledgeStore() as store:
    store.put_kv("model_quality", {"status":"measured"}, "benchmark")
    store.add_relation("dataset", "evaluated_by", "benchmark-2026")
    store.add_temporal_fact("state", "old", 0, 100, 10, "event-log")
    store.add_temporal_fact("state", "corrected", 0, 100, 20, "human-revision")
    assert store.fact_at("state",50,15)["value"] == "old"
    assert store.fact_at("state",50,25)["value"] == "corrected"
~~~

## Korekty źródła i rygor pomiarowy

- **Pearson** mierzy liniową zależność, nie dowodzi przyczynowości. Zerowa wariancja: korelacja niezdefiniowana.
- **Rozkłady Beta i Gamma** nie są identyczne: Gamma przyjmuje parametry *shape, scale*, podczas gdy wykładniczy używa *rate*.
- **MLE Gaussian** daje estymator wariancji z mianownikiem `n`, nie bezstronny `n−1`; `sample_variance` używa `n−1`.
- **Prawo wielkich liczb / CLT** wymagają właściwych założeń. CLT nie obowiązuje wszystkich rozkładów bezwarunkowo, np. bez odpowiednich warunków na wariancję i zależności obserwacji.
- **MI ≠ przyczynowość**; **KL nie jest metryką** (asymetria, potencjalnie nieskończona wartość).
- **Przepustowość Shannon–Hartley** jest teoretyczną pojemnością kanału AWGN w określonych założeniach, nie prędkością gwarantowaną aplikacji.
- **Huffman** optymalizuje średnią długość kodu prefixowego przy znanej dystrybucji; koszt kodbooka i framingu nie znika.
- Procenty „10% strukturalnych / 90% niestrukturalnych danych internetu”, „80% czasu analityka” itp. nie są przyjmowane za zweryfikowane parametry architektoniczne.
- **Feature leakage:** wszystkie parametry imputacji, kodowania, PCA i skali muszą być dopasowane wyłącznie na train i zastosowane bez zmiany na validation/test. Lekcje do aktywnego drift monitoringu pozostają roadmapą.
- Powtórzony wpis „Dane strukturalne” w dostarczonym materiale jest deduplikowany logicznie, nie liczymy go jako dwóch umiejętności.

**Status:** częściowa realizacja kolejnego materiału. Brak automatycznej generacji embeddings, serwerów Neo4j/Qdrant, Spark/Delta Lake, integracji produkcyjnej. Nie stworzono Zeusa.