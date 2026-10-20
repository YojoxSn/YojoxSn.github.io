"""
templates.py — Modèles de texte SANS IA.

Tout ce qui est déterministe vit ici : hashtags, liens, gabarits de posts
de secours (si le LLM échoue) et le post hebdomadaire de progression.
Aucun appel réseau, aucun token consommé.
"""

# --- Constantes du site ----------------------------------------------------
SITE = "https://yojoxsn.github.io"
THM_PROFILE = "https://tryhackme.com/p/YojoxSn"
GITHUB_PROFILE = "https://github.com/YojoxSn"
AUTEUR = "Jonas Sleiman"

# Hashtags pertinents et limités (règle anti-spam : 3 maximum).
# On en choisit 3 selon le type d'article, puisés dans cette liste.
HASHTAGS = {
    "writeup":  ["#TryHackMe", "#CTF", "#cybersecurity"],
    "tuto":     ["#pentest", "#cybersecurity", "#infosec"],
    "veille":   ["#infosec", "#cybersecurity", "#veille"],
    "vuln":     ["#pentest", "#CVE", "#cybersecurity"],
    "default":  ["#cybersecurity", "#pentest", "#TryHackMe"],
}


def choisir_hashtags(titre: str, resume: str) -> list[str]:
    """Choisit 3 hashtags d'après des mots-clés présents dans le texte."""
    t = (titre + " " + resume).lower()
    if any(m in t for m in ("writeup", "write-up", "ctf", "room", "challenge")):
        return HASHTAGS["writeup"]
    if any(m in t for m in ("tuto", "guide", "comment ", "mise en place", "installer")):
        return HASHTAGS["tuto"]
    if any(m in t for m in ("cve", "faille", "vulnérab", "vulnerab", "exploit")):
        return HASHTAGS["vuln"]
    if any(m in t for m in ("veille", "actualité", "actu", "tendance")):
        return HASHTAGS["veille"]
    return HASHTAGS["default"]


# --- Gabarits de SECOURS (utilisés si le LLM est indisponible) -------------
def fallback_textes(titre: str, resume: str) -> dict:
    """
    Versions 100 % sans IA, écrites à partir de modèles.
    Même structure de sortie que le LLM pour que le reste du code
    n'ait pas à savoir d'où vient le texte.
    """
    accroche = resume.strip()
    if len(accroche) > 180:
        accroche = accroche[:177].rsplit(" ", 1)[0] + "…"
    return {
        "bluesky":      f"Nouvel article sur mon blog : « {titre} ». {accroche}",
        "mastodon":     f"Nouvel article sur mon blog cybersécurité : « {titre} ».\n\n{accroche}",
        "linkedin":     (f"Je viens de publier un nouvel article sur mon blog : « {titre} ».\n\n"
                         f"{accroche}\n\n"
                         f"Je me forme au pentest et je partage mes notes au fil de l'eau. "
                         f"Retours bienvenus."),
        "reddit_title": titre,
        "reddit_body":  (f"{accroche}\n\n"
                         f"J'écris ces notes pendant ma formation au pentest, "
                         f"donc toute correction ou remarque est la bienvenue."),
    }


# --- Post hebdomadaire de PROGRESSION (sans IA) ----------------------------
def post_progression(stats: dict) -> dict:
    """
    Construit le post 'progression' à partir de stats.json.
    Ton humble et factuel, aucun superlatif marketing.
    """
    niveau   = stats.get("niveau", "?")
    ligue    = stats.get("ligue", "?")
    rang     = stats.get("rang", "?")
    serie    = stats.get("serie_max", "?")
    activ    = stats.get("activites_an", "?")

    corps = (f"Point d'étape sur ma formation en cybersécurité (TryHackMe, pseudo YojoxSn) :\n"
             f"• Niveau {niveau}, ligue {ligue}\n"
             f"• Classement : {rang}\n"
             f"• Meilleure série : {serie} jours d'affilée\n"
             f"• {activ} activités sur l'année\n\n"
             f"J'apprends chaque jour, un pas après l'autre. Objectif : devenir pentester.")

    return {
        "bluesky":      f"Point d'étape formation cybersécurité (TryHackMe) : niveau {niveau}, "
                        f"ligue {ligue}, {rang}, série record {serie} j. Objectif pentester, "
                        f"un pas après l'autre.",
        "mastodon":     corps,
        "linkedin":     corps + f"\n\nMon profil : {THM_PROFILE}",
        "reddit_title": f"Point d'étape : {rang} sur TryHackMe en formation pentest",
        "reddit_body":  corps + f"\n\nProfil : {THM_PROFILE}",
    }
