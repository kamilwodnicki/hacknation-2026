# PISMO — uruchomienie na serwerze oceniającym

## Komenda

Uruchamiana z katalogu `/opt/solution` (z `sudo`). Przetwarza wszystkie pliki PDF z `/opt/solution/input`
i zapisuje wyniki do `/opt/solution/output`, bez żadnej interakcji; kończy się sama.

```bash
docker compose --profile batch run --rm -T cli
```

- Wynik: dla każdego pliku `input/<ścieżka>/<nazwa>.pdf` powstaje `output/<ścieżka>/<nazwa>.json`
  (ta sama struktura folderów i nazwa). Dokument spoza obsługiwanych typów daje plik z `{}`.
- Metadane ekstrakcji (typ dokumentu, źródło każdej wartości) trafiają osobno do `/opt/solution/meta`.
- Obraz Dockera jest zbudowany wcześniej (`odwolania2json:latest`); komenda niczego nie pobiera ani nie buduje.

## Usługi zewnętrzne

- **LLM: Mistral AI** (Francja), endpoint UE `https://api.eu.mistral.ai/v1`, model `ministral-14b-2512`
  (Ministral 3 14B, otwarte wagi, Apache 2.0). Dane są przetwarzane w UE:
  https://docs.mistral.ai/admin/security-access/privacy
- **Klucz API:** w pliku `/opt/solution/.env` (`LLM_API_KEY=…`), poza repozytorium.
- **OCR:** lokalnie na CPU (RapidOCR + OpenVINO), bez usług zewnętrznych.
- Bez dostępu do API (brak klucza, awaria sieci) program nie przerywa pracy: zwraca wyniki z samych reguł.

## GUI (opcjonalnie)

Działa w tle i wstaje sam po restarcie serwera (`restart: unless-stopped`):
**http://&lt;adres-serwera&gt;:8080** (API: `:8000/docs`).
