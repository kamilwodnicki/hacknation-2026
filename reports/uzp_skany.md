# Ewaluacja: uzp_skany

Wygenerowano: 2026-11-21 21:38

Metryka: F1 na poziomie pól (wartości `null` nie są liczone; błędna wartość = FP + FN; listy dopasowywane po treści).

**F1 (UZP)** — zasada organizatora: pola typu „długi string” (nazwy firm, tytuły) zaliczane przy podobieństwie ≥ 80%, pozostałe muszą być identyczne. **F1 (dokładne)** — wszystkie pola identyczne.

Typ dokumentu do ekstrakcji: **z klasyfikatora** (pełny pipeline).

Tryb ekstrakcji: **rules**.

## Podsumowanie

| | TP | FP | FN | Precision | Recall | F1 (UZP) | F1 (dokładne) |
|---|---|---|---|---|---|---|---|
| **RAZEM** | 191 | 13 | 118 | 0.936 | 0.618 | **0.745** | 0.737 |
| odwolanie (10 dok.) | 113 | 6 | 64 | 0.950 | 0.638 | **0.764** | 0.757 |
| pelnomocnictwo (10 dok.) | 41 | 3 | 37 | 0.932 | 0.526 | **0.672** | 0.672 |
| przelew (10 dok.) | 37 | 4 | 17 | 0.902 | 0.685 | **0.779** | 0.758 |

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
| `OdwolanieKIO.czynnosc_dzien` | 0 | 0 | 10 | 0.000 | 0.000 | **0.000** | 0.000 |
| `OdwolanieKIO.czynnosc_opis` | 9 | 0 | 1 | 1.000 | 0.900 | **0.947** | 0.947 |
| `OdwolanieKIO.czynnosc_powod_id` | 9 | 0 | 1 | 1.000 | 0.900 | **0.947** | 0.947 |
| `OdwolanieKIO.data` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `OdwolanieKIO.miejscowosc` | 9 | 1 | 1 | 0.900 | 0.900 | **0.900** | 0.900 |
| `Odwolujacy[].krs` | 5 | 0 | 3 | 1.000 | 0.625 | **0.769** | 0.769 |
| `Odwolujacy[].nazwa` | 4 | 0 | 6 | 1.000 | 0.400 | **0.571** | 0.571 |
| `Odwolujacy[].nip` | 5 | 0 | 5 | 1.000 | 0.500 | **0.667** | 0.667 |
| `Odwolujacy[].pelnomocnik.imie_nazwisko` | 0 | 0 | 9 | 0.000 | 0.000 | **0.000** | 0.000 |
| `Odwolujacy[].pelnomocnik.mail` | 5 | 0 | 4 | 1.000 | 0.556 | **0.714** | 0.714 |
| `Odwolujacy[].pelnomocnik.nazwa` | 5 | 0 | 4 | 1.000 | 0.556 | **0.714** | 0.714 |
| `Odwolujacy[].przez-pelnomocnika` | 0 | 5 | 10 | 0.000 | 0.000 | **0.000** | 0.000 |
| `Odwolujacy[].regon` | 3 | 0 | 3 | 1.000 | 0.500 | **0.667** | 0.667 |
| `Zamawiajacy[].krs` | 0 | 0 | 0 | 0.000 | 0.000 | **0.000** | 0.000 |
| `Zamawiajacy[].nazwa` | 8 | 0 | 3 | 1.000 | 0.727 | **0.842** | 0.842 |
| `Zamawiajacy[].nip` | 6 | 0 | 2 | 1.000 | 0.750 | **0.857** | 0.857 |
| `Zamawiajacy[].prowadzacy_postepowanie` | 2 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `Zamawiajacy[].regon` | 3 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `ZamowieniePubliczne.numer_bzp` | 5 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `ZamowieniePubliczne.numer_postepowania` | 8 | 0 | 2 | 1.000 | 0.800 | **0.889** | 0.889 |
| `ZamowieniePubliczne.numer_ted` | 7 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `ZamowieniePubliczne.tytul` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 0.900 |

Przykładowe różnice dokładne (40 z 65):

- `0001` `OdwolanieKIO.czynnosc_dzien`: oczekiwano ["2026-09-06"], otrzymano [null]
- `0001` `Odwolujacy[].pelnomocnik.imie_nazwisko`: oczekiwano ["Aleksandra Rybak"], otrzymano [null]
- `0001` `Odwolujacy[].przez-pelnomocnika`: oczekiwano [1], otrzymano [0]
- `0002` `OdwolanieKIO.czynnosc_dzien`: oczekiwano ["2026-04-01"], otrzymano [null]
- `0002` `Odwolujacy[].krs`: oczekiwano ["9994354396"], otrzymano []
- `0002` `Odwolujacy[].nazwa`: oczekiwano ["Medicor Infrastruktura S.A."], otrzymano []
- `0002` `Odwolujacy[].nip`: oczekiwano ["9995090281"], otrzymano []
- `0002` `Odwolujacy[].pelnomocnik.imie_nazwisko`: oczekiwano ["Mateusz Wierzbicki"], otrzymano []
- `0002` `Odwolujacy[].pelnomocnik.mail`: oczekiwano ["m.wierzbicki@wierzbicki-kancelaria.example"], otrzymano []
- `0002` `Odwolujacy[].pelnomocnik.nazwa`: oczekiwano ["Kancelaria Adwokacka adw. Mateusz Wierzbicki"], otrzymano []
- `0002` `Odwolujacy[].przez-pelnomocnika`: oczekiwano [1], otrzymano []
- `0002` `Odwolujacy[].regon`: oczekiwano ["999368597"], otrzymano []
- `0002` `Zamawiajacy[].nazwa`: oczekiwano ["Powiatowy Zespół Szkół Technicznych w Wrzosowie"], otrzymano []
- `0003` `OdwolanieKIO.czynnosc_dzien`: oczekiwano ["2026-07-05"], otrzymano [null]
- `0003` `Odwolujacy[].pelnomocnik.imie_nazwisko`: oczekiwano ["Żaneta Olszewska"], otrzymano [null]
- `0003` `Odwolujacy[].przez-pelnomocnika`: oczekiwano [1], otrzymano [0]
- `0004` `OdwolanieKIO.czynnosc_dzien`: oczekiwano ["2026-02-04"], otrzymano [null]
- `0004` `Odwolujacy[].pelnomocnik.imie_nazwisko`: oczekiwano ["Krzysztof Jodłowski"], otrzymano [null]
- `0004` `Odwolujacy[].przez-pelnomocnika`: oczekiwano [1], otrzymano [0]
- `0005` `OdwolanieKIO.czynnosc_dzien`: oczekiwano ["2026-03-23"], otrzymano [null]
- `0005` `OdwolanieKIO.czynnosc_opis`: oczekiwano ["Opis przedmiotu zamówienia (OPZ)"], otrzymano [null]
- `0005` `OdwolanieKIO.czynnosc_powod_id`: oczekiwano [11], otrzymano [null]
- `0005` `Odwolujacy[].nazwa`: oczekiwano ["Medicor IT Solutions S.A."], otrzymano []
- `0005` `Odwolujacy[].nip`: oczekiwano ["9992326754"], otrzymano []
- `0005` `Odwolujacy[].pelnomocnik.imie_nazwisko`: oczekiwano ["Grzegorz Kaczmarek"], otrzymano []
- `0005` `Odwolujacy[].pelnomocnik.mail`: oczekiwano ["g.kaczmarek@kaczmarek-kancelaria.example"], otrzymano []
- `0005` `Odwolujacy[].pelnomocnik.nazwa`: oczekiwano ["Kancelaria Adwokacka adw. Grzegorz Kaczmarek"], otrzymano []
- `0005` `Odwolujacy[].przez-pelnomocnika`: oczekiwano [1], otrzymano []
- `0005` `Odwolujacy[].regon`: oczekiwano ["999749508"], otrzymano []
- `0005` `Zamawiajacy[].nazwa`: oczekiwano ["Regionalne Centrum Zdrowia Publicznego w Dębnicy Górnej"], otrzymano []
- `0005` `Zamawiajacy[].nip`: oczekiwano ["9996245053"], otrzymano []
- `0006` `OdwolanieKIO.czynnosc_dzien`: oczekiwano ["2026-05-11"], otrzymano [null]
- `0006` `Odwolujacy[].krs`: oczekiwano ["9997873010"], otrzymano []
- `0006` `Odwolujacy[].nazwa`: oczekiwano ["Nordenix Automatyka Sp. z o.o."], otrzymano []
- `0006` `Odwolujacy[].nip`: oczekiwano ["9991785572"], otrzymano []
- `0006` `Odwolujacy[].pelnomocnik.imie_nazwisko`: oczekiwano ["Sylwia Sikora"], otrzymano []
- `0006` `Odwolujacy[].pelnomocnik.mail`: oczekiwano ["s.sikora@olszewski-kancelaria.example"], otrzymano []
- `0006` `Odwolujacy[].pelnomocnik.nazwa`: oczekiwano ["Kancelaria Prawna Olszewski & Partnerzy sp. k."], otrzymano []
- `0006` `Odwolujacy[].przez-pelnomocnika`: oczekiwano [1], otrzymano []
- `0006` `Odwolujacy[].regon`: oczekiwano ["999885921"], otrzymano []

## pelnomocnictwo

| Pole | TP | FP | FN | Precision | Recall | F1 (UZP) | F1 (dokładne) |
|---|---|---|---|---|---|---|---|
| `mocodawca[].data.imie_nazwisko` | 0 | 0 | 1 | 0.000 | 0.000 | **0.000** | 0.000 |
| `mocodawca[].data.krs` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `mocodawca[].data.nazwa` | 9 | 2 | 1 | 0.818 | 0.900 | **0.857** | 0.857 |
| `mocodawca[].data.nip` | 11 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `mocodawca[].data.typ` | 10 | 1 | 1 | 0.909 | 0.909 | **0.909** | 0.909 |
| `mocodawca[].podpisujacy[].imie_nazwisko` | 0 | 0 | 14 | 0.000 | 0.000 | **0.000** | 0.000 |
| `pelnomocnicy[].imie_nazwisko` | 1 | 0 | 16 | 1.000 | 0.059 | **0.111** | 0.111 |
| `pelnomocnicy[].pesel` | 0 | 0 | 4 | 0.000 | 0.000 | **0.000** | 0.000 |

Przykładowe różnice dokładne (26 z 26):

- `0001` `mocodawca[].podpisujacy[].imie_nazwisko`: oczekiwano ["Szymon Brzozowski"], otrzymano []
- `0001` `pelnomocnicy[].imie_nazwisko`: oczekiwano ["Aleksandra Rybak", "Halina Jodłowska", "Wojciech Kaczmarek"], otrzymano []
- `0002` `mocodawca[].podpisujacy[].imie_nazwisko`: oczekiwano ["Grzegorz Jaworski"], otrzymano []
- `0003` `mocodawca[].podpisujacy[].imie_nazwisko`: oczekiwano ["Szymon Jabłoń"], otrzymano []
- `0003` `pelnomocnicy[].imie_nazwisko`: oczekiwano ["Żaneta Olszewska"], otrzymano []
- `0004` `mocodawca[].data.nazwa`: oczekiwano ["Arkomed Serwis spółka akcyjna"], otrzymano ["Arkomed Serwis S.A."]
- `0004` `mocodawca[].podpisujacy[].imie_nazwisko`: oczekiwano ["Halina Baran", "Dorota Topolska"], otrzymano []
- `0004` `pelnomocnicy[].imie_nazwisko`: oczekiwano ["Krzysztof Jodłowski"], otrzymano []
- `0004` `pelnomocnicy[].pesel`: oczekiwano ["69102340858"], otrzymano []
- `0005` `mocodawca[].podpisujacy[].imie_nazwisko`: oczekiwano ["Zbigniew Cieślak"], otrzymano []
- `0005` `pelnomocnicy[].imie_nazwisko`: oczekiwano ["Grzegorz Kaczmarek", "Katarzyna Sikora", "Karolina Baran"], otrzymano []
- `0006` `mocodawca[].podpisujacy[].imie_nazwisko`: oczekiwano ["Monika Kaczmarek", "Dorota Szulc"], otrzymano []
- `0006` `pelnomocnicy[].imie_nazwisko`: oczekiwano ["Sylwia Sikora", "Karolina Kaczmarek"], otrzymano []
- `0007` `mocodawca[].podpisujacy[].imie_nazwisko`: oczekiwano ["Dorota Grabowska", "Łukasz Sosnowski"], otrzymano []
- `0007` `pelnomocnicy[].imie_nazwisko`: oczekiwano ["Dorota Kubiak"], otrzymano []
- `0007` `pelnomocnicy[].pesel`: oczekiwano ["90082629103"], otrzymano []
- `0008` `mocodawca[].podpisujacy[].imie_nazwisko`: oczekiwano ["Szymon Zawadzki"], otrzymano []
- `0008` `pelnomocnicy[].imie_nazwisko`: oczekiwano ["Rafał Malinowski"], otrzymano []
- `0009` `mocodawca[].podpisujacy[].imie_nazwisko`: oczekiwano ["Żaneta Rybak", "Jakub Zawadzki"], otrzymano []
- `0009` `pelnomocnicy[].imie_nazwisko`: oczekiwano ["Anna Topolska", "Piotr Wróbel"], otrzymano []
- `0009` `pelnomocnicy[].pesel`: oczekiwano ["68091502944", "82070226436"], otrzymano []
- `0010` `mocodawca[].data.imie_nazwisko`: oczekiwano ["Paweł Brzozowski"], otrzymano [null]
- `0010` `mocodawca[].data.nazwa`: oczekiwano [null], otrzymano ["Paweł Brzozowski Asterion Usługi Techniczne"]
- `0010` `mocodawca[].data.typ`: oczekiwano ["osoba_fizyczna"], otrzymano ["osoba_prawna"]
- `0010` `mocodawca[].podpisujacy[].imie_nazwisko`: oczekiwano ["Paweł Brzozowski"], otrzymano []
- `0010` `pelnomocnicy[].imie_nazwisko`: oczekiwano ["Andrzej Wróbel", "Monika Zawadzka"], otrzymano []

## przelew

| Pole | TP | FP | FN | Precision | Recall | F1 (UZP) | F1 (dokładne) |
|---|---|---|---|---|---|---|---|
| `przelew_bankowy.data_operacji` | 3 | 0 | 7 | 1.000 | 0.300 | **0.462** | 0.462 |
| `przelew_bankowy.kwota` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.na_rachunek` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.numer_transakcji` | 1 | 0 | 3 | 1.000 | 0.250 | **0.400** | 0.400 |
| `przelew_bankowy.tytul` | 3 | 4 | 7 | 0.429 | 0.300 | **0.353** | 0.235 |
| `przelew_bankowy.z_rachunku` | 10 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |

Przykładowe różnice dokładne (18 z 18):

- `0001` `przelew_bankowy.numer_transakcji`: oczekiwano ["CEN9057564440515"], otrzymano [null]
- `0002` `przelew_bankowy.data_operacji`: oczekiwano ["2026-04-09"], otrzymano [null]
- `0002` `przelew_bankowy.tytul`: oczekiwano ["opłata skarbowa od pełnomocnictwa dla adw. Mateusz Wierzbicki w postępowaniu przed KIO w przetargu ZG.261.8.2026"], otrzymano ["opłata skarbowa od pełnomocnictwa dla adw. Mateusz Wierzbicki w postępowaniu przed KIO w przetargu ZG.261.8.2026 Dokument jest wydrukiem komputerowym i nie wymaga dodatkowych podpisów oraz stempla"]
- `0003` `przelew_bankowy.data_operacji`: oczekiwano ["2026-07-15"], otrzymano [null]
- `0003` `przelew_bankowy.tytul`: oczekiwano ["WPIS OD ODW., ZAM: KOMENDA WOJEWÓDZKA PAŃSTWOWEJ STRAŻY POŻARNEJ W JA, PN/58/2026/DOS"], otrzymano ["WPIS OD ODW., ZAM: KOMENDA WOJEWÓDZKA PAÑSTWOWEJ STRAŻY POŻARNEJ W JA, PN/58/2026/DOS"]
- `0004` `przelew_bankowy.tytul`: oczekiwano ["OPŁATA SKARBOWA OD PEŁNOMOCNICTWA DLA RADCA PRAWNY KRZYSZTOF JODŁOWSKI W POSTĘPOWANIU PRZED KIO W PRZETARGU DZP.260.69.2026"], otrzymano ["Rachunek odbiorcy: 90103015082458665313544731 Nazwa odbiorcy: URZAD MIASTA WRZOSOWO Tytut: OPLATA SKARBOWA OD PELNOMOCNICTWA DLA"]
- `0005` `przelew_bankowy.data_operacji`: oczekiwano ["2026-03-26"], otrzymano [null]
- `0005` `przelew_bankowy.numer_transakcji`: oczekiwano ["305494"], otrzymano [null]
- `0005` `przelew_bankowy.tytul`: oczekiwano ["Wpis od odwołania, ZP/12/2026, REGIONALNE CENTRUM ZDROWIA PUBLICZNEGO W DĘBNICY GÓRNEJ"], otrzymano [null]
- `0006` `przelew_bankowy.data_operacji`: oczekiwano ["2026-05-20"], otrzymano [null]
- `0007` `przelew_bankowy.data_operacji`: oczekiwano ["2026-03-17"], otrzymano [null]
- `0007` `przelew_bankowy.tytul`: oczekiwano ["Wpis od odwołania, ZP.271.59.2026, MUZEUM REGIONALNE W OLSZANOWIE"], otrzymano ["Wpis od odwolania, ZP.271.59.2026, MUZEUM REGIONALNE W OLSZANOWIE Dokument jest wydrukiem komputerowym i nie wymaga dodatkowych podpisów oraz stempla bankowego."]
- `0008` `przelew_bankowy.data_operacji`: oczekiwano ["2026-04-20"], otrzymano [null]
- `0008` `przelew_bankowy.tytul`: oczekiwano ["opłata skarbowa od pełnomocnictwa dla adw. Rafał Malinowski w postępowaniu przed KIO w przetargu ZP/134/2026"], otrzymano [null]
- `0009` `przelew_bankowy.tytul`: oczekiwano ["WPIS OD ODWOŁANIA, DA.ZP.242.13.2026, MIEJSKI OŚRODEK SPORTU I REKREACJI W OLSZANOWIE"], otrzymano ["Rachunek odbiorcy: 60101010100081362231000000 Nazwa odbiorcy: URZAD ZAMÓWIEN PUBLICZNYCH Tytul: WPIS OD ODWOLANIA, DA.ZP:242.13.2026,MIEJSKI"]
- `0010` `przelew_bankowy.data_operacji`: oczekiwano ["2026-03-29"], otrzymano [null]
- `0010` `przelew_bankowy.numer_transakcji`: oczekiwano ["801140"], otrzymano [null]
- `0010` `przelew_bankowy.tytul`: oczekiwano ["opłata skarbowa od pełnomocnictwa dla radca prawny Andrzej Wróbel i adwokat Monika Zawadzka w postępowaniu przed KIO w przetargu ZP/107/2026"], otrzymano [null]
