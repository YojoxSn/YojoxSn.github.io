"""
main.py — Chef d'orchestre de l'agent.

Déroulé d'un passage (quotidien via GitHub Actions) :
  1. Charger l'état (state.json) : articles déjà traités, dates des derniers posts.
  2. Scanner blog/ et repérer les NOUVEAUX articles (hash absent de l'état).
  3. Pour chaque nouvel article : UN appel LLM -> textes mis en cache, + brouillons.
  4. Publier en respectant « 1 post / plateforme / jour ».
  5. Régénérer feed.xml + sitemap.xml, puis IndexNow sur les nouvelles URL.
  6. Le lundi : post de progression (stats.json) + audit SEO.
  7. Sauver l'état. (Le commit Git est fait par le workflow.)

Économie de tokens : le LLM n'est appelé qu'une fois par article, jamais pour
un article déjà vu (cache par hash), jamais pour les stats (modèle sans IA).
"""

import json
import os
from datetime import date, datetime, timezone
from pathlib import Path

# Charge _agent/.env.local en local (n'existe pas sur GitHub Actions, qui
# utilise les vrais secrets). Pratique pour tester sur ta machine.
_env = Path(__file__).resolve().parent / ".env.local"
if _env.exists():
    for _ligne in _env.read_text(encoding="utf-8").splitlines():
        if "=" in _ligne and not _ligne.startswith("#"):
            _k, _, _v = _ligne.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

import detect
import generate
import publish
import seo
import templates

# --- Chemins (l'agent est dans _agent/, le site est au-dessus) -------------
AGENT_DIR = Path(__file__).resolve().parent
ROOT = AGENT_DIR.parent
BLOG_DIR = ROOT / "blog"
FEED = ROOT / "feed.xml"
SITEMAP = ROOT / "sitemap.xml"
STATE = AGENT_DIR / "state.json"
STATS = AGENT_DIR / "stats.json"
DRAFTS = AGENT_DIR / "drafts.md"

PLATEFORMES_AUTO = ["bluesky", "mastodon", "devto"]
MAX_ARTICLES_NOUVEAUX_PAR_PASSAGE = 3  # garde-fou anti-rafale


# --- État ------------------------------------------------------------------
def charger_etat() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"articles": {}, "pending": {}, "last_post": {},
            "last_stats_post": "", "last_seo_check": ""}


def sauver_etat(etat: dict) -> None:
    STATE.write_text(json.dumps(etat, indent=2, ensure_ascii=False), encoding="utf-8")


def aujourdhui() -> str:
    return date.today().isoformat()


def semaine_de(d: str) -> str:
    return datetime.fromisoformat(d).strftime("%G-W%V") if d else ""


# --- Publication d'un lot de textes sur une plateforme ---------------------
def _publier(plateforme: str, article_meta: dict, posts: dict) -> bool:
    if plateforme == "bluesky":
        return publish.publier_bluesky(posts["bluesky"])
    if plateforme == "mastodon":
        return publish.publier_mastodon(posts["mastodon"])
    if plateforme == "devto":
        return publish.publier_devto(
            article_meta["titre"], article_meta.get("corps_html", ""),
            article_meta["url"], posts["hashtags"])
    return False


def main() -> None:
    etat = charger_etat()
    today = aujourdhui()
    etat.setdefault("pending", {})
    etat.setdefault("last_post", {})

    articles = detect.scanner_articles(BLOG_DIR)
    print(f"[main] {len(articles)} article(s) trouvé(s) dans blog/")

    connus = set(etat["articles"]) | set(etat["pending"])

    # 1) Nouveaux articles -> UN appel LLM chacun, mis en file d'attente.
    nouveaux = [a for a in articles if a.hash not in connus]
    for a in nouveaux[:MAX_ARTICLES_NOUVEAUX_PAR_PASSAGE]:
        print(f"[main] nouvel article : « {a.titre} »")
        posts = generate.generer_posts(a.titre, a.resume, a.url)  # 1 seul appel LLM
        publish.ecrire_brouillons(DRAFTS, a.titre, posts)         # LinkedIn + Reddit
        etat["pending"][a.hash] = {
            "meta": {"slug": a.slug, "url": a.url, "titre": a.titre,
                     "corps_html": a.corps_html},
            "posts": posts,
            "done": [],
        }

    # 2) Post de progression hebdo (lundi) : on l'injecte comme un "pending"
    #    prioritaire, sans IA.
    est_lundi = date.today().weekday() == 0
    if est_lundi and semaine_de(etat.get("last_stats_post", "")) != semaine_de(today):
        if STATS.exists():
            stats = json.loads(STATS.read_text(encoding="utf-8"))
            sp = templates.post_progression(stats)
            tags = templates.HASHTAGS["default"]
            posts_stats = {
                "bluesky": f"{sp['bluesky']}\n{templates.THM_PROFILE}\n{' '.join(tags)}"[:300],
                "mastodon": f"{sp['mastodon']}\n\n{templates.THM_PROFILE}\n{' '.join(tags)}"[:500],
                "linkedin": sp["linkedin"], "reddit_title": sp["reddit_title"],
                "reddit_body": sp["reddit_body"], "hashtags": tags, "source_ia": False,
            }
            publish.ecrire_brouillons(DRAFTS, "Progression hebdomadaire", posts_stats)
            # Les stats ne vont pas sur Dev.to (pas un article).
            etat["pending"]["stats-" + today] = {
                "meta": {"titre": "Progression", "url": templates.THM_PROFILE},
                "posts": posts_stats, "done": ["devto"],
            }
            etat["last_stats_post"] = today

    # 3) Publication : 1 post / plateforme / jour maximum.
    for plateforme in PLATEFORMES_AUTO:
        if etat["last_post"].get(plateforme) == today:
            continue  # déjà publié aujourd'hui sur cette plateforme
        # Premier pending qui n'a pas encore cette plateforme.
        for h, entree in etat["pending"].items():
            if plateforme in entree["done"]:
                continue
            ok = _publier(plateforme, entree["meta"], entree["posts"])
            if ok:
                entree["done"].append(plateforme)
                etat["last_post"][plateforme] = today
            break

    # 4) Déplacer les pending terminés vers "articles" (cache définitif).
    termines = [h for h, e in etat["pending"].items()
                if all(p in e["done"] for p in PLATEFORMES_AUTO)]
    for h in termines:
        meta = etat["pending"][h]["meta"]
        etat["articles"][h] = {"slug": meta.get("slug", ""), "url": meta.get("url", ""),
                               "processed_at": today}
        del etat["pending"][h]

    # 5) SEO : feed + sitemap + IndexNow sur les nouvelles URL.
    seo.generer_feed(articles, FEED)
    nouvelles_urls = seo.maj_sitemap(articles, SITEMAP)
    seo.indexnow(nouvelles_urls)

    # 6) Audit SEO hebdomadaire (lundi).
    if est_lundi and semaine_de(etat.get("last_seo_check", "")) != semaine_de(today):
        alertes = seo.audit_seo(articles)
        etat["last_seo_check"] = today
        if alertes:
            horo = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            with DRAFTS.open("a", encoding="utf-8") as f:
                f.write(f"\n## [Audit SEO {horo}]\n"
                        + "\n".join(f"- ⚠️ {x}" for x in alertes) + "\n\n---\n")

    sauver_etat(etat)
    print("[main] terminé.")


if __name__ == "__main__":
    main()
