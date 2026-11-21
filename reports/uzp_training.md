# Ewaluacja: uzp_training

Wygenerowano: 2026-11-21 13:31

Metryka: F1 na poziomie pól (wartości `null` nie są liczone; błędna wartość = FP + FN).

Typ dokumentu do ekstrakcji: **z klasyfikatora** (pełny pipeline).

## Podsumowanie

| | TP | FP | FN | Precision | Recall | F1 (strict) | F1 (lenient) |
|---|---|---|---|---|---|---|---|
| **RAZEM** | 2027 | 5 | 5 | 0.998 | 0.998 | **0.998** | 0.998 |
| odwolanie (60 dok.) | 1209 | 5 | 5 | 0.996 | 0.996 | **0.996** | 0.996 |
| pelnomocnictwo (60 dok.) | 458 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| przelew (60 dok.) | 360 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |

## Klasyfikacja

Trafność: **1.000** (182/182)

| oczekiwany \ przewidziany | odwolanie | pelnomocnictwo | przelew | ∅ (nierozpoznany) |
|---|---|---|---|---|
| odwolanie | 61 | 0 | 0 | 0 |
| pelnomocnictwo | 0 | 60 | 0 | 0 |
| przelew | 0 | 0 | 60 | 0 |
| ∅ (nierozpoznany) | 0 | 0 | 0 | 1 |

## odwolanie

| Pole | TP | FP | FN | Precision | Recall | F1 (strict) | F1 (lenient) |
|---|---|---|---|---|---|---|---|
| `OdwolanieKIO.czynnosc_dzien` | 59 | 1 | 1 | 0.983 | 0.983 | **0.983** | 0.983 |
| `OdwolanieKIO.czynnosc_opis` | 58 | 2 | 2 | 0.967 | 0.967 | **0.967** | 0.967 |
| `OdwolanieKIO.czynnosc_powod_id` | 58 | 2 | 2 | 0.967 | 0.967 | **0.967** | 0.967 |
| `OdwolanieKIO.data` | 45 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `OdwolanieKIO.miejscowosc` | 45 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Odwolujacy[].krs` | 56 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Odwolujacy[].nazwa` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Odwolujacy[].nip` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Odwolujacy[].pelnomocnik.imie_nazwisko` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Odwolujacy[].pelnomocnik.mail` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Odwolujacy[].pelnomocnik.nazwa` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Odwolujacy[].przez-pelnomocnika` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Odwolujacy[].regon` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Zamawiajacy[].krs` | 58 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Zamawiajacy[].nazwa` | 63 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Zamawiajacy[].nip` | 63 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Zamawiajacy[].prowadzacy_postepowanie` | 6 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Zamawiajacy[].regon` | 63 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `ZamowieniePubliczne.numer_bzp` | 48 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `ZamowieniePubliczne.numer_postepowania` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `ZamowieniePubliczne.numer_ted` | 47 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `ZamowieniePubliczne.tytul` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |

## pelnomocnictwo

| Pole | TP | FP | FN | Precision | Recall | F1 (strict) | F1 (lenient) |
|---|---|---|---|---|---|---|---|
| `mocodawca[].data.imie_nazwisko` | 4 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `mocodawca[].data.krs` | 62 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `mocodawca[].data.nazwa` | 66 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `mocodawca[].data.nip` | 66 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `mocodawca[].data.typ` | 66 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `mocodawca[].podpisujacy[].imie_nazwisko` | 95 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `pelnomocnicy[].imie_nazwisko` | 98 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `pelnomocnicy[].pesel` | 1 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |

## przelew

| Pole | TP | FP | FN | Precision | Recall | F1 (strict) | F1 (lenient) |
|---|---|---|---|---|---|---|---|
| `przelew_bankowy.data_operacji` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.kwota` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.na_rachunek` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.numer_transakcji` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.tytul` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.z_rachunku` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
