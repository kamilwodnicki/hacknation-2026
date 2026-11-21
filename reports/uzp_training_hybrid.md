# Ewaluacja: uzp_training

Wygenerowano: 2026-11-21 20:45

Metryka: F1 na poziomie pól (wartości `null` nie są liczone; błędna wartość = FP + FN; listy dopasowywane po treści).

**F1 (UZP)** — zasada organizatora: pola typu „długi string” (nazwy firm, tytuły) zaliczane przy podobieństwie ≥ 80%, pozostałe muszą być identyczne. **F1 (dokładne)** — wszystkie pola identyczne.

Typ dokumentu do ekstrakcji: **z klasyfikatora** (pełny pipeline).

Tryb ekstrakcji: **hybrid** — do modelu wysłano 180 dok. (z pamięci podręcznej: 60), pominięto 0 (reguły kompletne), błędy LLM: 0; nowe tokeny: wejście 191513, wyjście 24406.

## Podsumowanie

| | TP | FP | FN | Precision | Recall | F1 (UZP) | F1 (dokładne) |
|---|---|---|---|---|---|---|---|
| **RAZEM** | 2032 | 0 | 0 | 1.000 | 1.000 | **1.000** | 0.953 |
| odwolanie (60 dok.) | 1214 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
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
| `OdwolanieKIO.czynnosc_dzien` | 60 | 0 | 0 | 1.000 | 1.000 | **1.000** | 1.000 |
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

Przykładowe różnice dokładne (40 z 96):

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
- `przyklad_14` `przelew_bankowy.na_rachunek`: oczekiwano ["70127936703217946356148898"], otrzymano ["PL70127936703217946356148898"]
- `przyklad_14` `przelew_bankowy.z_rachunku`: oczekiwano ["65163294615868454368277984"], otrzymano ["PL65163294615868454368277984"]
- `przyklad_17` `przelew_bankowy.na_rachunek`: oczekiwano ["40948702352746681959149838"], otrzymano ["PL40948702352746681959149838"]
- `przyklad_17` `przelew_bankowy.z_rachunku`: oczekiwano ["21671392196881757429472751"], otrzymano ["PL21671392196881757429472751"]
- `przyklad_19` `przelew_bankowy.na_rachunek`: oczekiwano ["98259602737060888831984936"], otrzymano ["PL98259602737060888831984936"]
- `przyklad_19` `przelew_bankowy.z_rachunku`: oczekiwano ["97552076088416465820563693"], otrzymano ["PL97552076088416465820563693"]
- `przyklad_20` `przelew_bankowy.na_rachunek`: oczekiwano ["81296583508215258243090935"], otrzymano ["PL81296583508215258243090935"]
- `przyklad_20` `przelew_bankowy.z_rachunku`: oczekiwano ["83849557122740895669356241"], otrzymano ["PL83849557122740895669356241"]
- `przyklad_23` `przelew_bankowy.na_rachunek`: oczekiwano ["31263692113897855587588527"], otrzymano ["PL31263692113897855587588527"]
- `przyklad_23` `przelew_bankowy.z_rachunku`: oczekiwano ["40507561379331317832598717"], otrzymano ["PL40507561379331317832598717"]
- `przyklad_24` `przelew_bankowy.na_rachunek`: oczekiwano ["37497545976859306820772856"], otrzymano ["PL37497545976859306820772856"]
- `przyklad_24` `przelew_bankowy.z_rachunku`: oczekiwano ["21098240169258849380864560"], otrzymano ["PL21098240169258849380864560"]
- `przyklad_25` `przelew_bankowy.na_rachunek`: oczekiwano ["26435909972191537905850420"], otrzymano ["PL26435909972191537905850420"]
- `przyklad_25` `przelew_bankowy.z_rachunku`: oczekiwano ["92476215236332523894371099"], otrzymano ["PL92476215236332523894371099"]
- `przyklad_26` `przelew_bankowy.na_rachunek`: oczekiwano ["70953449300090369058127127"], otrzymano ["PL70953449300090369058127127"]
- `przyklad_26` `przelew_bankowy.z_rachunku`: oczekiwano ["00880509913633331687549357"], otrzymano ["PL00880509913633331687549357"]
- `przyklad_28` `przelew_bankowy.na_rachunek`: oczekiwano ["02985526938978681496365038"], otrzymano ["PL02985526938978681496365038"]
- `przyklad_28` `przelew_bankowy.z_rachunku`: oczekiwano ["34214818386561206921524195"], otrzymano ["PL34214818386561206921524195"]
- `przyklad_29` `przelew_bankowy.na_rachunek`: oczekiwano ["04079856982163338024690274"], otrzymano ["PL04079856982163338024690274"]
- `przyklad_29` `przelew_bankowy.z_rachunku`: oczekiwano ["78686803479783141916212008"], otrzymano ["PL78686803479783141916212008"]
