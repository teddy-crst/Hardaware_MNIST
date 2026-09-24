# Extracteur AMeTICE — stages M2 Sciences de la Mer

Récupère les fiches de stage du cours AMeTICE « Stage de M2 », puis prépare un
fichier à déposer dans la carte des stages (onglet « Sujets AMeTICE »).

## Le plus simple (Windows)

Double-clique sur `lancer_extraction.bat`. Il installe ce qu'il faut dans un
environnement `.venv` (une seule fois), ouvre AMeTICE dans Chromium pour que tu
te connectes par l'ENT, extrait toutes les fiches, puis prépare
`offres_ametice_carte.json` pour la carte. Si Windows affiche un avertissement
SmartScreen, clique sur « Informations complémentaires » puis « Exécuter quand
même ».

## Installation manuelle

```
pip install -r requirements.txt
playwright install chromium
```

## 1. Extraire les fiches

```
python extract_stages.py
```

Au premier lancement, Chromium s'ouvre sur AMeTICE : connecte-toi via l'ENT.
La session est gardée dans `ametice_profile/` (ignoré par git : il contient tes
cookies de connexion).

Sorties : `stages_ametice.csv`, `stages_ametice.xlsx` et les pièces jointes dans
`documents_stages/`. Chaque ligne indique sa section (« SUJETS STAGE M2
2026-2027 », « Archives stages M2 2025-2026 »…).

Réglages en tête de `extract_stages.py` :

- `SECTIONS_INCLUDE` / `SECTIONS_EXCLUDE` : sections parcourues. Par défaut les
  sujets de l'année et les archives de stages, sans les directives, les dépôts,
  les soutenances ni les thèses. Pour l'année en cours seulement :
  `SECTIONS_INCLUDE = r"sujets stage m2"`.
- `REPRENDRE = True` : après une coupure, les fiches déjà extraites sans erreur
  ne sont pas retéléchargées.

## 2. Préparer pour la carte

```
python preparer_carte.py
```

Produit `offres_ametice_carte.json` : titre nettoyé, laboratoire et ville
déduits (du titre d'abord, sinon du texte de la fiche), coordonnées, mention de
la plongée avec l'extrait, lien AMeTICE. Dépose ce fichier dans l'onglet
« Sujets AMeTICE » de la carte.

## Corrections par rapport à la première version

- La section « Stage de M2 » était introuvable telle quelle : ce texte apparaît
  d'abord dans « Généralités », qui ne contient que le forum. Le script parcourt
  maintenant toutes les sections et filtre par titre.
- `Locator.eval_on_selector_all` n'existe pas dans Playwright (seulement sur
  `Page`) : remplacé par `locator("a[href]").evaluate_all(...)`.
- Les ressources Moodle (`/mod/resource/`) et les liens (`/mod/url/`) sont
  ouverts avec `redirect=1`, sinon Moodle renvoie souvent une page HTML au lieu
  du fichier ou du site externe.
- Les liens « activité précédente / suivante » de chaque fiche ne sont plus
  téléchargés comme pièces jointes.
- Les suffixes cachés « Fichier », « URL », « Page », « Dossier » sont retirés
  des titres.
