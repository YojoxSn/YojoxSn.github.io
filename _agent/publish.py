"""
publish.py — Publication sur les plateformes à API gratuite + brouillons.

Publie automatiquement : Bluesky, Mastodon, Dev.to.
Ne publie JAMAIS : LinkedIn, Reddit -> brouillons dans drafts.md.

Mode DRY_RUN=true : rien n'est publié, tout est seulement affiché.
"""

import os
from datetime import datetime, timezone
from pathlib import Path

import requests

from templates import SITE

DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"


def _log(msg: str) -> None:
    print(("[DRY_RUN] " if DRY_RUN else "[PUBLIÉ] ") + msg)


# --- Bluesky (AT Protocol via atproto) -------------------------------------
def publier_bluesky(texte: str) -> bool:
    if DRY_RUN:
        _log("Bluesky :\n" + texte + "\n")
        return True
    handle = os.environ.get("BLUESKY_HANDLE")
    mdp = os.environ.get("BLUESKY_APP_PASSWORD")
    if not (handle and mdp):
        print("[bluesky] identifiants manquants -> ignoré")
        return False
    from atproto import Client, client_utils

    client = Client()
    client.login(handle, mdp)

    # On rend le lien cliquable (facet). Le texte reçu est : prose\nURL\ntags
    lignes = texte.split("\n")
    url = next((l for l in lignes if l.startswith("http")), "")
    prose = texte.split("\n" + url)[0] if url else texte
    tags_ligne = lignes[-1] if lignes and lignes[-1].startswith("#") else ""

    tb = client_utils.TextBuilder()
    tb.text(prose + "\n")
    if url:
        tb.link(url, url)
    if tags_ligne:
        tb.text("\n")
        for tag in tags_ligne.split():
            tb.tag(tag + " ", tag.lstrip("#"))
    client.send_post(tb)
    _log("Bluesky OK")
    return True


# --- Mastodon (Mastodon.py) ------------------------------------------------
def publier_mastodon(texte: str) -> bool:
    if DRY_RUN:
        _log("Mastodon :\n" + texte + "\n")
        return True
    token = os.environ.get("MASTODON_ACCESS_TOKEN")
    base = os.environ.get("MASTODON_API_BASE", "https://infosec.exchange")
    if not token:
        print("[mastodon] token manquant -> ignoré")
        return False
    from mastodon import Mastodon

    m = Mastodon(access_token=token, api_base_url=base)
    m.status_post(texte, visibility="public", language="fr")
    _log("Mastodon OK")
    return True


# --- Dev.to (API REST) -----------------------------------------------------
def publier_devto(titre: str, corps_html: str, url_canonique: str,
                  tags: list[str]) -> bool:
    """Republie l'article avec canonical_url pointant vers ton site (SEO safe)."""
    # Conversion HTML -> Markdown (léger). Repli : résumé + lien.
    try:
        from markdownify import markdownify
        body_md = markdownify(corps_html, heading_style="ATX").strip()
    except Exception:
        body_md = ""
    if len(body_md) < 50:
        body_md = f"*(Extrait — article complet sur mon site.)*"
    body_md += f"\n\n---\n\n👉 **Article original :** {url_canonique}"

    # Dev.to : tags en minuscules, alphanumériques, 4 max.
    dev_tags = [t.lstrip("#").lower() for t in tags][:4]

    if DRY_RUN:
        _log(f"Dev.to : « {titre} » (canonical={url_canonique}, tags={dev_tags})\n")
        return True

    cle = os.environ.get("DEVTO_API_KEY")
    if not cle:
        print("[devto] clé manquante -> ignoré")
        return False
    payload = {"article": {
        "title": titre,
        "body_markdown": body_md,
        "published": True,
        "canonical_url": url_canonique,
        "tags": dev_tags,
    }}
    r = requests.post("https://dev.to/api/articles",
                      json=payload, headers={"api-key": cle}, timeout=30)
    r.raise_for_status()
    _log("Dev.to OK")
    return True


# --- Brouillons LinkedIn + Reddit (jamais publiés automatiquement) ---------
def ecrire_brouillons(drafts_path: Path, titre: str, posts: dict) -> None:
    horo = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    bloc = f"""
## {titre}
_Préparé le {horo} — à copier-coller à la main (API payantes / règles anti-spam)._

### LinkedIn
{posts['linkedin']}

### Reddit (ex. r/cybersecurity, r/netsecstudents)
**Titre :** {posts['reddit_title']}

{posts['reddit_body']}

---
"""
    with drafts_path.open("a", encoding="utf-8") as f:
        f.write(bloc)
    print(f"[brouillons] ajoutés pour « {titre} » dans {drafts_path.name}")
