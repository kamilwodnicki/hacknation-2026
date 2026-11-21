@echo off
rem Odwolania2json - przetwarzanie wsadowe: wszystkie PDF-y z .\input -> pliki JSON w .\output
rem Wymaga: Docker Desktop (docker compose). Uzycie: start.bat
setlocal
cd /d "%~dp0"

rem Uruchomienie dwuklikiem (Eksplorator: cmd /c ""...\start.bat" ") - na koncu czekamy na klawisz,
rem zeby okno nie zniknelo przed przeczytaniem wyniku. Z terminala / skryptu - bez pauzy.
set "DBLCLICK="
echo(%CMDCMDLINE%| findstr /i /c:"%~nx0\" \"" >nul && set "DBLCLICK=1"

where docker >nul 2>nul
if errorlevel 1 (
    echo [BLAD] Nie znaleziono polecenia "docker". Zainstaluj i uruchom Docker Desktop.
    set RESULT=2
    goto end
)
docker info >nul 2>nul
if errorlevel 1 (
    echo [BLAD] Docker nie dziala. Uruchom Docker Desktop i sprobuj ponownie.
    set RESULT=2
    goto end
)

rem Ustawienia: .env.overdrive (jesli istnieje, .env jest pomijany) albo .env
set ENVFILE=.env
if exist ".env.overdrive" set ENVFILE=.env.overdrive
if not exist "%ENVFILE%" (
    copy ".env.example" ".env" >nul
    echo [UWAGA] Utworzono .env z .env.example - wpisz LLM_API_KEY, aby wlaczyc AI ^(bez klucza: same reguly^).
)
echo Ustawienia: %ENVFILE%
if not exist "input" mkdir "input"
if not exist "output" mkdir "output"
if not exist "meta" mkdir "meta"

echo Przetwarzanie .\input -^> .\output ...
docker compose --env-file "%ENVFILE%" --profile batch run --rm --build cli
set RESULT=%ERRORLEVEL%

if %RESULT%==0 (
    echo.
    echo Wyniki: %CD%\output
) else (
    echo.
    echo [UWAGA] Zakonczono z bledami ^(kod %RESULT%^) - szczegoly powyzej.
)

:end
if defined DBLCLICK (
    echo.
    pause
)
exit /b %RESULT%
