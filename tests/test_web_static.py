from __future__ import annotations

import json
import tempfile
from pathlib import Path

from scholaraio import web_static


class _DummyCfg:
    def __init__(self, topics_model_dir: Path) -> None:
        self.topics_model_dir = topics_model_dir


def test_export_static_site_data_preserves_todo_snapshot() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        output_dir = root / "site-data"
        output_dir.mkdir(parents=True, exist_ok=True)
        todo_payload = {
            "version": 1,
            "generated_at": "2026-04-12T00:00:00+00:00",
            "collection": {"key": "RECF7KND", "name": "Todo", "count": 1},
            "cards": [{"route_id": "todo-1", "title": "Example Todo"}],
        }
        (output_dir / "todo-cards.json").write_text(
            json.dumps(todo_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        topics_dir = root / "topic_model"
        topics_dir.mkdir(parents=True, exist_ok=True)
        cfg = _DummyCfg(topics_dir)

        originals = {
            "_build_route_map": web_static._build_route_map,
            "_project_payloads": web_static._project_payloads,
            "list_papers": web_static.list_papers,
            "list_tags": web_static.list_tags,
            "get_knowledge": web_static.get_knowledge,
            "list_explore_libraries": web_static.list_explore_libraries,
            "get_explore_library": web_static.get_explore_library,
            "_safe_graph": web_static._safe_graph,
        }
        try:
            web_static._build_route_map = lambda _cfg: ({}, [])
            web_static._project_payloads = lambda _cfg: ([], {})
            web_static.list_papers = lambda _cfg, show_all=False: []
            web_static.list_tags = lambda _cfg: []
            web_static.get_knowledge = lambda _cfg: ""
            web_static.list_explore_libraries = lambda _cfg: []
            web_static.get_explore_library = lambda _cfg, _name: {}
            web_static._safe_graph = lambda _cfg, *, mode, scope, project="": {}

            result = web_static.export_static_site_data(cfg, output_dir)
        finally:
            for name, value in originals.items():
                setattr(web_static, name, value)

        preserved = json.loads((output_dir / "todo-cards.json").read_text(encoding="utf-8"))
        assert preserved == todo_payload
        assert result["todo_cards"] == 1
