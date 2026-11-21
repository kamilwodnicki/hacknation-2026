# Jak dodać nowy typ dokumentu (bez programowania)

Każdy typ dokumentu to **jeden plik YAML** w `config/document_types/`. Plik opisuje:

1. **jak rozpoznać dokument** (`classification`),
2. **jaki JSON zwrócić** (`output` — struktura 1:1 z oczekiwanym formatem),
3. **skąd brać każdą wartość** (reguły `extract`) i **jak ma pomóc AI** (`description`, `llm`).

Po zapisaniu pliku typ jest od razu obsługiwany przez CLI, API, GUI i tryb z AI. Błąd w pliku (np. literówka w nazwie typu wartości) jest zgłaszany przy starcie z nazwą pliku i pola.

## Przykład: „Zawiadomienie o wyborze najkorzystniejszej oferty”

Zapisz jako `config/document_types/zawiadomienie_wybor.yaml`:

```yaml
name: zawiadomienie_wybor
description: Zawiadomienie zamawiającego o wyborze najkorzystniejszej oferty

classification:
  keywords:                      # +1 punkt za każde znalezione (bez względu na wielkość liter i polskie znaki)
    - wybór najkorzystniejszej oferty
    - zawiadomienie o wyborze
    - zamawiający informuje
    - punktacja
  titles:                        # +3 punkty, gdy linia nagłówka jest dokładnie taka
    - Zawiadomienie o wyborze najkorzystniejszej oferty
  exclude:                       # te frazy w nagłówku wykluczają typ
    - odwołanie
  min_score: 3

output:
  Zawiadomienie:
    data:
      type: date
      description: Data zawiadomienia z nagłówka.
      extract:
        - method: regex
          pages: 1
          flags: [MULTILINE]
          pattern: '^\s*{place}\s*,?\s+(?:dnia\s+)?({value})'
    numer_postepowania:
      type: reference
      extract:
        - method: label
          labels: [Znak sprawy, Numer postępowania, Nr postępowania]
    wybrany_wykonawca:
      type: company
      description: Pełna nazwa wykonawcy, którego ofertę wybrano.
      extract:
        - method: regex
          pattern: 'wybrana\s+została\s+oferta\s+(?:wykonawcy\s+)?({value})'
    cena:
      type: amount
      extract:
        - method: label
          labels: [Cena oferty, Cena brutto]
  Oferty:
    type: list                   # lista elementów
    description: Wszystkie oferty z punktacją.
    split:
      method: matches            # każde dopasowanie = jeden element; nazwana grupa = pole
      pattern: '(?P<wykonawca>{company})[^\n]*?(?P<punkty>\d+(?:,\d+)?)\s*pkt'
    item:
      wykonawca: {type: company}
      punkty: {type: amount}
```

Gotowe. Sprawdź na przykładowym pliku:

```
docker compose run --rm tests python -m src.ingestion /data/sciezka/do/pliku.pdf --text   # jak wygląda tekst
docker compose up -d --build                                                            # GUI: http://localhost:8501
```

## Typy wartości (`type`)

Typ odpowiada za **wzorzec wyszukiwania** i **normalizację** do formatu UZP.

| Typ | Przykład w dokumencie | Wynik |
|---|---|---|
| `date` | `5 marca 2026 r.`, `05.03.2026`, `2026-03-05` | `2026-03-05` |
| `amount` | `10 000,00 zł`, `PLN 34.00` | `10000.0` |
| `iban_pl` | `PL61 1090 1014 0000 0712 1981 2874` | `61109010140000071219812874` |
| `nip`, `regon`, `krs`, `pesel` | `NIP: 554-024-05-49` | `5540240549` (+ suma kontrolna) |
| `ted` | `2025/S 112-383751` | `383751-2025` |
| `bzp` | `2025/BZP 00270698` | `2025/BZP00270698` |
| `reference` | `ZP.271.93.2026` | identyfikator (musi zawierać cyfrę) |
| `person` | `adw. Jan Kowalski` | `Jan Kowalski` |
| `company` | `Hartica Serwis S.A.` | nazwa z formą prawną |
| `place` | `Zielona Góra` | miejscowość |
| `email`, `integer`, `text` | | |

## Strategie wyszukiwania (`extract`)

Strategie są próbowane **po kolei** — pierwsza poprawna wartość wygrywa.

| Strategia | Kiedy | Najważniejsze opcje |
|---|---|---|
| `label` | wartość po etykiecie: `NIP: 123…`, `Kwota przelewu 50,00 zł` | `labels`, `lookahead` (ile linii dalej), `multiline` + `until` (tekst wieloliniowy), `pages` |
| `regex` | wartość w zdaniu: `w dniu 5 marca 2026` | `pattern` z `{value}` (wzorzec typu pola) lub `{date}`, `{person}`…, `group`, `pages` |
| `nth_match` | n-ta wartość danego typu w tekście | `n` |
| `keyword_map` | wartość zależna od słów, np. powód odwołania | `within` (fragment), `map` (wartość → słowa; kolejność ma znaczenie), `default` |
| `derived` | wartość wyliczana z innego pola | `from`, `if_present`, `if_absent` |
| `lookup` | wartość ze słownika `config/dictionaries/<nazwa>.yaml` | `from`, `dictionary` |

## Listy (`type: list`)

| Opcja | Znaczenie |
|---|---|
| `split: {method: section}` | elementy to bloki tekstu od etykiety `start` do `end`; `item_marker` dzieli blok na „1)”, „2)” |
| `split: {method: matches}` | każde dopasowanie wzorca to element; nazwana grupa `(?P<pole>…)` od razu wypełnia pole |
| `split: {method: whole}` | cały tekst (lub pierwsze `pages` stron) to jeden element |
| `split: [ … ]` | lista alternatyw — pierwsza, która znajdzie elementy, wygrywa |
| `unique_by`, `max_items`, `scope: document` | usuwanie duplikatów, limit, wyszukiwanie w całym dokumencie (listy zagnieżdżone) |

## Zabezpieczenia precyzji

Zła wartość kosztuje w F1 więcej niż jej brak, dlatego pole może odrzucać niepewne kandydatury:

- `must_match: '^[A-ZĄĆĘŁŃÓŚŹŻ]'` — wartość musi pasować do wzorca,
- `reject: ['^(KRS|NIP|tel)\b']` — wartości do odrzucenia (np. same etykiety),
- `checksum` / `on_invalid_checksum: reject` — suma kontrolna NIP/REGON/PESEL/IBAN.

## Współpraca z AI (tryb `hybrid` / `llm`)

Model dostaje prompt **budowany automatycznie z tego samego pliku YAML**: szablon JSON, typ i `description` każdego pola, dozwolone wartości słownikowe. Dobry `description` = lepsza odpowiedź modelu.

| Opcja pola | Działanie |
|---|---|
| `llm: fill` (domyślnie) | AI uzupełnia tylko pola, których reguły nie znalazły |
| `llm: prefer` | poprawna wartość AI wygrywa z regułą |
| `llm: arbitrate` | przy sporze reguła–AI krótkie drugie zapytanie wybiera wartość na podstawie obu fragmentów |
| `llm: never` | AI nie zmienia pola (np. gdy `null` jest poprawną odpowiedzią) |
| `llm_evidence: true` | AI najpierw cytuje zdanie z dokumentu, potem podaje wartość (lepsze rozumowanie, cytat widoczny w GUI) |
| `trusted: true` (opcja **strategii** w `extract`) | wartość znaleziona przez tę strategię zostaje — AI jej nie zastępuje ani nie arbitruje; słabsze strategie tego samego pola nadal mogą być poprawiane |

Przy listach element z reguł i element od AI są parowane po polach `unique_by`, a gdy reguła wzięła złą nazwę — po NIP/KRS/REGON/PESEL. Element, którego reguły nie znalazły, AI dodaje tylko wtedy, gdy ma taki identyfikator, obecny w treści dokumentu.

Typ dokumentu **bez żadnych reguł** (same `type` + `description`) też działa — w trybie `llm` cały JSON wypełnia model.

## Pomiar jakości nowego typu

Dodaj przypadki z wzorcowymi JSON-ami do zbioru ewaluacyjnego (`config/evaluation/*.yaml`, sekcja `documents`) i uruchom:

```
docker compose run --rm tests python -m src.evaluation --dataset config/evaluation/moj_zbior.yaml
```

Raport pokaże F1 dla każdego pola i listę różnic.
