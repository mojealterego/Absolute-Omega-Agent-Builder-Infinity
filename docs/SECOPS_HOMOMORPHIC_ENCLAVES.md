# SecOps: szyfrowanie homomorficzne, enclaves, VRAM i ochrona wag

**Ważne ograniczenie:** zaszyfrowane obliczenia homomorficzne (FHE/HE) i sprzętowe TEE są **odmiennymi technikami**. Standardowe CUDA/VRAM nie daje dziś automatycznie efektywnego obliczania dowolnych modeli LLM wyłącznie na zaszyfrowanych tensorach.

| Mechanizm | Możliwość | Ograniczenie |
|---|---|---|
| Homomorphic encryption (CKKS/BFV/BGV) | Wybrane operacje arytmetyczne na szyfrogramach; potencjalne prywatne obliczenia macierzowe | Nieliniowości, bootstrapping, pamięć, precyzja i znaczący koszt obliczeniowy; wymagany profiling i osobny pipeline |
| TEE / confidential computing | Izolacja wybranych obszarów wykonania i atestacja | Nie każda enklawa obejmuje GPU/VRAM, trzeba sprawdzić konkretny sprzęt i driver |
| Model weight encryption at rest | Szyfrowanie wag w spoczynku | Wagi mogą być odszyfrowywane w pamięci podczas inferencji; osobna ochrona w użyciu |
| mTLS, envelope encryption, KMS | Ochrona transportu, materiałów kluczowych i dostępu | Nie dowodzi ochrony danych po odszyfrowaniu |
| Differential privacy / confidential inference | Ograniczenia ryzyka danych na wyjściu i etapie treningu | Nie są substytutem weryfikacji dostępu ani GPU attestation |

Wymagania integracyjne: odrębny threat model, testy atestacji, model dostępu do pamięci GPU, unieważnianie kluczy, przywracanie po awarii, side-channel assessment, backup i audyt. Nie należy twierdzić, że „nikt nawet administrator nie może odczytać VRAM” bez analizy sprzętu.

**Status w repo: blueprint / badanie, bez implementacji FHE, TEE i operacji na zaszyfrowanych wagach.**
