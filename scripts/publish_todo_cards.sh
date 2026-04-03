#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT"

python3 scripts/generate_todo_cards.py --workers 2 --model gpt-5.4-mini --timeout 900

cd "$ROOT/scholaraio/web"
conda run -n node22 npm run generate

cd "$ROOT"
git add \
  scholaraio/web/pages/index.vue \
  scholaraio/web/public/site-data/todo-cards.json \
  scripts/generate_todo_cards.py \
  scripts/publish_todo_cards.sh \
  scripts/todo_card.schema.json
git commit -m "Add Todo reading cards to library"
git push origin main
