"""
generate.py — Reformulation par le LLM (le SEUL endroit qui consomme des tokens).

Règles d'économie strictes :
  • UN SEUL appel LLM par article.
  • Entrée = titre + résumé (<=300 mots). Jamais l'article complet.
  • Prompt système < 80 mots. Pas d'historique. max_tokens <= 400. Température basse.
  • Le LLM renvoie UNIQUEMENT de la prose (pas de liens, pas de hashtags) :
    le code ajoute ensuite liens + hashtags + mise en forme (déterministe).
  • Fournisseur interchangeable via la variable d'environnement LLM_PROVIDER :
        gemini (défaut) | groq | ollama
  • En cas d'échec ou de quota dépassé : repli immédiat sur les gabarits sans IA,
    AUCUNE nouvelle tentative en boucle.
"""

import json
import os
import re

import requests

from templates import (SITE, choisir_hashtags, fallback_textes)

# --- Réglages communs ------------------------------------------------------
TEMPERATURE = 0.3
MAX_TOKENS = 400
TIMEOUT = 30  # secondes

# Prompt système (< 80 mots), français, ton humble et pédagogique.
SYSTEME = (
    "Tu reformules l'annonce d'un article de blog cybersécurité, en français, "
    "ton humble et pédagogique d'un étudiant en pentest, sans exagération marketing. "
    "Réponds UNIQUEMENT en JSON avec les clés : bluesky, mastodon, linkedin, "
    "reddit_title, reddit_body. Chaque valeur est du texte court, sans hashtag ni "
    "lien ni emoji. Longueurs : bluesky <=200 caractères, mastodon <=400, "
    "linkedin 3-4 phrases, reddit_title <=100, reddit_body 3-5 phrases."
)

CLES = ["bluesky", "mastodon", "linkedin", "reddit_title", "reddit_body"]


# --- Extraction robuste du JSON renvoyé par le modèle ----------------------
def _extraire_json(texte: str) -> dict | None:
    if not texte:
        return None
    texte = texte.strip()
    texte = re.sub(r"^```(json)?", "", texte).strip()
    texte = re.sub(r"```$", "", texte).strip()
    try:
        return json.loads(texte)
    except json.JSONDecodeError:
        pass
    # Dernier recours : on isole le premier objet { ... }
    m = re.search(r"\{.*\}", texte, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return None


# --- Fournisseurs ----------------------------------------------------------
def _appel_gemini(user: str) -> dict | None:
    cle = os.environ.get("GEMINI_API_KEY")
    if not cle:
        return None
    modele = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{modele}:generateContent?key={cle}")
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEME}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "temperature": TEMPERATURE,
            "maxOutputTokens": MAX_TOKENS,
            "responseMimeType": "application/json",
        },
    }
    r = requests.post(url, json=payload, timeout=TIMEOUT)
    if not r.ok:
        raise RuntimeError(f"HTTP {r.status_code} — {r.text[:400]}")
    data = r.json()
    return _extraire_json(data["candidates"][0]["content"]["parts"][0]["text"])


def _appel_groq(user: str) -> dict | None:
    cle = os.environ.get("GROQ_API_KEY")
    if not cle:
        return None
    modele = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": modele,
        "messages": [
            {"role": "system", "content": SYSTEME},
            {"role": "user", "content": user},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {cle}"}
    r = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
    if not r.ok:
        raise RuntimeError(f"HTTP {r.status_code} — {r.text[:400]}")
    return _extraire_json(r.json()["choices"][0]["message"]["content"])


def _appel_ollama(user: str) -> dict | None:
    base = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    modele = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")
    payload = {
        "model": modele,
        "messages": [
            {"role": "system", "content": SYSTEME},
            {"role": "user", "content": user},
        ],
        "format": "json",
        "stream": False,
        "options": {"temperature": TEMPERATURE, "num_predict": MAX_TOKENS},
    }
    r = requests.post(f"{base}/api/chat", json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    return _extraire_json(r.json()["message"]["content"])


_FOURNISSEURS = {"gemini": _appel_gemini, "groq": _appel_groq, "ollama": _appel_ollama}


def _reformuler(titre: str, resume: str) -> dict | None:
    """Un seul appel LLM. Renvoie un dict ou None (jamais de retry en boucle)."""
    provider = os.environ.get("LLM_PROVIDER", "gemini").lower()
    fn = _FOURNISSEURS.get(provider)
    if fn is None:
        print(f"[generate] fournisseur inconnu '{provider}' -> repli sans IA")
        return None
    user = f"Titre: {titre}\nRésumé: {resume}"
    try:
        res = fn(user)
    except Exception as e:  # quota, réseau, 4xx/5xx... : on ne réessaie pas
        print(f"[generate] échec LLM ({provider}) : {e} -> repli sans IA")
        return None
    if not res or not all(k in res for k in CLES):
        print("[generate] réponse LLM incomplète -> repli sans IA")
        return None
    return res


# --- Assemblage final (déterministe, sans IA) ------------------------------
def _habiller(prose: str, url: str, tags: list[str], limite: int) -> str:
    """Ajoute le lien et les hashtags, puis coupe proprement à la limite."""
    tags_txt = " ".join(tags)
    # On réserve la place du lien + hashtags, le reste pour la prose.
    reste = limite - len(url) - len(tags_txt) - 4
    if len(prose) > reste:
        prose = prose[:max(0, reste - 1)].rsplit(" ", 1)[0] + "…"
    return f"{prose}\n{url}\n{tags_txt}".strip()


def generer_posts(titre: str, resume: str, url: str) -> dict:
    """
    Point d'entrée : renvoie un dict prêt à publier :
      { bluesky, mastodon, linkedin, reddit_title, reddit_body,
        hashtags, source_ia (bool) }
    """
    res = _reformuler(titre, resume)
    source_ia = res is not None
    if not source_ia:
        res = fallback_textes(titre, resume)

    tags = choisir_hashtags(titre, resume)

    # Bluesky 300 car. max (on vise 300 pile), Mastodon 500 (on vise 500).
    bluesky = _habiller(res["bluesky"], url, tags, limite=300)
    mastodon = _habiller(res["mastodon"], url, tags, limite=500)

    return {
        "bluesky": bluesky,
        "mastodon": mastodon,
        "linkedin": f"{res['linkedin']}\n\n{url}\n{' '.join(tags)}",
        "reddit_title": res["reddit_title"][:300],
        "reddit_body": f"{res['reddit_body']}\n\nArticle complet : {url}",
        "hashtags": tags,
        "source_ia": source_ia,
    }
