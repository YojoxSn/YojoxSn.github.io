"""
seo.py — Tâches SEO (sans IA, sans token).

  • generer_feed()    : crée/met à jour feed.xml (Atom) à la racine du site.
  • maj_sitemap()     : ajoute les articles manquants dans sitemap.xml.
  • indexnow()        : prévient Bing + Yandex des nouvelles URL (IndexNow).
  • audit_seo()       : vérifie title/description/canonical/OG sur chaque page.

Note importante : le "ping sitemap" de Google a été supprimé par Google en 2023.
Pour Google, l'indexation passe désormais par Google Search Console
(ta balise de vérification est déjà en place). IndexNow couvre Bing et Yandex.
"""

import os
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

import requests

from templates import SITE, AUTEUR

HOST = SITE.replace("https://", "").replace("http://", "").rstrip("/")

# Pages fixes toujours présentes dans le sitemap.
PAGES_FIXES = [f"{SITE}/", f"{SITE}/projets/", f"{SITE}/blog/"]


# --- feed.xml (Atom) -------------------------------------------------------
def generer_feed(articles, feed_path: Path) -> None:
    aujourd = date.today().isoformat()
    entrees = []
    for a in articles:
        maj = a.date or aujourd
        entrees.append(f"""  <entry>
    <title>{escape(a.titre)}</title>
    <link href="{escape(a.url)}"/>
    <id>{escape(a.url)}</id>
    <updated>{maj}T00:00:00Z</updated>
    <summary>{escape(a.description or a.resume[:300])}</summary>
  </entry>""")
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Blog cybersécurité de {escape(AUTEUR)}</title>
  <link href="{SITE}/feed.xml" rel="self"/>
  <link href="{SITE}/blog/"/>
  <id>{SITE}/</id>
  <updated>{aujourd}T00:00:00Z</updated>
  <author><name>{escape(AUTEUR)}</name></author>
{chr(10).join(entrees)}
</feed>
"""
    feed_path.write_text(feed, encoding="utf-8")
    print(f"[seo] feed.xml écrit ({len(articles)} articles)")


# --- sitemap.xml -----------------------------------------------------------
def maj_sitemap(articles, sitemap_path: Path) -> list[str]:
    """
    Reconstruit sitemap.xml : pages fixes + un <url> par article.
    Renvoie la liste des URL d'articles nouvellement ajoutées (pour IndexNow).
    """
    aujourd = date.today().isoformat()
    anciennes = {}  # url -> lastmod déjà présent
    if sitemap_path.exists():
        import re
        contenu = sitemap_path.read_text(encoding="utf-8")
        for bloc in re.findall(r"<url>(.*?)</url>", contenu, re.DOTALL):
            loc = re.search(r"<loc>(.*?)</loc>", bloc)
            mod = re.search(r"<lastmod>(.*?)</lastmod>", bloc)
            if loc:
                anciennes[loc.group(1)] = mod.group(1) if mod else aujourd

    urls = []
    # Pages fixes : on garde leur date existante (pas de faux « mis à jour »).
    for p in PAGES_FIXES:
        urls.append((p, anciennes.get(p, aujourd)))
    # Articles : date de l'article, sinon date déjà connue, sinon aujourd'hui.
    for a in articles:
        urls.append((a.url, a.date or anciennes.get(a.url, aujourd)))

    corps = "\n".join(
        f"  <url>\n    <loc>{escape(u)}</loc>\n    <lastmod>{m}</lastmod>\n  </url>"
        for u, m in urls
    )
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               f"{corps}\n</urlset>\n")
    sitemap_path.write_text(sitemap, encoding="utf-8")

    nouvelles = [a.url for a in articles if a.url not in anciennes]
    print(f"[seo] sitemap.xml écrit ({len(urls)} URL, {len(nouvelles)} nouvelles)")
    return nouvelles


# --- IndexNow (Bing + Yandex) ---------------------------------------------
def indexnow(urls: list[str]) -> None:
    cle = os.environ.get("INDEXNOW_KEY")
    if not urls or not cle:
        if urls and not cle:
            print("[seo] INDEXNOW_KEY absente -> IndexNow ignoré")
        return
    if os.environ.get("DRY_RUN", "false").lower() == "true":
        print(f"[DRY_RUN] IndexNow aurait notifié : {urls}")
        return
    payload = {
        "host": HOST,
        "key": cle,
        "keyLocation": f"{SITE}/{cle}.txt",
        "urlList": urls,
    }
    try:
        r = requests.post("https://api.indexnow.org/indexnow",
                          json=payload, timeout=30)
        print(f"[seo] IndexNow -> HTTP {r.status_code} pour {len(urls)} URL")
    except Exception as e:
        print(f"[seo] IndexNow échec (non bloquant) : {e}")


# --- Audit SEO hebdomadaire ------------------------------------------------
def audit_seo(articles) -> list[str]:
    """Vérifie la présence des balises clés. Renvoie une liste d'alertes."""
    a_verifier = list(PAGES_FIXES) + [a.url for a in articles]
    attendus = ['rel="canonical"', 'property="og:title"', 'name="description"']
    alertes = []
    for url in a_verifier:
        try:
            html = requests.get(url, timeout=20).text
        except Exception as e:
            alertes.append(f"{url} : inaccessible ({e})")
            continue
        if "<title" not in html:
            alertes.append(f"{url} : <title> manquant")
        for att in attendus:
            if att not in html:
                alertes.append(f"{url} : balise manquante ({att})")
    print(f"[seo] audit : {len(alertes)} alerte(s) sur {len(a_verifier)} page(s)")
    return alertes
