"""
test_gemini.py — Test rapide : vérifie que la clé Gemini marche POUR DE VRAI.

Usage (dans ton terminal) :
    export GEMINI_API_KEY="colle_ta_cle_ici"
    python3 _agent/test_gemini.py

Ça appelle Gemini UNE fois sur un article d'exemple et affiche les posts
reformulés. Si tu vois "source_ia: True", l'IA fonctionne.
"""
import os
from pathlib import Path

# Charge la clé depuis _agent/.env.local si elle y est (créée par setup_cle.py).
_env = Path(__file__).resolve().parent / ".env.local"
if _env.exists():
    for _ligne in _env.read_text(encoding="utf-8").splitlines():
        if "=" in _ligne and not _ligne.startswith("#"):
            _k, _, _v = _ligne.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

import generate

# Article d'exemple (comme un vrai writeup).
TITRE = "Writeup TryHackMe Nmap — reconnaissance réseau"
RESUME = ("Dans ce writeup, je documente pas à pas ma reconnaissance avec Nmap "
          "sur une room TryHackMe : scan des ports avec -sV et -sC, analyse des "
          "services détectés, et premières pistes d'exploitation. J'explique "
          "chaque option simplement, en tant qu'étudiant en pentest.")
URL = "https://yojoxsn.github.io/blog/intro-nmap/"

if not os.environ.get("GEMINI_API_KEY"):
    print("❌ GEMINI_API_KEY n'est pas définie. Fais d'abord :")
    print('   export GEMINI_API_KEY="ta_cle"')
    raise SystemExit(1)

os.environ.setdefault("LLM_PROVIDER", "gemini")
posts = generate.generer_posts(TITRE, RESUME, URL)

print("\n==================== RÉSULTAT ====================")
print("source_ia :", posts["source_ia"],
      "(True = Gemini a marché, False = repli sans IA)")
print("\n--- BLUESKY ---\n" + posts["bluesky"])
print("\n--- MASTODON ---\n" + posts["mastodon"])
print("\n--- LINKEDIN (brouillon) ---\n" + posts["linkedin"])
print("\n--- REDDIT (brouillon) ---")
print("Titre :", posts["reddit_title"])
print(posts["reddit_body"])
print("==================================================")
if posts["source_ia"]:
    print("\n✅ Gemini fonctionne ! Tu peux passer à la mise en ligne.")
else:
    print("\n⚠️  Repli sans IA utilisé : vérifie ta clé ou le nom du modèle "
          "(variable GEMINI_MODEL).")
