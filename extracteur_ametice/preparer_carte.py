"""Transforme stages_ametice.csv (sortie de extract_stages.py) en
offres_ametice_carte.json, à déposer dans l'onglet « Offres » de la carte.

Pour chaque fiche : numéro, titre nettoyé, laboratoire et ville déduits
(titre d'abord, puis texte de la fiche), coordonnées, mention de la
plongée avec l'extrait correspondant, lien AMeTICE.

Usage : python preparer_carte.py [stages_ametice.csv]
"""

import csv
import json
import re
import sys
import unicodedata
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_CSV = Path(sys.argv[1] if len(sys.argv) > 1 else "stages_ametice.csv")
OUTPUT_JSON = Path("offres_ametice_carte.json")

# Longueur maximale du texte de fiche recopié dans le JSON
DETAILS_MAX = 4000


# ============================================================
# RÉFÉRENTIELS : LABORATOIRES ET VILLES
# ============================================================

# (motif, laboratoire, ville, lat, lon) — testés dans l'ordre, le
# premier qui correspond l'emporte. Les motifs plus précis d'abord.
LABOS = [
    (r"\bMIO\b.{0,25}Toulon|Toulon.{0,25}\bMIO\b", "MIO", "La Garde", 43.1360, 6.0140),
    (r"\bM\.?I\.?O\b|institut m[ée]diterran[ée]en d.oc[ée]anolog", "MIO", "Marseille — Luminy", 43.2327, 5.4400),
    (r"GIS Posidonie", "GIS Posidonie", "Marseille — Luminy", 43.2327, 5.4400),
    (r"Septentrion", "Septentrion Environnement", "Marseille", 43.2415, 5.3790),
    (r"Parc national des Calanques", "Parc national des Calanques", "Marseille", 43.2720, 5.3905),
    (r"\bCEREGE\b", "CEREGE", "Aix-en-Provence", 43.4880, 5.3310),
    (r"\bIMBE\b", "IMBE", "Marseille — Endoume", 43.2800, 5.3497),
    (r"Paul Ricard", "Institut Paul Ricard", "Île des Embiez", 43.0797, 5.7870),
    (r"Ifremer.{0,30}La Seyne|La Seyne.{0,30}Ifremer", "Ifremer", "La Seyne-sur-Mer", 43.1060, 5.8850),
    (r"Cr[ée]oc[ée]an", "Créocéan", "La Seyne-sur-Mer", 43.1060, 5.8850),
    (r"\bLOV\b|\bIMEV\b|Institut de la Mer de Villefranche", "IMEV", "Villefranche-sur-Mer", 43.6960, 7.3080),
    (r"ECOSEAS", "ECOSEAS", "Nice", 43.7166, 7.2656),
    (r"Centre Scientifique (de )?Monaco|\bCSM\b", "Centre Scientifique de Monaco", "Monaco", 43.7340, 7.4245),
    (r"STARESO", "STARESO", "Calvi", 42.5795, 8.7255),
    (r"Stella Mare", "Stella Mare", "Biguglia (Corse)", 42.6206, 9.4517),
    (r"\bEqEL\b|Universit[ée] de Corse", "Université de Corse", "Corte", 42.3040, 9.1500),
    (r"\bLECOB\b|\bLOMIC\b|\bLBBM\b|Observatoire oc[ée]anologique de Banyuls|\bOOB\b|Arago", "Observatoire de Banyuls", "Banyuls-sur-Mer", 42.4806, 3.1364),
    (r"\bCRIOBE\b.{0,40}Perpignan|Perpignan.{0,40}\bCRIOBE\b", "CRIOBE", "Perpignan", 42.6800, 2.8990),
    (r"\bCEFREM\b|\bUPVD\b", "CEFREM", "Perpignan", 42.6800, 2.8990),
    (r"\bCRIOBE\b", "CRIOBE", "Moorea", -17.4903, -149.8260),
    (r"ENTROPIE.{0,60}(Noum[ée]a|Nouvelle[- ]Cal)", "ENTROPIE", "Nouméa", -22.3036, 166.4449),
    (r"ENTROPIE", "ENTROPIE", "La Réunion", -20.9018, 55.4847),
    (r"MARBEC.{0,30}S[èe]te|S[èe]te.{0,30}MARBEC", "MARBEC", "Sète", 43.4040, 3.6930),
    (r"\bMARBEC\b", "MARBEC", "Montpellier", 43.6108, 3.8767),
    (r"\bCEFE\b", "CEFE", "Montpellier", 43.6380, 3.8640),
    (r"Androm[èe]de", "Andromède Océanologie", "Carnon", 43.5480, 3.9790),
    (r"\bEcocean\b|\bECOCEAN\b", "ECOCEAN", "Montpellier", 43.6108, 3.8767),
    (r"Biotope", "Biotope", "Mèze", 43.4270, 3.6040),
    (r"\bP2A\b", "P2A Développement", "Vic-la-Gardiole", 43.4903, 3.7967),
    (r"\bLEMAR\b|\bIUEM\b|\bBEEP\b|\bLOPS\b|\bLM2E\b|Plouzan[ée]", "IUEM / Ifremer", "Plouzané", 48.3585, -4.5700),
    (r"Station biologique de Roscoff|\bSBR\b|Roscoff", "Station biologique de Roscoff", "Roscoff", 48.7275, -3.9870),
    (r"Concarneau", "Station marine de Concarneau", "Concarneau", 47.8697, -3.9185),
    (r"Dinard|\bCRESCO\b", "Station marine de Dinard", "Dinard", 48.6400, -2.0580),
    (r"\bLEGOS\b", "LEGOS", "Toulouse", 43.5620, 1.4800),
    (r"\bLOCEAN\b", "LOCEAN", "Paris", 48.8466, 2.3563),
    (r"\bLSCE\b", "LSCE", "Gif-sur-Yvette", 48.7090, 2.1480),
    (r"\bEPOC\b", "EPOC", "Talence", 44.8060, -0.5930),
    (r"\bLIENSs?\b|\bL3i\b", "La Rochelle Université", "La Rochelle", 46.1603, -1.1511),
    (r"\bSIAME\b", "SIAME", "Anglet", 43.4850, -1.5160),
    (r"\bIPREM\b", "IPREM", "Pau", 43.2951, -0.3708),
    (r"\bLOG\b.{0,40}(Wimereux|Opale)|Wimereux", "LOG", "Wimereux", 50.7640, 1.6110),
    (r"\bDECOD\b.{0,40}Nantes|Ifremer.{0,20}Nantes|Nantes.{0,20}Ifremer", "Ifremer / DECOD", "Nantes", 47.2184, -1.5536),
    (r"\bDECOD\b.{0,40}Lorient|Ifremer.{0,20}Lorient", "Ifremer / DECOD", "Lorient", 47.7486, -3.3700),
    (r"\bDECOD\b", "DECOD", "Rennes", 48.1140, -1.7070),
]

# Villes seules (si aucun laboratoire connu n'est cité)
VILLES = [
    ("Marseille", 43.2965, 5.3698), ("Toulon", 43.1242, 5.9280), ("La Garde", 43.1360, 6.0140),
    ("La Seyne-sur-Mer", 43.1060, 5.8850), ("Nice", 43.7102, 7.2620), ("Villefranche-sur-Mer", 43.6960, 7.3080),
    ("Monaco", 43.7384, 7.4246), ("Montpellier", 43.6108, 3.8767), ("Sète", 43.4040, 3.6930),
    ("Perpignan", 42.6986, 2.8956), ("Banyuls-sur-Mer", 42.4806, 3.1364), ("Port-Vendres", 42.5185, 3.1065),
    ("Brest", 48.3904, -4.4861), ("Plouzané", 48.3585, -4.5700), ("Roscoff", 48.7275, -3.9870),
    ("Concarneau", 47.8697, -3.9185), ("Dinard", 48.6400, -2.0580), ("Lorient", 47.7486, -3.3700),
    ("Nantes", 47.2184, -1.5536), ("La Rochelle", 46.1603, -1.1511), ("Bordeaux", 44.8378, -0.5792),
    ("Arcachon", 44.6586, -1.1689), ("Toulouse", 43.6047, 1.4442), ("Paris", 48.8566, 2.3522),
    ("Gif-sur-Yvette", 48.7018, 2.1339), ("Caen", 49.1829, -0.3707), ("Boulogne-sur-Mer", 50.7264, 1.6147),
    ("Wimereux", 50.7640, 1.6110), ("Le Havre", 49.4944, 0.1079), ("Rennes", 48.1173, -1.6778),
    ("Dijon", 47.3220, 5.0415), ("Lyon", 45.7640, 4.8357), ("Aix-en-Provence", 43.5297, 5.4474),
    ("Anglet", 43.4850, -1.5160), ("Pau", 43.2951, -0.3708), ("Ajaccio", 41.9192, 8.7386),
    ("Bastia", 42.6970, 9.4503), ("Calvi", 42.5679, 8.7575), ("Corte", 42.3060, 9.1500),
    ("Nouméa", -22.2758, 166.4580), ("Papeete", -17.5350, -149.5696), ("Moorea", -17.5388, -149.8295),
    ("Mayotte", -12.7806, 45.2279), ("La Réunion", -21.1151, 55.5364), ("Guadeloupe", 16.2650, -61.5510),
    ("Martinique", 14.6415, -61.0242), ("Cayenne", 4.9224, -52.3135), ("Guyane", 4.9224, -52.3135),
    ("Saint-Pierre-et-Miquelon", 46.7811, -56.1764), ("Barcelone", 41.3874, 2.1686), ("Barcelona", 41.3874, 2.1686),
    ("Blanes", 41.6750, 2.8020), ("Gênes", 44.4056, 8.9463), ("Genova", 44.4056, 8.9463),
    ("Naples", 40.8518, 14.2681), ("Faro", 37.0440, -7.9720), ("Lisbonne", 38.7223, -9.1393),
    ("Milan", 45.4642, 9.1900), ("Bruxelles", 50.8503, 4.3517), ("Gand", 51.0543, 3.7174),
    ("Gent", 51.0543, 3.7174), ("České Budějovice", 48.9745, 14.4743), ("Oban", 56.4510, -5.4390),
]

# Même règle que la carte pour « plongée mentionnée »
PLONGEE = re.compile(
    r"plong[ée]es?\b|(?<!grands )plongeu[rs]e?s?\b|\bplonger\b|scaphandr"
    r"|aptitude (?:a|à) l.hyperbar|certificat[^.]{0,40}hyperbar"
    r"|\bCAH\s?(?:1|I|2|II)\s?[AB]?\b|\bCAH (?:indispensable|requis|obligatoire|exigé)"
    r"|classe\s?(?:1|I)\s?B\b|\bscuba\b|\bdiving\b|\bdiver\b|scientific divers|\bUVC\b"
    r"|recensements?\s+visuels?|comptages?\s+visuels?|underwater visual|\bapn[ée]e\b|snorkel",
    re.I,
)


# ============================================================
# OUTILS
# ============================================================

def clean_text(text):
    return re.sub(r"\s+", " ", text or "").strip()


def sans_accents(text):
    return unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()


def numero_et_titre(nom):
    """« 5_INRAE_DECOD_Rennes_Unravelling… » -> (5, « INRAE DECOD Rennes Unravelling… »)"""
    m = re.match(r"^\s*\(?(\d{1,3})\)?\s*[._\-–)]*\s*(.*)$", nom or "")
    if not m:
        return None, clean_text(nom)
    titre = re.sub(r"_+", " ", m.group(2))
    return int(m.group(1)), clean_text(titre)


def localiser(texte):
    for motif, labo, ville, lat, lon in LABOS:
        if re.search(motif, texte, re.I):
            return labo, ville, lat, lon
    plain = sans_accents(texte).lower()
    for ville, lat, lon in VILLES:
        if re.search(r"\b" + re.escape(sans_accents(ville).lower()) + r"\b", plain):
            return "", ville, lat, lon
    return "", "", None, None


def extrait_plongee(texte):
    m = PLONGEE.search(texte)
    if not m:
        return ""
    a, b = max(0, m.start() - 90), min(len(texte), m.end() + 120)
    return ("…" if a else "") + clean_text(texte[a:b]) + ("…" if b < len(texte) else "")


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

def main():
    if not INPUT_CSV.exists():
        sys.exit(f"Fichier introuvable : {INPUT_CSV} (lance d'abord extract_stages.py)")

    with INPUT_CSV.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))

    offres = []

    for row in rows:
        n, titre = numero_et_titre(row.get("nom_liste") or row.get("titre"))
        details = row.get("details") or ""

        # Le titre de la liste contient souvent « _LABO_Ville » : il prime
        labo, ville, lat, lon = localiser(titre)
        source = "titre"

        if lat is None:
            labo, ville, lat, lon = localiser(details[:3000])
            source = "fiche" if lat is not None else ""

        extrait = extrait_plongee(titre + " — " + details)

        offres.append({
            "n": n,
            "t": titre,
            "lab": labo,
            "v": ville,
            "lat": lat,
            "lon": lon,
            "loc_source": source,
            "section": row.get("section", ""),
            "plongee": bool(extrait),
            "extrait": extrait,
            "url": row.get("url_ametice", ""),
            "details": clean_text(details)[:DETAILS_MAX],
        })

    OUTPUT_JSON.write_text(
        json.dumps({"offres": offres}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )

    localisees = sum(1 for o in offres if o["lat"] is not None)
    plongee = [o for o in offres if o["plongee"]]

    print(f"{len(offres)} fiches · {localisees} localisées · {len(plongee)} mentionnent la plongée")
    for o in plongee:
        print(f"  ⚑ {o['t'][:90]}  ({o['v'] or 'lieu non trouvé'})")
    print(f"\nFichier prêt : {OUTPUT_JSON.resolve()}")
    print("Dépose-le dans l'onglet « Sujets AMeTICE » de la carte.")


if __name__ == "__main__":
    main()
