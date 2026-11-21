#!/usr/bin/env sh
# Odwołania2json — przetwarzanie wsadowe: wszystkie PDF-y z ./input -> pliki JSON w ./output
# Wymaga: Docker (docker compose). Użycie: ./start.sh
set -u
cd "$(dirname "$0")"

if ! command -v docker >/dev/null 2>&1; then
    echo "[BŁĄD] Nie znaleziono polecenia 'docker'." >&2
    exit 2
fi
if ! docker info >/dev/null 2>&1; then
    echo "[BŁĄD] Docker nie działa — uruchom go i spróbuj ponownie." >&2
    exit 2
fi

# Ustawienia: .env.overdrive (jeśli istnieje, .env jest pomijany) albo .env
envfile=.env
[ -f .env.overdrive ] && envfile=.env.overdrive
if [ ! -f "$envfile" ]; then
    cp .env.example .env
    echo "[UWAGA] Utworzono .env z .env.example — wpisz LLM_API_KEY, aby włączyć AI (bez klucza: same reguły)."
fi
echo "Ustawienia: $envfile"
mkdir -p input output meta

echo "Przetwarzanie ./input -> ./output ..."
docker compose --env-file "$envfile" --profile batch run --rm --build cli
result=$?

if [ "$result" -eq 0 ]; then
    echo
    echo "Wyniki: $(pwd)/output"
else
    echo
    echo "[UWAGA] Zakończono z błędami (kod $result) — szczegóły powyżej."
fi
exit "$result"
