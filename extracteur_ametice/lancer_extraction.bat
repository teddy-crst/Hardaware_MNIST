@echo off
rem Extraction complete des fiches AMeTICE, en un double-clic.
rem 1. installe ce qu'il faut (une seule fois), 2. extrait les fiches,
rem 3. prepare offres_ametice_carte.json pour la carte.
chcp 65001 >nul
cd /d "%~dp0"
title Extracteur AMeTICE

echo ============================================================
echo  Extracteur AMeTICE - stages M2 Sciences de la Mer
echo ============================================================
echo.

set "PY="
where py >nul 2>nul && set "PY=py"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
  echo Python n'est pas installe sur cet ordinateur.
  echo Installe-le depuis python.org en cochant "Add python.exe to PATH",
  echo puis relance ce fichier.
  start "" https://www.python.org/downloads/
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Premiere utilisation : creation de l'environnement Python...
  %PY% -m venv .venv || goto :erreur
)
set "VPY=.venv\Scripts\python.exe"

echo Installation des modules (quelques minutes la premiere fois)...
"%VPY%" -m pip install --disable-pip-version-check -q -r requirements.txt || goto :erreur
"%VPY%" -m playwright install chromium || goto :erreur

echo.
echo Une fenetre Chromium va s'ouvrir sur AMeTICE.
echo Connecte-toi avec ton compte AMU (ENT), puis laisse tourner :
echo compter 15 a 25 minutes pour tous les sujets. Ne ferme pas la fenetre.
echo.
"%VPY%" extract_stages.py || goto :erreur

echo.
"%VPY%" preparer_carte.py || goto :erreur

echo.
echo ============================================================
echo  Termine. Depose offres_ametice_carte.json dans l'onglet
echo  "Sujets AMeTICE" de la carte (ou envoie-le a Claude).
echo ============================================================
explorer /select,"%cd%\offres_ametice_carte.json"
pause
exit /b 0

:erreur
echo.
echo Une erreur est survenue. Copie le texte ci-dessus et envoie-le a Claude.
pause
exit /b 1
