# Ewaluacja: uzp_skany

Wygenerowano: 2026-11-21 20:46

Metryka: F1 na poziomie pól (wartości `null` nie są liczone; błędna wartość = FP + FN; listy dopasowywane po treści).

**F1 (UZP)** — zasada organizatora: pola typu „długi string” (nazwy firm, tytuły) zaliczane przy podobieństwie ≥ 80%, pozostałe muszą być identyczne. **F1 (dokładne)** — wszystkie pola identyczne.

Typ dokumentu do ekstrakcji: **z klasyfikatora** (pełny pipeline).

Tryb ekstrakcji: **hybrid** — do modelu wysłano 30 dok. (z pamięci podręcznej: 10), pominięto 0 (reguły kompletne), błędy LLM: 0; nowe tokeny: wejście 33885, wyjście 4036.

## Podsumowanie

| | TP | FP | FN | Precision | Recall | F1 (UZP) | F1 (dokładne) |
|---|---|---|---|---|---|---|---|
| **RAZEM** | 299 | 9 | 10 | 0.971 | 0.968 | **0.969** | 0.947 |
| odwolanie (10 dok.) | 170 | 6 | 7 | 0.966 | 0.960 | **0.963** | 0.958 |
| pelnomocnictwo (10 dok.) | 75 | 3 | 3 | 0.962 | 0.962 | **0.962** | 0.962 |
| przelew (10 dok.) | 54 | 0 | 0 | 1.000 | 1.000 | **1.000** | 0.889 |

## Klasyfikacja

Trafność: **1.000** (30/30)

| oczekiwany \ przewidziany | odwolanie | pelnomocnictwo | przelew |
|---|---|---|---|
| odwolanie | 10 | 0 | 0 |
| pelnomocnictwo | 0 | 10 | 0 |
| przelew | 0 | 0 | 10 |

## odwolanie

| Pole | TP | FP | FN | Precision | Recall | F1 (UZP) | F1 (dokładne) |
|---|---|---|---|---|---|---|---|
| `OdwolanieKIO.czynnosc_dzien` | 9 | 1 | 1 | 0.900 | 0.900 | **0.900** | 0.900 |
| `OdwolanieKIO.czynnosc_opis` | 9 | 1 | 1 | 0.900 | 0.900 | **0.900** | 0.900 |
| `OdwolanieKIO.czynnosc_powod_id` | 9 | 1 | 1 | 0.900 | 0.900 | **0.900** | 0.900 |
| `OdwolanieKIO.data` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `OdwolanieKIO.miejscowosc` | 9 | 1 | 1 | 0.900 | 0.900 | **0.900** | 0.900 |
| `Odwolujacy[].krs` | 8 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Odwolujacy[].nazwa` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Odwolujacy[].nip` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Odwolujacy[].pelnomocnik.imie_nazwisko` | 9 | 1 | 0 | 0.900 | 1.000 | **0.947** | 0.947 |
| `Odwolujacy[].pelnomocnik.mail` | 9 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Odwolujacy[].pelnomocnik.nazwa` | 9 | 0 | 0 | 1.000 | 1.000 | **1.000** | 0.889 |
| `Odwolujacy[].przez-pelnomocnika` | 9 | 1 | 1 | 0.900 | 0.900 | **0.900** | 0.900 |
| `Odwolujacy[].regon` | 6 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Zamawiajacy[].krs` | 0 | 0 | 0 | 0.000 | 0.000 | **0.000** | 0.000 |
| `Zamawiajacy[].nazwa` | 11 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Zamawiajacy[].nip` | 8 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Zamawiajacy[].prowadzacy_postepowanie` | 2 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Zamawiajacy[].regon` | 3 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `ZamowieniePubliczne.numer_bzp` | 4 | 0 | 1 | 1.000 | 0.800 | **0.889** | 0.889 |
| `ZamowieniePubliczne.numer_postepowania` | 9 | 0 | 1 | 1.000 | 0.900 | **0.947** | 0.947 |
| `ZamowieniePubliczne.numer_ted` | 7 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `ZamowieniePubliczne.tytul` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |

Przykładowe różnice dokładne (9 z 9):

- `0005` `OdwolanieKIO.czynnosc_dzien`: oczekiwano ["2026-03-23"], otrzymano ["2026-02-19"]
- `0005` `OdwolanieKIO.czynnosc_opis`: oczekiwano ["Opis przedmiotu zamówienia (OPZ)"], otrzymano ["Publikacja specyfikacji warunków zamówienia (SWZ)"]
- `0005` `OdwolanieKIO.czynnosc_powod_id`: oczekiwano [11], otrzymano [4]
- `0005` `ZamowieniePubliczne.numer_bzp`: oczekiwano ["2026/BZP00879135/03"], otrzymano [null]
- `0005` `ZamowieniePubliczne.numer_postepowania`: oczekiwano ["ZP/12/2026"], otrzymano [null]
- `0009` `OdwolanieKIO.miejscowosc`: oczekiwano ["Łódź"], otrzymano ["Lódź"]
- `0009` `Odwolujacy[].pelnomocnik.imie_nazwisko`: oczekiwano [null], otrzymano ["Żaneta Rybak"]
- `0009` `Odwolujacy[].przez-pelnomocnika`: oczekiwano [0], otrzymano [1]
- `0010` `Odwolujacy[].pelnomocnik.nazwa`: oczekiwano ["Kancelaria Radcy Prawnego Andrzej Wróbel"], otrzymano ["BBD Kancelaria Radcy Prawnego Andrzej Wróbel"]

## pelnomocnictwo

| Pole | TP | FP | FN | Precision | Recall | F1 (UZP) | F1 (dokładne) |
|---|---|---|---|---|---|---|---|
| `mocodawca[].data.imie_nazwisko` | 0 | 0 | 1 | 0.000 | 0.000 | **0.000** | 0.000 |
| `mocodawca[].data.krs` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `mocodawca[].data.nazwa` | 9 | 2 | 1 | 0.818 | 0.900 | **0.857** | 0.857 |
| `mocodawca[].data.nip` | 11 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `mocodawca[].data.typ` | 10 | 1 | 1 | 0.909 | 0.909 | **0.909** | 0.909 |
| `mocodawca[].podpisujacy[].imie_nazwisko` | 14 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `pelnomocnicy[].imie_nazwisko` | 17 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `pelnomocnicy[].pesel` | 4 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |

Przykładowe różnice dokładne (4 z 4):

- `0004` `mocodawca[].data.nazwa`: oczekiwano ["Arkomed Serwis spółka akcyjna"], otrzymano ["Arkomed Serwis S.A."]
- `0010` `mocodawca[].data.imie_nazwisko`: oczekiwano ["Paweł Brzozowski"], otrzymano [null]
- `0010` `mocodawca[].data.nazwa`: oczekiwano [null], otrzymano ["Brzozowski Asterion Usługi Techniczne"]
- `0010` `mocodawca[].data.typ`: oczekiwano ["osoba_fizyczna"], otrzymano ["osoba_prawna"]

## przelew

| Pole | TP | FP | FN | Precision | Recall | F1 (UZP) | F1 (dokładne) |
|---|---|---|---|---|---|---|---|
| `przelew_bankowy.data_operacji` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.kwota` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.na_rachunek` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.numer_transakcji` | 4 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.tytul` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 0.400 |
| `przelew_bankowy.z_rachunku` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |

Przykładowe różnice dokładne (6 z 6):

- `0001` `przelew_bankowy.tytul`: oczekiwano ["wpis od odwołania - postępowanie nr DA.ZP.242.50.2026 CEN9057564440515"], otrzymano ["wpis od odwolania - postępowanie nr DA.ZP.242.50.2026 CEN9057564440515"]
- `0004` `przelew_bankowy.tytul`: oczekiwano ["OPŁATA SKARBOWA OD PEŁNOMOCNICTWA DLA RADCA PRAWNY KRZYSZTOF JODŁOWSKI W POSTĘPOWANIU PRZED KIO W PRZETARGU DZP.260.69.2026"], otrzymano ["OPLATA SKARBOWA OD PELNOMOCNICTWA DLA RADCA PRAWNY KRZYSZTOF JODŁOWSKI W POSTEPOWANIU PRZED KIO W PRZETARGU DZP.260.69.2026"]
- `0005` `przelew_bankowy.tytul`: oczekiwano ["Wpis od odwołania, ZP/12/2026, REGIONALNE CENTRUM ZDROWIA PUBLICZNEGO W DĘBNICY GÓRNEJ"], otrzymano ["Wpis od odwolania, ZP/12/2026, REGIONALNE CENTRUM ZDROWIA PUBLICZNEGO W DEBNICY GÓRNEJ"]
- `0007` `przelew_bankowy.tytul`: oczekiwano ["Wpis od odwołania, ZP.271.59.2026, MUZEUM REGIONALNE W OLSZANOWIE"], otrzymano ["Wpis od odwolania, ZP.271.59.2026, MUZEUM REGIONALNE W OLSZANOWIE"]
- `0008` `przelew_bankowy.tytul`: oczekiwano ["opłata skarbowa od pełnomocnictwa dla adw. Rafał Malinowski w postępowaniu przed KIO w przetargu ZP/134/2026"], otrzymano ["opłata skarbowa od pełnomocnictwa dla adw Rafał Maknowski w postępowaniu przed KIO w przetargu ZP/134/2026"]
- `0009` `przelew_bankowy.tytul`: oczekiwano ["WPIS OD ODWOŁANIA, DA.ZP.242.13.2026, MIEJSKI OŚRODEK SPORTU I REKREACJI W OLSZANOWIE"], otrzymano ["WPIS OD ODWOLANIA, DA.ZP:242.13.2026, MIEJSKI OŚRODEK SPORTU I REKREACJI W OLSZANOWIE"]
