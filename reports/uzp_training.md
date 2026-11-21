# Ewaluacja: uzp_training

Wygenerowano: 2026-11-21 22:38

Metryka: F1 na poziomie pól (wartości `null` nie są liczone; błędna wartość = FP + FN; listy dopasowywane po treści).

**F1 (UZP)** — zasada organizatora: pola typu „długi string” (nazwy firm, tytuły) zaliczane przy podobieństwie ≥ 80%, pozostałe muszą być identyczne. **F1 (dokładne)** — wszystkie pola identyczne.

Typ dokumentu do ekstrakcji: **z klasyfikatora** (pełny pipeline).

Tryb ekstrakcji: **rules**.

## Podsumowanie

| | TP | FP | FN | Precision | Recall | F1 (UZP) | F1 (dokładne) |
|---|---|---|---|---|---|---|---|
| **RAZEM** | 2031 | 1 | 1 | 1.000 | 1.000 | **1.000** | 0.952 |
| odwolanie (60 dok.) | 1213 | 1 | 1 | 0.999 | 0.999 | **0.999** | 0.999 |
| pelnomocnictwo (60 dok.) | 458 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| przelew (60 dok.) | 360 | 0 | 0 | 1.000 | 1.000 | **1.000** | 0.733 |

## Klasyfikacja

Trafność: **1.000** (198/198)

| oczekiwany \ przewidziany | odwolanie | pelnomocnictwo | przelew | ∅ (nierozpoznany) |
|---|---|---|---|---|
| odwolanie | 61 | 0 | 0 | 0 |
| pelnomocnictwo | 0 | 60 | 0 | 0 |
| przelew | 0 | 0 | 60 | 0 |
| ∅ (nierozpoznany) | 0 | 0 | 0 | 17 |

## odwolanie

| Pole | TP | FP | FN | Precision | Recall | F1 (UZP) | F1 (dokładne) |
|---|---|---|---|---|---|---|---|
| `OdwolanieKIO.czynnosc_dzien` | 59 | 1 | 1 | 0.983 | 0.983 | **0.983** | 0.983 |
| `OdwolanieKIO.czynnosc_opis` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `OdwolanieKIO.czynnosc_powod_id` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
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

Przykładowe różnice dokładne (1 z 1):

- `przyklad_40` `OdwolanieKIO.czynnosc_dzien`: oczekiwano ["2026-10-09"], otrzymano ["2026-09-18"]

## pelnomocnictwo

| Pole | TP | FP | FN | Precision | Recall | F1 (UZP) | F1 (dokładne) |
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

| Pole | TP | FP | FN | Precision | Recall | F1 (UZP) | F1 (dokładne) |
|---|---|---|---|---|---|---|---|
| `przelew_bankowy.data_operacji` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.kwota` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.na_rachunek` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 0.200 |
| `przelew_bankowy.numer_transakcji` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.tytul` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
| `przelew_bankowy.z_rachunku` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 0.200 |

Przykładowe różnice dokładne (20 z 96):

- `przyklad_01` `przelew_bankowy.na_rachunek`: oczekiwano ["68438223049992295262834736"], otrzymano ["PL68438223049992295262834736"]
- `przyklad_01` `przelew_bankowy.z_rachunku`: oczekiwano ["05470680287581539721455024"], otrzymano ["PL05470680287581539721455024"]
- `przyklad_03` `przelew_bankowy.na_rachunek`: oczekiwano ["09460896147587484470692985"], otrzymano ["PL09460896147587484470692985"]
- `przyklad_03` `przelew_bankowy.z_rachunku`: oczekiwano ["39203888965989833490230983"], otrzymano ["PL39203888965989833490230983"]
- `przyklad_04` `przelew_bankowy.na_rachunek`: oczekiwano ["91363778606394934264547691"], otrzymano ["PL91363778606394934264547691"]
- `przyklad_04` `przelew_bankowy.z_rachunku`: oczekiwano ["43046337661291756811869204"], otrzymano ["PL43046337661291756811869204"]
- `przyklad_05` `przelew_bankowy.na_rachunek`: oczekiwano ["10386393618709740848534519"], otrzymano ["PL10386393618709740848534519"]
- `przyklad_05` `przelew_bankowy.z_rachunku`: oczekiwano ["66211180801009882857081733"], otrzymano ["PL66211180801009882857081733"]
- `przyklad_06` `przelew_bankowy.na_rachunek`: oczekiwano ["47138858777839172875872799"], otrzymano ["PL47138858777839172875872799"]
- `przyklad_06` `przelew_bankowy.z_rachunku`: oczekiwano ["83857487285854133752374620"], otrzymano ["PL83857487285854133752374620"]
- `przyklad_07` `przelew_bankowy.na_rachunek`: oczekiwano ["95504884425794546508647369"], otrzymano ["PL95504884425794546508647369"]
- `przyklad_07` `przelew_bankowy.z_rachunku`: oczekiwano ["64621719650035158366008774"], otrzymano ["PL64621719650035158366008774"]
- `przyklad_08` `przelew_bankowy.na_rachunek`: oczekiwano ["41351879105578128609561192"], otrzymano ["PL41351879105578128609561192"]
- `przyklad_08` `przelew_bankowy.z_rachunku`: oczekiwano ["57936403120146943695277279"], otrzymano ["PL57936403120146943695277279"]
- `przyklad_10` `przelew_bankowy.na_rachunek`: oczekiwano ["64610803725981455663135560"], otrzymano ["PL64610803725981455663135560"]
- `przyklad_10` `przelew_bankowy.z_rachunku`: oczekiwano ["21822962409050354037148193"], otrzymano ["PL21822962409050354037148193"]
- `przyklad_11` `przelew_bankowy.na_rachunek`: oczekiwano ["04669325299404954519396033"], otrzymano ["PL04669325299404954519396033"]
- `przyklad_11` `przelew_bankowy.z_rachunku`: oczekiwano ["55773565366491997400614103"], otrzymano ["PL55773565366491997400614103"]
- `przyklad_13` `przelew_bankowy.na_rachunek`: oczekiwano ["47326231412257943251088415"], otrzymano ["PL47326231412257943251088415"]
- `przyklad_13` `przelew_bankowy.z_rachunku`: oczekiwano ["34484587158449675491600836"], otrzymano ["PL34484587158449675491600836"]
