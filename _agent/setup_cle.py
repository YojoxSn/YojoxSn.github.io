"""
setup_cle.py — Enregistre ta clé Gemini UNE fois, sans la taper dans une commande.

Lance :  python3 _agent/setup_cle.py
Colle ta clé quand c'est demandé (elle reste invisible), et c'est fini.
La clé est écrite dans _agent/.env.local (fichier privé, ignoré par Git).
"""
import getpass
import os
import stat
from pathlib import Path

ENV = Path(__file__).resolve().parent / ".env.local"

print("Colle ta clé Gemini (elle commence par AIza) puis Entrée.")
print("Rien ne s'affichera pendant que tu colles, c'est normal (sécurité).")
cle = getpass.getpass("Clé Gemini : ").strip()

if not cle:
    raise SystemExit("❌ Aucune clé saisie.")
if not cle.startswith("AIza"):
    print(f"⚠️  Attention : ta clé ne commence pas par 'AIza' "
          f"(elle commence par '{cle[:4]}'). C'est peut-être la mauvaise valeur.")
if len(cle) < 30:
    print(f"⚠️  Attention : ta clé semble courte ({len(cle)} caractères).")

# On conserve d'éventuelles autres lignes déjà présentes, sauf GEMINI_API_KEY.
lignes = []
if ENV.exists():
    lignes = [l for l in ENV.read_text().splitlines()
              if l and not l.startswith("GEMINI_API_KEY=")]
lignes.append(f"GEMINI_API_KEY={cle}")
ENV.write_text("\n".join(lignes) + "\n", encoding="utf-8")
os.chmod(ENV, stat.S_IRUSR | stat.S_IWUSR)  # lecture/écriture pour toi seul (600)

print(f"\n✅ Clé enregistrée dans {ENV} (longueur {len(cle)}).")
print("Tu peux maintenant me dire « c'est fait », je lance le test.")
