from __future__ import annotations

import json
from pathlib import Path


def _load_todo_cards() -> dict:
    root = Path(__file__).resolve().parents[1]
    fp = root / 'scholaraio' / 'web' / 'public' / 'site-data' / 'todo-cards.json'
    return json.loads(fp.read_text(encoding='utf-8'))


def test_todo_cards_snapshot_count_consistent() -> None:
    payload = _load_todo_cards()
    cards = payload.get('cards') or []
    count = (payload.get('collection') or {}).get('count')

    assert isinstance(cards, list)
    assert count == len(cards)
    assert len(cards) == 168


def test_todo_cards_have_unique_route_and_paper_target() -> None:
    payload = _load_todo_cards()
    cards = payload.get('cards') or []

    route_ids = [str(card.get('route_id') or '').strip() for card in cards]
    assert all(route_ids), 'All cards must have route_id'
    assert len(route_ids) == len(set(route_ids)), 'route_id must be unique'

    # For unmatched todo cards, paper_route_id and DOI may both be empty.
    # In that case, we only require the route to use the unmatched prefix.
    for card in cards:
        route_id = str(card.get('route_id') or '').strip()
        paper_route_id = str(card.get('paper_route_id') or '').strip()
        doi = str(card.get('doi') or '').strip()
        if paper_route_id or doi:
            continue
        assert route_id.startswith('todo-unmatched-'), f"Card {route_id} has neither paper_route_id nor DOI"
