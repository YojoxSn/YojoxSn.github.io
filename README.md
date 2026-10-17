# yojoxsn.github.io

Site personnel de **Jonas Sleiman** : cybersécurité et pentest, à Orléans.
En ligne sur https://yojoxsn.github.io/ (GitHub Pages).

## Structure

| Chemin | Rôle |
|---|---|
| `index.html` | Accueil : présentation, données structurées `Person` / `ProfilePage` |
| `projets/index.html` | Projets et dépôts GitHub |
| `blog/index.html` | Liste des articles |
| `blog/<slug>/index.html` | Un article (créé à partir de `_modeles/article.html`) |
| `src/style.css`, `src/main.js` | Sources lisibles du CSS et du JS |
| `assets/css/style.min.css`, `assets/js/main.min.js` | Versions minifiées utilisées par le site |
| `assets/img/` | Images (WebP pour le contenu, PNG pour l'image de partage) |
| `robots.txt`, `sitemap.xml` | Indexation |
| `_modeles/` | Modèles d'article et de carte (non publiés) |

## Modifier le style ou le script

Modifier `src/style.css` ou `src/main.js`, puis régénérer les fichiers minifiés :

```sh
./scripts/build.sh
```

## Publier un article

1. Copier `_modeles/article.html` dans `blog/<slug>/index.html` et remplacer les `[[...]]`.
2. Ajouter la carte dans `blog/index.html` (`_modeles/carte-article.html`).
3. Ajouter l'URL dans `sitemap.xml` et mettre à jour `<lastmod>`.
4. Images : les convertir en WebP (`cwebp -q 80 image.png -o image.webp`) et toujours mettre `alt`, `width`, `height`, `loading="lazy"`.
