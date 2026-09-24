@echo off
setlocal
rem Extraction complete des fiches AMeTICE, en un double-clic :
rem installe Python et les modules si besoin, extrait les fiches,
rem puis prepare offres_ametice_carte.json pour la carte.
cd /d "%~dp0"
title Extracteur AMeTICE

echo ============================================================
echo  Extracteur AMeTICE - stages M2 Sciences de la Mer
echo ============================================================
echo.

rem --- lance depuis le zip sans extraction : les autres fichiers manquent
if not exist "extract_stages.py" goto :pas_extrait
if not exist "requirements.txt" goto :pas_extrait

rem --- un vrai Python (l'alias du Microsoft Store ne compte pas)
set "PY="
for /f "delims=" %%i in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do set "PY=%%i"
if not defined PY for /f "delims=" %%i in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "PY=%%i"
if defined PY if not exist "%PY%" set "PY="
if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PY goto :installer_python

:python_ok
"%PY%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" || goto :python_ancien
echo Python trouve : %PY%

if not exist ".venv\Scripts\python.exe" (
  echo Premiere utilisation : preparation de l'environnement Python...
  "%PY%" -m venv .venv > installation_log.txt 2>&1 || goto :erreur_install
)
set "VPY=%CD%\.venv\Scripts\python.exe"

echo Installation des modules : 2 a 3 minutes la premiere fois...
"%VPY%" -m pip install --disable-pip-version-check -r requirements.txt >> installation_log.txt 2>&1 || goto :erreur_install
echo Preparation du navigateur...
"%VPY%" -m playwright install chromium >> installation_log.txt 2>&1 || echo   Chromium non telecharge : Microsoft Edge sera utilise.

echo.
echo Une fenetre de navigateur va s'ouvrir sur AMeTICE.
echo Connecte-toi avec ton compte AMU (ENT), puis laisse tourner :
echo compter 15 a 25 minutes. Ne ferme ni cette fenetre ni le navigateur.
echo.
"%VPY%" extract_stages.py
if errorlevel 1 goto :erreur_extraction

echo.
"%VPY%" preparer_carte.py
if errorlevel 1 goto :erreur_extraction

echo.
echo ============================================================
echo  Termine. Depose offres_ametice_carte.json dans l'onglet
echo  "Sujets AMeTICE" de la carte, ou envoie-le a Claude.
echo ============================================================
explorer /select,"%CD%\offres_ametice_carte.json"
echo.
pause
exit /b 0

:installer_python
echo Python n'est pas installe : installation automatique, quelques minutes...
where winget >nul 2>nul || goto :python_manuel
winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements
if not exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" goto :python_manuel
set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
goto :python_ok

:python_manuel
echo.
echo Installation automatique de Python impossible sur ce PC.
echo Sur la page qui s'ouvre, clique sur "Download Python", lance l'installateur
echo en cochant "Add python.exe to PATH", puis relance ce fichier.
start "" https://www.python.org/downloads/
goto :fin_erreur

:python_ancien
echo.
echo La version de Python installee est trop ancienne : il faut la 3.9 ou plus.
echo Installe la derniere version depuis la page qui s'ouvre, puis relance ce fichier.
start "" https://www.python.org/downloads/
goto :fin_erreur

:pas_extrait
echo Ce fichier a ete ouvert directement dans le zip, sans l'extraire.
echo Fais un clic droit sur extracteur_ametice.zip, choisis "Extraire tout",
echo puis double-clique sur lancer_extraction.bat dans le dossier obtenu.
goto :fin_erreur

:erreur_install
echo.
echo L'installation a echoue. Le detail est dans installation_log.txt,
echo dans ce dossier : envoie ce fichier a Claude.
goto :fin_erreur

:erreur_extraction
echo.
echo L'extraction s'est arretee. Copie le texte ci-dessus et envoie-le a Claude.
goto :fin_erreur

:fin_erreur
echo.
pause
exit /b 1
