# Ewaluacja: uzp_training

Wygenerowano: 2026-11-21 12:48

Metryka: F1 na poziomie pól (wartości `null` nie są liczone; błędna wartość = FP + FN).

## Podsumowanie

| | TP | FP | FN | Precision | Recall | F1 (strict) | F1 (lenient) |
|---|---|---|---|---|---|---|---|
| **RAZEM** | 360 | 0 | 1672 | 1.000 | 0.177 | **0.301** | 0.301 |
| odwolanie (60 dok.) — brak definicji YAML | 0 | 0 | 1214 | 0.000 | 0.000 | **0.000** | 0.000 |
| pelnomocnictwo (60 dok.) — brak definicji YAML | 0 | 0 | 458 | 0.000 | 0.000 | **0.000** | 0.000 |
| przelew (60 dok.) | 360 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |

## odwolanie

| Pole | TP | FP | FN | Precision | Recall | F1 (strict) | F1 (lenient) |
|---|---|---|---|---|---|---|---|
| `OdwolanieKIO.czynnosc_dzien` | 0 | 0 | 60 | 0.000 | 0.000 | **0.000** | 0.000 |
| `OdwolanieKIO.czynnosc_opis` | 0 | 0 | 60 | 0.000 | 0.000 | **0.000** | 0.000 |
| `OdwolanieKIO.czynnosc_powod_id` | 0 | 0 | 60 | 0.000 | 0.000 | **0.000** | 0.000 |
| `OdwolanieKIO.data` | 0 | 0 | 45 | 0.000 | 0.000 | **0.000** | 0.000 |
| `OdwolanieKIO.miejscowosc` | 0 | 0 | 45 | 0.000 | 0.000 | **0.000** | 0.000 |
| `Odwolujacy[].krs` | 0 | 0 | 56 | 0.000 | 0.000 | **0.000** | 0.000 |
| `Odwolujacy[].nazwa` | 0 | 0 | 60 | 0.000 | 0.000 | **0.000** | 0.000 |
| `Odwolujacy[].nip` | 0 | 0 | 60 | 0.000 | 0.000 | **0.000** | 0.000 |
| `Odwolujacy[].pelnomocnik.imie_nazwisko` | 0 | 0 | 60 | 0.000 | 0.000 | **0.000** | 0.000 |
| `Odwolujacy[].pelnomocnik.mail` | 0 | 0 | 60 | 0.000 | 0.000 | **0.000** | 0.000 |
| `Odwolujacy[].pelnomocnik.nazwa` | 0 | 0 | 60 | 0.000 | 0.000 | **0.000** | 0.000 |
| `Odwolujacy[].przez-pelnomocnika` | 0 | 0 | 60 | 0.000 | 0.000 | **0.000** | 0.000 |
| `Odwolujacy[].regon` | 0 | 0 | 60 | 0.000 | 0.000 | **0.000** | 0.000 |
| `Zamawiajacy[].krs` | 0 | 0 | 58 | 0.000 | 0.000 | **0.000** | 0.000 |
| `Zamawiajacy[].nazwa` | 0 | 0 | 63 | 0.000 | 0.000 | **0.000** | 0.000 |
| `Zamawiajacy[].nip` | 0 | 0 | 63 | 0.000 | 0.000 | **0.000** | 0.000 |
| `Zamawiajacy[].prowadzacy_postepowanie` | 0 | 0 | 6 | 0.000 | 0.000 | **0.000** | 0.000 |
| `Zamawiajacy[].regon` | 0 | 0 | 63 | 0.000 | 0.000 | **0.000** | 0.000 |
| `ZamowieniePubliczne.numer_bzp` | 0 | 0 | 48 | 0.000 | 0.000 | **0.000** | 0.000 |
| `ZamowieniePubliczne.numer_postepowania` | 0 | 0 | 60 | 0.000 | 0.000 | **0.000** | 0.000 |
| `ZamowieniePubliczne.numer_ted` | 0 | 0 | 47 | 0.000 | 0.000 | **0.000** | 0.000 |
| `ZamowieniePubliczne.tytul` | 0 | 0 | 60 | 0.000 | 0.000 | **0.000** | 0.000 |

Przykładowe błędy (3 z 1200):

- `przyklad_01` `OdwolanieKIO.czynnosc_dzien`: oczekiwano ["2026-03-20"], otrzymano []
- `przyklad_01` `OdwolanieKIO.czynnosc_opis`: oczekiwano ["Decyzja o unieważnieniu postępowania"], otrzymano []
- `przyklad_01` `OdwolanieKIO.czynnosc_powod_id`: oczekiwano [9], otrzymano []

## pelnomocnictwo

| Pole | TP | FP | FN | Precision | Recall | F1 (strict) | F1 (lenient) |
|---|---|---|---|---|---|---|---|
| `mocodawca[].data.imie_nazwisko` | 0 | 0 | 4 | 0.000 | 0.000 | **0.000** | 0.000 |
| `mocodawca[].data.krs` | 0 | 0 | 62 | 0.000 | 0.000 | **0.000** | 0.000 |
| `mocodawca[].data.nazwa` | 0 | 0 | 66 | 0.000 | 0.000 | **0.000** | 0.000 |
| `mocodawca[].data.nip` | 0 | 0 | 66 | 0.000 | 0.000 | **0.000** | 0.000 |
| `mocodawca[].data.typ` | 0 | 0 | 66 | 0.000 | 0.000 | **0.000** | 0.000 |
| `mocodawca[].podpisujacy[].imie_nazwisko` | 0 | 0 | 95 | 0.000 | 0.000 | **0.000** | 0.000 |
| `pelnomocnicy[].imie_nazwisko` | 0 | 0 | 98 | 0.000 | 0.000 | **0.000** | 0.000 |
| `pelnomocnicy[].pesel` | 0 | 0 | 1 | 0.000 | 0.000 | **0.000** | 0.000 |

Przykładowe błędy (3 z 361):

- `przyklad_01` `mocodawca[].data.krs`: oczekiwano ["9999405188"], otrzymano []
- `przyklad_01` `mocodawca[].data.nazwa`: oczekiwano ["Belmoria Rozwiązania S.A."], otrzymano []
- `przyklad_01` `mocodawca[].data.nip`: oczekiwano ["9999284065"], otrzymano []

## przelew

| Pole | TP | FP | FN | Precision | Recall | F1 (strict) | F1 (lenient) |
|---|---|---|---|---|---|---|---|
| `przelew_bankowy.data_operacji` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.kwota` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.na_rachunek` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.numer_transakcji` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.tytul` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.z_rachunku` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
