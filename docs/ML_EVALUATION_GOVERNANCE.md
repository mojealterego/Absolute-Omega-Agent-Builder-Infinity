# ML Evaluation, Redukcja Wymiarów, Wizualizacja i Data Governance

## Zakres i realność implementacji — 115–125, 165–200

| Funkcja | Kod | Status i ograniczenia |
|---|---|---|
| LDA (Linear Discriminant Analysis) | omega_builder/ml_embeddings.py | Działający adapter scikit-learn, opcjonalna instalacja '.[ml]'; uczy się **tylko na treningowych X i y**. |
| t-SNE | omega_builder/ml_embeddings.py | Działające sklearn TSNE; n<2001, perplexity<n, tylko fit_transform eksploracyjne, bez oceny jakości predykcyjnej. |
| UMAP | omega_builder/ml_embeddings.py | Działający adapter umap-learn; wymaga '.[umap]'; bez gwarancji zachowania globalnych odległości. |
| Autoenkoder | omega_builder/ml_embeddings.py | Rzeczywiście trenowany niewielki 1-hidden-layer tanh encoder–decoder (NumPy/backprop/SGD), cel MSE. Wymaga normalizacji danych i '.[math]'. |
| Histogram / box / scatter / heatmap | omega_builder/ml_visualization.py | Statystyki wykresów w Pythonie stdlib, zapis prawdziwego PNG wymaga '.[visual]'. Żadne generowane obrazy nie są symulacjami LLM. |
| Pearson i Spearman | omega_builder/mathematics/statistics.py | Oba działające: Spearman oblicza Pearsona na średnich rangach przy remisach; zero-wariancja odrzucana. |
| Train / validation / test | omega_builder/ml_validation.py | Rozłączne indeksy, seed, stratified; warianty małych klas odrzucane zamiast niejawnie tracić etykiety. Proporcja 80/20 NIE jest obowiązkową stałą. |
| K-fold / stratified / LOOCV | omega_builder/ml_validation.py | Prawdziwe podziały, bez uczenia modeli przez sam walidator. LOOCV max 1000 rekordów. |
| Klasyfikacja / imbalance | omega_builder/ml_validation.py | Accuracy, balanced accuracy, macro-F1, precision, recall, confusion matrix. Rzetelna ocena rzadkich klas wymaga odpowiednich metryk. |
| SMOTE + under-/oversampling | omega_builder/ml_validation.py | Interpolacja kNN rzeczywistych NUMERYCZNYCH przykładów mniejszości; wyłącznie podzbiór treningowy, wymaga >= k+1 mniejszości. Nie stosować do testu. |
| Numeryczne dane syntetyczne i augmentacja | omega_builder/ml_validation.py | W pełni reprodukowalne szumy Gaussa na TRAIN i niezależne próbki Gaussa z jawnych parametrów; NIE gwarantują prywatności i zachowania etykiet. |
| Data drift / Concept drift | omega_builder/ml_validation.py, omega_builder/ml_governance.py | KS two-sample, PSI smoothing reference bins. Concept drift: obserwowana zmiana skuteczności przy dostępnych prawdziwych etykietach, nie dowód przyczynowy. |
| Feature / data leakage | omega_builder/preprocessing.py, omega_builder/ml_governance.py | Fit-only-on-train i detektor duplikatów pomiędzy splitami; brak dostępu do testowych danych w preprocessingu. |
| Quality / weak supervision | omega_builder/ml_governance.py | Missing values, duplikaty, weak-label literal keywords (abstain); **nie Snorkel**, nie eksploitacje regex. |
| PII / GDPR | omega_builder/ml_governance.py | HMAC-SHA256 pseudonimizacja; best-effort maskowanie emaili / 11 cyfr. Nie pełna anonimizacja, nie certyfikat zgodności. |
| Bias / data poisoning | omega_builder/ml_governance.py | Diagnostyka selection-rate gap, TPR/FPR według grup, konfliktów identycznych obserwacji. Brak automatycznego dowodu sprawiedliwości lub odporności na poisoning. |
| Data lineage | omega_builder/storage.py | Poprzednio utworzony lokalny zapis lineage w SQLite; brak integracji z zewnętrznym data catalog. |
| UMAP / LDA model serving / MLOps dashboard | — | Docelowe integracje produkcyjne nie są aktywne. |
| Snorkel / benchmark MNIST/ImageNet/COCO / aktywne etykietowanie UI | — | Zgłoszone jako wymagania do następnej warstwy. |
| Synthetic Data & privacy | — | Nie tworzymy fałszywych kart pacjentów ani nie twierdzimy, że dane syntetyczne automatycznie obchodzą przepisy RODO. |

## Uruchomienie

Bez dodatkowych zależności działają podziały, walidacje, SMOTE dla liczbowych macierzy, governance, PSI/KS oraz przygotowanie danych wykresów.

~~~sh
python -m unittest discover -s tests -v
python -m omega_builder math-ops
python -m omega_builder math examples/ml_stratified_split.json

pip install '.[ml]'       # NumPy + scikit-learn, LDA, t-SNE
pip install '.[umap]'     # UMAP, NumPy, scikit-learn
pip install '.[visual]'   # matplotlib, PNG
pip install '.[math]'     # NumPy, trenowany autoencoder
~~~

Interfejs JSON jest whitelisted; bez \`eval\`, bez sieci i bez systemowego zapisu plików. Prywatny sekret HMAC oraz bezpośredni zapis obrazów nie są wystawione przez publiczne wejście JSON.

Przykład manualnej orkiestracji:

~~~python
from omega_builder.ml_validation import split_indices, kfold_indices, psi, smote_train
from omega_builder.ml_governance import split_overlap
from omega_builder import preprocessing
X = [[float(i)] for i in range(12)]
y = ["small"]*6 + ["large"]*6
parts = split_indices(len(X), .2, .2, 123, y)
train = [X[i] for i in parts["train"]]
validation = [X[i] for i in parts["validation"]]
test = [X[i] for i in parts["test"]]
assert not split_overlap(train, validation, test)["potential_leakage"]
# fit on train; transform validation and test using identical fitted parameters
train_rows=[{"x":row[0]} for row in train]
fit=preprocessing.fit_numeric(train_rows,"x")
Xv=preprocessing.transform_numeric([{"x":row[0]} for row in validation],fit)
~~~

### Uwagi merytoryczne

- **LDA** nie jest tożsame z **PCA**: LDA wykorzystuje etykiety (supervised), PCA nie.
- **t-SNE** i **UMAP** nie stanowią iteracji jeden drugiego; różnią się celami i obiektywami optymalizacyjnymi. UMAP ma podstawy topologiczne, ale nie daje automatycznej gwarancji wiernej geometrii globalnej.
- **Pearson** mierzy zależność liniową także przy szumie; wartość 1/-1 oznacza doskonałą zależność liniową. **Spearman** mierzy związek monotoniczny na rangach.
- Poprawność na **validation** nie jest równoznaczna z nieobciążonym końcowym testem. Proporcje splitów dobiera się do danych.
- **SMOTE przed splitem** zanieczyszcza ewaluację. Używamy po oddzieleniu train i po fit preprocessingu dla train. To reguła proceduralna; kod przyjmujący macierz nie weryfikuje pochodzenia wierszy.
- Metryki mniejszości (recall, precision, PR-AUC, F1) są kluczowe; accuracy może maskować porażkę.
- **Data Drift** ≠ **Concept Drift**: PSI/KS badają rozkład cech, a skuteczność oceniona na etykietach jest obserwacją zmian performance, nie dowodem przyczynowego driftu.
- „Dane syntetyczne omijają RODO” i „PESEL ukryty przez regex jest anonimowy” — twierdzenia fałszywe. Pseudonim pozostaje potencjalnie danymi osobowymi.
- Nawet formalne testy statystyczne nie gwarantują absence of bias, security ani pełnej jakości zbioru.

Zeus: ON_HOLD_AWAITING_USER_MATERIAL.
**Uzupełnienie bieżące:** testy remisów Spearmana, reproducible random under/oversampling, train-only Gaussian noise augmentation i reference independent Gaussian sampler zostały dodane do matematycznego interfejsu JSON. Nie przedstawiamy tego jako GAN ani pełnego generatora syntetycznych danych dla medycyny.
