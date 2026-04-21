#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT"

python3 scripts/generate_todo_cards.py \
  --workers 2 \
  --model gpt-5.4 \
  --metadata-model gpt-5.4 \
  --refresh-metadata-only \
  --refresh-fallback-only \
  --timeout 900

python3 scripts/audit_todo_card_web_context.py \
  --output workspace/todo_card_web_context_audit.md

python3 scripts/sync_todo_summaries.py

python3 scripts/generate_todo_compass_materials.py \
  --workers 2 \
  --todo-workers 2 \
  --todo-model gpt-5.4 \
  --score-model fallback \
  --report-model fallback \
  --timeout 900

# Read-only sync check report before publish
python3 scripts/check_snapshot_sync.py

cd "$ROOT/scholaraio/web"
conda run -n node22 npm run generate

cd "$ROOT"
git add \
  scholaraio/web/pages/index.vue \
  scholaraio/web/public/site-data/todo-cards.json \
  scripts/check_snapshot_sync.py \
  scripts/audit_todo_card_web_context.py \
  scripts/generate_todo_cards.py \
  scripts/generate_todo_compass_materials.py \
  scripts/publish_todo_cards.sh \
  scripts/todo_card.schema.json \
  tests/test_todo_compass.py
git commit -m "Add Todo reading cards to library"
git push origin main
