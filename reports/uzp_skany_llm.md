# Ewaluacja: uzp_skany

Wygenerowano: 2026-11-21 22:36

Metryka: F1 na poziomie pól (wartości `null` nie są liczone; błędna wartość = FP + FN; listy dopasowywane po treści).

**F1 (UZP)** — zasada organizatora: pola typu „długi string” (nazwy firm, tytuły) zaliczane przy podobieństwie ≥ 80%, pozostałe muszą być identyczne. **F1 (dokładne)** — wszystkie pola identyczne.

Typ dokumentu do ekstrakcji: **z klasyfikatora** (pełny pipeline).

Tryb ekstrakcji: **llm** — do modelu wysłano 30 dok. (z pamięci podręcznej: 0), pominięto 0 (reguły kompletne), błędy LLM: 0; nowe tokeny: wejście 78553, wyjście 8896.

## Podsumowanie

| | TP | FP | FN | Precision | Recall | F1 (UZP) | F1 (dokładne) |
|---|---|---|---|---|---|---|---|
| **RAZEM** | 273 | 4 | 36 | 0.986 | 0.883 | **0.932** | 0.911 |
| odwolanie (10 dok.) | 151 | 2 | 26 | 0.987 | 0.853 | **0.915** | 0.909 |
| pelnomocnictwo (10 dok.) | 68 | 2 | 10 | 0.971 | 0.872 | **0.919** | 0.919 |
| przelew (10 dok.) | 54 | 0 | 0 | 1.000 | 1.000 | **1.000** | 0.907 |

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
| `OdwolanieKIO.czynnosc_dzien` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `OdwolanieKIO.czynnosc_opis` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `OdwolanieKIO.czynnosc_powod_id` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `OdwolanieKIO.data` | 0 | 0 | 10 | 0.000 | 0.000 | **0.000** | 0.000 |
| `OdwolanieKIO.miejscowosc` | 0 | 0 | 10 | 0.000 | 0.000 | **0.000** | 0.000 |
| `Odwolujacy[].krs` | 8 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Odwolujacy[].nazwa` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Odwolujacy[].nip` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Odwolujacy[].pelnomocnik.imie_nazwisko` | 9 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Odwolujacy[].pelnomocnik.mail` | 9 | 1 | 0 | 0.900 | 1.000 | **0.947** | 0.947 |
| `Odwolujacy[].pelnomocnik.nazwa` | 9 | 0 | 0 | 1.000 | 1.000 | **1.000** | 0.889 |
| `Odwolujacy[].przez-pelnomocnika` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Odwolujacy[].regon` | 6 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Zamawiajacy[].krs` | 0 | 0 | 0 | 0.000 | 0.000 | **0.000** | 0.000 |
| `Zamawiajacy[].nazwa` | 11 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Zamawiajacy[].nip` | 8 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Zamawiajacy[].prowadzacy_postepowanie` | 0 | 0 | 2 | 0.000 | 0.000 | **0.000** | 0.000 |
| `Zamawiajacy[].regon` | 3 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `ZamowieniePubliczne.numer_bzp` | 4 | 1 | 1 | 0.800 | 0.800 | **0.800** | 0.800 |
| `ZamowieniePubliczne.numer_postepowania` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `ZamowieniePubliczne.numer_ted` | 4 | 0 | 3 | 1.000 | 0.571 | **0.727** | 0.727 |
| `ZamowieniePubliczne.tytul` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |

Przykładowe różnice dokładne (27 z 27):

- `0001` `OdwolanieKIO.data`: oczekiwano ["2026-09-11"], otrzymano [null]
- `0001` `OdwolanieKIO.miejscowosc`: oczekiwano ["Poznań"], otrzymano [null]
- `0002` `OdwolanieKIO.data`: oczekiwano ["2026-04-10"], otrzymano [null]
- `0002` `OdwolanieKIO.miejscowosc`: oczekiwano ["Białystok"], otrzymano [null]
- `0003` `OdwolanieKIO.data`: oczekiwano ["2026-07-15"], otrzymano [null]
- `0003` `OdwolanieKIO.miejscowosc`: oczekiwano ["Gdańsk"], otrzymano [null]
- `0004` `OdwolanieKIO.data`: oczekiwano ["2026-02-13"], otrzymano [null]
- `0004` `OdwolanieKIO.miejscowosc`: oczekiwano ["Wrocław"], otrzymano [null]
- `0004` `Zamawiajacy[].prowadzacy_postepowanie`: oczekiwano [1, 0], otrzymano [null, null]
- `0005` `OdwolanieKIO.data`: oczekiwano ["2026-03-27"], otrzymano [null]
- `0005` `OdwolanieKIO.miejscowosc`: oczekiwano ["Wrocław"], otrzymano [null]
- `0005` `ZamowieniePubliczne.numer_ted`: oczekiwano ["429185-2026"], otrzymano [null]
- `0006` `OdwolanieKIO.data`: oczekiwano ["2026-05-21"], otrzymano [null]
- `0006` `OdwolanieKIO.miejscowosc`: oczekiwano ["Bydgoszcz"], otrzymano [null]
- `0007` `OdwolanieKIO.data`: oczekiwano ["2026-03-19"], otrzymano [null]
- `0007` `OdwolanieKIO.miejscowosc`: oczekiwano ["Gdynia"], otrzymano [null]
- `0007` `ZamowieniePubliczne.numer_ted`: oczekiwano ["706707-2026"], otrzymano [null]
- `0008` `OdwolanieKIO.data`: oczekiwano ["2026-04-20"], otrzymano [null]
- `0008` `OdwolanieKIO.miejscowosc`: oczekiwano ["Warszawa"], otrzymano [null]
- `0008` `ZamowieniePubliczne.numer_bzp`: oczekiwano ["2026/BZP00239965/01"], otrzymano ["2026/BZP00239965"]
- `0008` `ZamowieniePubliczne.numer_ted`: oczekiwano ["142793-2026"], otrzymano [null]
- `0009` `OdwolanieKIO.data`: oczekiwano ["2026-06-05"], otrzymano [null]
- `0009` `OdwolanieKIO.miejscowosc`: oczekiwano ["Łódź"], otrzymano [null]
- `0009` `Odwolujacy[].pelnomocnik.mail`: oczekiwano [null], otrzymano ["biuro@asterion.example"]
- `0010` `OdwolanieKIO.data`: oczekiwano ["2026-03-31"], otrzymano [null]
- `0010` `OdwolanieKIO.miejscowosc`: oczekiwano ["Toruń"], otrzymano [null]
- `0010` `Odwolujacy[].pelnomocnik.nazwa`: oczekiwano ["Kancelaria Radcy Prawnego Andrzej Wróbel"], otrzymano ["BRI P Kancelaria Radcy Prawnego Andrzej Wróbel"]

## pelnomocnictwo

| Pole | TP | FP | FN | Precision | Recall | F1 (UZP) | F1 (dokładne) |
|---|---|---|---|---|---|---|---|
| `mocodawca[].data.imie_nazwisko` | 1 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `mocodawca[].data.krs` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `mocodawca[].data.nazwa` | 9 | 2 | 1 | 0.818 | 0.900 | **0.857** | 0.857 |
| `mocodawca[].data.nip` | 11 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `mocodawca[].data.typ` | 2 | 0 | 9 | 1.000 | 0.182 | **0.308** | 0.308 |
| `mocodawca[].podpisujacy[].imie_nazwisko` | 14 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `pelnomocnicy[].imie_nazwisko` | 17 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `pelnomocnicy[].pesel` | 4 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |

Przykładowe różnice dokładne (11 z 11):

- `0001` `mocodawca[].data.typ`: oczekiwano ["osoba_prawna"], otrzymano [null]
- `0002` `mocodawca[].data.typ`: oczekiwano ["osoba_prawna"], otrzymano [null]
- `0003` `mocodawca[].data.typ`: oczekiwano ["osoba_prawna"], otrzymano [null]
- `0004` `mocodawca[].data.nazwa`: oczekiwano ["Arkomed Serwis spółka akcyjna"], otrzymano ["Arkomed Serwis spółkaakcyjna"]
- `0004` `mocodawca[].data.typ`: oczekiwano ["osoba_prawna"], otrzymano [null]
- `0005` `mocodawca[].data.typ`: oczekiwano ["osoba_prawna"], otrzymano [null]
- `0006` `mocodawca[].data.typ`: oczekiwano ["osoba_prawna"], otrzymano [null]
- `0008` `mocodawca[].data.typ`: oczekiwano ["osoba_prawna"], otrzymano [null]
- `0009` `mocodawca[].data.typ`: oczekiwano ["osoba_prawna"], otrzymano [null]
- `0010` `mocodawca[].data.nazwa`: oczekiwano [null], otrzymano ["Paweł Brzozowski Asterion Usługi Techniczne"]
- `0010` `mocodawca[].data.typ`: oczekiwano ["osoba_fizyczna"], otrzymano [null]

## przelew

| Pole | TP | FP | FN | Precision | Recall | F1 (UZP) | F1 (dokładne) |
|---|---|---|---|---|---|---|---|
| `przelew_bankowy.data_operacji` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.kwota` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.na_rachunek` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.numer_transakcji` | 4 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.tytul` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 0.500 |
| `przelew_bankowy.z_rachunku` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |

Przykładowe różnice dokładne (5 z 5):

- `0004` `przelew_bankowy.tytul`: oczekiwano ["OPŁATA SKARBOWA OD PEŁNOMOCNICTWA DLA RADCA PRAWNY KRZYSZTOF JODŁOWSKI W POSTĘPOWANIU PRZED KIO W PRZETARGU DZP.260.69.2026"], otrzymano ["OPLATA SKARBOWA OD PELNOMOCNICTWA DLA RADCA PRAWNY KRZYSZTOF JODLOWSKI W POSTEPOWANIU PRZED KIO W PRZETARGU DZP.260.69.2026"]
- `0005` `przelew_bankowy.tytul`: oczekiwano ["Wpis od odwołania, ZP/12/2026, REGIONALNE CENTRUM ZDROWIA PUBLICZNEGO W DĘBNICY GÓRNEJ"], otrzymano ["Wpis od odwołania, ZP/12/2026, REGIONALNE CENTRUM ZDROWIA PUBLICZNEGO W DEBNICY GÓRNEJ"]
- `0007` `przelew_bankowy.tytul`: oczekiwano ["Wpis od odwołania, ZP.271.59.2026, MUZEUM REGIONALNE W OLSZANOWIE"], otrzymano ["Wpis od odwolania, ZP.271.59.2026, MUZEUM REGIONALNE W OLSZANOWIE"]
- `0008` `przelew_bankowy.tytul`: oczekiwano ["opłata skarbowa od pełnomocnictwa dla adw. Rafał Malinowski w postępowaniu przed KIO w przetargu ZP/134/2026"], otrzymano ["opłata skarbowa od pełnomocnictwa dla adw Rafał Maknowski w postępowaniu przed KIO w przetargu ZP/134/2026"]
- `0009` `przelew_bankowy.tytul`: oczekiwano ["WPIS OD ODWOŁANIA, DA.ZP.242.13.2026, MIEJSKI OŚRODEK SPORTU I REKREACJI W OLSZANOWIE"], otrzymano ["WPIS OD ODWOLANIA, DA.ZP:242.13.2026,MIEJSKI OŚRODEK SPORTU I REKREACJI W OLSZANOWIE"]
