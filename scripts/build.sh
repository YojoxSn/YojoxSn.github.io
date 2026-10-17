#!/usr/bin/env sh
# Minifie le CSS et le JS (src/ -> assets/). À lancer après chaque modification de src/.
set -e
cd "$(dirname "$0")/.."
npx --yes esbuild@0.24.0 src/style.css --minify --outfile=assets/css/style.min.css
npx --yes esbuild@0.24.0 src/main.js --minify --target=es2019 --outfile=assets/js/main.min.js
