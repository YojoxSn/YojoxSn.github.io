# Agent SEO & réseaux — portfolio cybersécurité de Jonas Sleiman

Agent **100 % gratuit** qui fait connaître [yojoxsn.github.io](https://yojoxsn.github.io/) :
à chaque nouvel article de blog, il prépare et publie des posts courts
(Bluesky, Mastodon, Dev.to), prévient les moteurs de recherche, et une fois
par semaine publie un point de progression TryHackMe.

- **0 € :** tourne sur GitHub Actions (cron), pas de serveur, pas de base de
  données. L'état est un simple `state.json` versionné dans le dépôt.
- **Tokens minimaux :** le LLM ne sert QU'À reformuler. **Un seul appel par
  article**, entrée = titre + résumé (≤ 300 mots), sortie ≤ 400 tokens.
  Tout le reste (détection, hashtags, liens, SEO, stats) est du code sans IA.
- **Éthique :** 1 post/plateforme/jour max, ton humble, 3 hashtags max,
  LinkedIn/Reddit en brouillon seulement, mode `DRY_RUN` pour tester à vide.

---

## Arborescence (à placer dans le dépôt `yojoxsn.github.io`)

```
yojoxsn.github.io/
├── .github/workflows/agent.yml      # cron quotidien + bouton manuel
├── 7d9f3e2a8c4b1f60d5e7a9c2b4f6081d.txt   # clé IndexNow (publique, racine du site)
├── feed.xml                         # généré par l'agent (flux Atom)
├── sitemap.xml                      # complété par l'agent (articles ajoutés)
├── blog/<slug>/index.html           # tes articles (inchangé)
└── _agent/                          # le dossier underscore => ignoré par Jekyll
    ├── main.py          # chef d'orchestre
    ├── detect.py        # scan du dossier blog/ (sans IA, sans réseau)
    ├── generate.py      # 1 appel LLM -> reformulation (Gemini/Groq/Ollama)
    ├── publish.py       # Bluesky / Mastodon / Dev.to + brouillons
    ├── seo.py           # feed.xml, sitemap.xml, IndexNow, audit
    ├── templates.py     # textes sans IA (hashtags, gabarits, post stats)
    ├── requirements.txt
    ├── stats.json       # TES stats TryHackMe (tu les mets à jour à la main)
    ├── state.json       # mémoire des articles déjà traités
    └── drafts.md        # brouillons LinkedIn/Reddit (rempli automatiquement)
```

> Le dossier `_agent/` commence par `_` : Jekyll (actif sur ton site) ne le
> publie donc pas. Le code reste privé au sens « pas servi par le site »,
> mais visible sur GitHub (dépôt public) — n'y mets jamais de clé en clair.

---

## Installation en 8 étapes

1. **Copie** `_agent/`, `.github/workflows/agent.yml` et le fichier
   `7d9f...081d.txt` à la racine de ton dépôt `yojoxsn.github.io`, puis `git push`.
2. **Crée une clé LLM gratuite** (choisis-en UNE, voir plus bas) :
   Google Gemini *(recommandé)* ou Groq.
3. **Crée tes comptes** Bluesky, Mastodon (infosec.exchange) et Dev.to, et
   récupère leurs clés (guides détaillés plus bas).
4. Dans GitHub : **Settings → Secrets and variables → Actions → Secrets**,
   ajoute les *secrets* du tableau ci-dessous.
5. Dans le même écran, onglet **Variables**, ajoute les *variables*
   (non secrètes) : `INDEXNOW_KEY`, `LLM_PROVIDER`, et au début `DRY_RUN=true`.
6. **Test à blanc** : onglet **Actions → Agent SEO & réseaux → Run workflow**,
   laisse « Mode test » coché. Vérifie les logs : rien n'est publié, tout
   s'affiche.
7. Quand les logs te conviennent, passe la variable **`DRY_RUN=false`** (ou
   supprime-la).
8. C'est fini : le cron tourne tous les jours à 9h UTC. Écris un article dans
   `blog/<slug>/index.html` et l'agent s'en occupe au prochain passage.

---

## Secrets et variables GitHub

| Nom | Type | Obligatoire ? | Rôle |
|---|---|---|---|
| `GEMINI_API_KEY` | secret | si `LLM_PROVIDER=gemini` | Clé Google Gemini |
| `GROQ_API_KEY` | secret | si `LLM_PROVIDER=groq` | Clé Groq |
| `BLUESKY_HANDLE` | secret | pour publier sur Bluesky | ex. `yojoxsn.bsky.social` |
| `BLUESKY_APP_PASSWORD` | secret | pour publier sur Bluesky | mot de passe d'application |
| `MASTODON_ACCESS_TOKEN` | secret | pour publier sur Mastodon | jeton d'accès |
| `DEVTO_API_KEY` | secret | pour publier sur Dev.to | clé API Dev.to |
| `LLM_PROVIDER` | variable | non (défaut `gemini`) | `gemini`, `groq` ou `ollama` |
| `INDEXNOW_KEY` | variable | pour IndexNow | `7d9f3e2a8c4b1f60d5e7a9c2b4f6081d` |
| `MASTODON_API_BASE` | variable | non | défaut `https://infosec.exchange` |
| `DRY_RUN` | variable | au début `true` | `true` = ne rien publier |

> **Secret** = valeur masquée (clés). **Variable** = valeur visible (réglages).
> La clé IndexNow n'est pas un secret : elle est publique par conception.

---

## Obtenir chaque clé gratuitement (pas à pas, débutant)

### 1. Google Gemini (LLM recommandé — gratuit, quota large)
1. Va sur **https://aistudio.google.com/apikey** et connecte-toi avec un compte Google.
2. Clique **« Create API key »** → **« Create API key in new project »**.
3. Copie la clé (commence par `AIza...`).
4. GitHub → Secrets → **New secret** : nom `GEMINI_API_KEY`, valeur = la clé.
5. Variable `LLM_PROVIDER` = `gemini`. Modèle par défaut : `gemini-3.5-flash-lite`
   (le plus léger). Si Google le renomme, ajoute une variable `GEMINI_MODEL`.

### 1-bis. Groq (alternative au LLM — gratuit)
1. Va sur **https://console.groq.com/keys**, connecte-toi (Google/GitHub).
2. **« Create API Key »**, copie la clé (`gsk_...`).
3. Secret `GROQ_API_KEY` = la clé. Variable `LLM_PROVIDER` = `groq`.
4. Modèle léger par défaut : `llama-3.1-8b-instant`.

### 2. Bluesky (API AT Protocol — gratuit)
1. Crée un compte sur **https://bsky.app** (ex. handle `yojoxsn.bsky.social`).
2. Va dans **Settings → Privacy and security → App passwords → Add app password**.
3. Donne un nom (ex. « agent »), copie le mot de passe affiché (format `xxxx-xxxx-xxxx-xxxx`).
4. Secrets : `BLUESKY_HANDLE` = ton handle, `BLUESKY_APP_PASSWORD` = ce mot de passe.
   > Utilise bien un **mot de passe d'application**, jamais ton vrai mot de passe.

### 3. Mastodon / infosec.exchange (gratuit)
1. Crée un compte sur **https://infosec.exchange** (instance orientée cybersécurité).
2. **Préférences → Développement → Nouvelle application**.
3. Nom : « agent ». Laisse les permissions par défaut mais garde au moins
   **`write:statuses`**. Valide.
4. Ouvre l'application créée : copie **« Votre jeton d'accès »**.
5. Secret `MASTODON_ACCESS_TOKEN` = ce jeton. (Si tu changes d'instance,
   ajuste la variable `MASTODON_API_BASE`.)

### 4. Dev.to (gratuit)
1. Crée un compte sur **https://dev.to**.
2. **Settings → Extensions → DEV Community API Keys** (ou
   https://dev.to/settings/extensions).
3. Saisis un nom de projet, clique **« Generate API Key »**, copie la clé.
4. Secret `DEVTO_API_KEY` = la clé.

### 5. IndexNow (gratuit, sans compte)
- Rien à créer : le fichier `7d9f3e2a8c4b1f60d5e7a9c2b4f6081d.txt` à la racine
  de ton site **est** la preuve de propriété. Mets juste la variable
  `INDEXNOW_KEY` = `7d9f3e2a8c4b1f60d5e7a9c2b4f6081d`.
- Tu peux générer ta propre clé (32 caractères hexadécimaux) : renomme le
  fichier `.txt` avec cette valeur, mets la même dans son contenu et dans la variable.

---

## Estimation des tokens / mois (preuve que ça reste gratuit)

Le LLM n'est appelé **que pour reformuler un nouvel article** (jamais pour les
stats, jamais deux fois le même article grâce au cache par hash).

**Coût d'un appel :**

| Élément | ~Tokens |
|---|---|
| Prompt système (< 80 mots) | ~110 |
| Titre + résumé 300 mots (français) | ~480 |
| Consignes de format | ~40 |
| **Entrée totale** | **~630** |
| Sortie (plafonnée `max_tokens=400`) | **≤ 400** |
| **Total par article** | **~1 000** |

**Par mois**, pour un blog en construction (hypothèse large de **8 articles/mois**) :

> 8 × 1 000 ≈ **8 000 tokens / mois**.

Comparaison aux offres gratuites :

- **Gemini Flash-Lite (gratuit)** : ~1 000 requêtes/jour et des millions de
  tokens/jour. 8 requêtes **par mois** = **< 0,001 %** du quota quotidien.
- **Groq (gratuit)** : plafonds en centaines de milliers de tokens/jour.
  8 000 tokens/mois passent très largement.

Même en écrivant 1 article/jour (≈ 30 000 tokens/mois), tu restes **des ordres
de grandeur** sous les limites gratuites. GitHub Actions : quelques minutes de
build/jour, **gratuit et illimité sur dépôt public**. **Conclusion : 0 €.**

---

## Comment ça marche (résumé)

- **Détection sans IA** : `detect.py` scanne `blog/<slug>/index.html` et calcule
  un hash. Nouveau hash = nouvel article. Rien n'est renvoyé au LLM deux fois.
- **1 appel LLM** → JSON `{bluesky, mastodon, linkedin, reddit_title, reddit_body}`.
  Le code y ajoute liens + 3 hashtags + coupe aux bonnes longueurs.
- **Repli automatique** : si quota dépassé / API en erreur → gabarits sans IA,
  **aucune relance en boucle**.
- **Publication** : Bluesky + Mastodon + Dev.to (canonical vers ton site).
  LinkedIn + Reddit → `drafts.md` à copier-coller.
- **SEO** : régénère `feed.xml`, complète `sitemap.xml` avec les articles,
  notifie Bing/Yandex via IndexNow. (Google = Search Console, déjà vérifié.)
- **Hebdo (lundi)** : post de progression depuis `stats.json` + audit SEO.

---

## 5 bonus SEO 100 % gratuits et sans IA

1. **Google Search Console** — ta balise est déjà en place. Connecte-toi sur
   https://search.google.com/search-console, soumets `sitemap.xml`, et utilise
   « Inspection d'URL → Demander l'indexation » pour chaque nouvel article.
   C'est le vrai canal Google (le ping sitemap a été supprimé en 2023).
2. **Backlinks depuis tes profils** — ajoute `https://yojoxsn.github.io/` dans :
   la bio TryHackMe, le champ *website* de ton profil GitHub, le README de ton
   profil (`github.com/YojoxSn/YojoxSn`), et la bio Bluesky/Mastodon/Dev.to.
   Des liens entrants fiables = meilleur référencement, gratuitement.
3. **Données structurées JSON-LD** — tu as déjà `Person`/`BlogPosting`. Ajoute
   `sameAs` dans le `Person` (tableau de tes URLs TryHackMe/GitHub/Bluesky) :
   Google relie alors tous tes profils à ton identité. Zéro coût, gros signal.
4. **Maillage interne + dates** — depuis chaque writeup, lie 1–2 autres articles
   et la page d'accueil ; garde `lastmod` du sitemap à jour (l'agent le fait).
   Le maillage aide Google à explorer et à comprendre la thématique du site.
5. **Contenu régulier ciblé longue traîne** — publie des writeups avec des
   titres précis (« Writeup TryHackMe <Room> — <technique> »). Ces requêtes de
   niche sont peu concurrentielles : c'est là qu'un petit site gagne vite des
   visites. La régularité (ton atout : série de 190 j) est aussi un signal.
