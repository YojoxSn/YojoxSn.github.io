"""
detect.py — Détection des articles du blog.

Comme le site est du HTML statique (pas de Jekyll _posts/, pas de RSS),
la méthode la plus fiable ET la moins coûteuse est de SCANNER le dossier
blog/ directement dans le dépôt (l'agent tourne dedans). Aucun appel réseau,
donc aucun token consommé pour la détection.

Chaque article est : blog/<slug>/index.html
On en extrait : titre, description, URL canonique, date, résumé (<=300 mots),
corps en HTML (pour Dev.to) et un hash du contenu (pour le cache).
"""

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup

from templates import SITE


@dataclass
class Article:
    slug: str
    url: str
    titre: str
    description: str
    resume: str          # texte brut, <= 300 mots
    corps_html: str      # HTML interne de <article>, pour Dev.to
    date: str            # AAAA-MM-JJ si connue, sinon ""
    hash: str
    chemin: Path = field(repr=False, default=None)


def _nettoyer_titre(titre: str) -> str:
    """Retire le suffixe du site : « Titre – Jonas Sleiman » -> « Titre »."""
    for sep in (" – ", " | ", " — ", " - "):
        if sep in titre:
            return titre.split(sep)[0].strip()
    return titre.strip()


def _resume_300_mots(texte: str) -> str:
    mots = re.sub(r"\s+", " ", texte).strip().split(" ")
    if len(mots) <= 300:
        return " ".join(mots)
    return " ".join(mots[:300]) + "…"


def _extraire_date(soup: BeautifulSoup) -> str:
    """Cherche la date dans le JSON-LD BlogPosting, puis dans <time>."""
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        objets = data if isinstance(data, list) else [data]
        for obj in objets:
            if isinstance(obj, dict) and obj.get("datePublished"):
                return str(obj["datePublished"])[:10]
    time = soup.find("time")
    if time and time.get("datetime"):
        return str(time["datetime"])[:10]
    return ""


def parser_article(chemin: Path, slug: str) -> Article:
    html = chemin.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    # Titre : og:title sinon <title>
    og_title = soup.find("meta", property="og:title")
    titre = _nettoyer_titre(
        (og_title["content"] if og_title and og_title.get("content")
         else (soup.title.string if soup.title else slug))
    )

    # Description : meta description sinon og:description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    og_desc = soup.find("meta", property="og:description")
    description = ((meta_desc and meta_desc.get("content"))
                   or (og_desc and og_desc.get("content")) or "")

    # URL canonique : <link rel=canonical> sinon og:url sinon construite
    canon = soup.find("link", rel="canonical")
    og_url = soup.find("meta", property="og:url")
    url = ((canon and canon.get("href"))
           or (og_url and og_url.get("content"))
           or f"{SITE}/blog/{slug}/")

    # Corps : on privilégie <article>, sinon <main>, sinon <body>
    bloc = soup.find("article") or soup.find("main") or soup.body or soup
    corps_html = bloc.decode_contents() if bloc else ""
    resume = _resume_300_mots(bloc.get_text(" ", strip=True) if bloc else description)

    date = _extraire_date(soup)

    # Hash du contenu : si l'article change, le hash change -> on le retraite.
    base = (titre + "|" + description + "|" + resume[:1000]).encode("utf-8")
    h = hashlib.sha256(base).hexdigest()[:16]

    return Article(slug=slug, url=url, titre=titre, description=description,
                   resume=resume, corps_html=corps_html, date=date, hash=h,
                   chemin=chemin)


def scanner_articles(blog_dir: Path) -> list[Article]:
    """Retourne la liste des articles trouvés, triés par date croissante."""
    articles = []
    if not blog_dir.exists():
        return articles
    for enfant in sorted(blog_dir.iterdir()):
        index = enfant / "index.html"
        if enfant.is_dir() and index.exists():
            articles.append(parser_article(index, enfant.name))
    # Tri par date (les sans-date passent en dernier)
    articles.sort(key=lambda a: a.date or "9999")
    return articles
