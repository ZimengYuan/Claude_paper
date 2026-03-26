from __future__ import annotations

import json
import sys
from typing import Any, Callable

from scholaraio.config import load_config
from scholaraio.services.common import ServiceError


ActionFn = Callable[[dict[str, Any], Any], Any]


def _require(payload: dict[str, Any], key: str) -> Any:
    value = payload.get(key)
    if value is None:
        raise ServiceError(f'{key} is required', status_code=400)
    return value


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _graph_kwargs(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        'mode': str(payload.get('mode') or 'citation'),
        'scope': str(payload.get('scope') or 'library'),
        'project': str(payload.get('project') or ''),
        'paper_ref': str(payload.get('paper_ref') or payload.get('paper') or ''),
        'min_shared': _as_int(payload.get('min_shared'), 2),
        'max_nodes': _as_int(payload.get('max_nodes'), 80),
    }


def _action_list_papers(payload: dict[str, Any], cfg: Any) -> Any:
    from scholaraio.services.library_service import list_papers

    return list_papers(
        cfg,
        query=str(payload.get('query') or ''),
        show_all=bool(payload.get('show_all')),
        project=str(payload.get('project') or ''),
    )


def _action_list_projects(payload: dict[str, Any], cfg: Any) -> Any:
    from scholaraio.services.project_service import list_projects

    return list_projects(cfg)


def _action_get_paper(payload: dict[str, Any], cfg: Any) -> Any:
    from scholaraio.services.paper_service import get_paper_detail

    return get_paper_detail(cfg, str(_require(payload, 'paper_ref')))


def _action_get_paper_markdown(payload: dict[str, Any], cfg: Any) -> Any:
    from scholaraio.services.paper_service import get_paper_markdown

    return get_paper_markdown(cfg, str(_require(payload, 'paper_ref')))


def _action_set_read_status(payload: dict[str, Any], cfg: Any) -> Any:
    from scholaraio.services.paper_service import update_paper_read_status

    return update_paper_read_status(
        cfg,
        str(_require(payload, 'paper_ref')),
        str(_require(payload, 'status')),
    )


def _action_set_tags(payload: dict[str, Any], cfg: Any) -> Any:
    from scholaraio.services.paper_service import update_paper_tags

    return update_paper_tags(
        cfg,
        str(_require(payload, 'paper_ref')),
        list(payload.get('tags') or []),
    )


def _action_enqueue_generate(payload: dict[str, Any], cfg: Any) -> Any:
    from scholaraio.services.generation_service import enqueue_generation_task

    return enqueue_generation_task(
        cfg,
        str(_require(payload, 'paper_ref')),
        list(payload.get('types') or []),
    )


def _action_enqueue_generate_batch(payload: dict[str, Any], cfg: Any) -> Any:
    from scholaraio.services.generation_service import enqueue_batch_generation_task

    return enqueue_batch_generation_task(
        cfg,
        list(payload.get('paper_refs') or payload.get('paper_ids') or []),
        list(payload.get('types') or []),
    )


def _action_get_graph(payload: dict[str, Any], cfg: Any) -> Any:
    from scholaraio.services.graph_service import get_graph

    return get_graph(cfg, **_graph_kwargs(payload))


def _action_build_graph(payload: dict[str, Any], cfg: Any) -> Any:
    from scholaraio.services.graph_service import build_graph

    return build_graph(cfg, **_graph_kwargs(payload))


def _action_list_tags(payload: dict[str, Any], cfg: Any) -> Any:
    from scholaraio.services.knowledge_service import list_tags

    return list_tags(cfg)


def _action_get_knowledge(payload: dict[str, Any], cfg: Any) -> Any:
    from scholaraio.services.knowledge_service import get_knowledge

    return get_knowledge(cfg)


def _action_append_knowledge(payload: dict[str, Any], cfg: Any) -> Any:
    from scholaraio.services.knowledge_service import add_knowledge_note

    return add_knowledge_note(
        cfg,
        str(_require(payload, 'note')),
        str(payload.get('category') or 'general'),
    )


def _action_append_paper_summary(payload: dict[str, Any], cfg: Any) -> Any:
    from scholaraio.services.knowledge_service import add_paper_summary_note

    return add_paper_summary_note(
        cfg,
        title=str(payload.get('title') or ''),
        summary=str(_require(payload, 'summary')),
        category=str(payload.get('category') or 'paper-summary'),
    )


def _action_search_knowledge(payload: dict[str, Any], cfg: Any) -> Any:
    from scholaraio.services.knowledge_service import search_knowledge_notes

    return search_knowledge_notes(cfg, str(payload.get('query') or ''))


def _action_get_task(payload: dict[str, Any], cfg: Any) -> Any:
    from scholaraio.services.task_service import get_task

    return get_task(str(_require(payload, 'task_id')))


def _load_explore_actions() -> dict[str, ActionFn]:
    try:
        from scholaraio.services.explore_service import (
            generate_explore_roadmap_service,
            get_explore_library,
            list_explore_libraries,
        )
    except ImportError as exc:
        raise ServiceError(f'Explore service unavailable: {exc}', status_code=500) from exc

    return {
        'list_explores': lambda payload, cfg: list_explore_libraries(cfg),
        'get_explore': lambda payload, cfg: get_explore_library(cfg, str(payload.get('name') or 'current-library')),
        'generate_explore_roadmap': lambda payload, cfg: generate_explore_roadmap_service(
            cfg,
            str(payload.get('name') or 'current-library'),
            force=bool(payload.get('force')),
        ),
    }


def _run_explore_action(name: str, payload: dict[str, Any], cfg: Any) -> Any:
    return _load_explore_actions()[name](payload, cfg)


def _action_list_explores(payload: dict[str, Any], cfg: Any) -> Any:
    return _run_explore_action('list_explores', payload, cfg)


def _action_get_explore(payload: dict[str, Any], cfg: Any) -> Any:
    return _run_explore_action('get_explore', payload, cfg)


def _action_generate_explore_roadmap(payload: dict[str, Any], cfg: Any) -> Any:
    return _run_explore_action('generate_explore_roadmap', payload, cfg)


_ACTIONS: dict[str, ActionFn] = {
    'list_papers': _action_list_papers,
    'list_projects': _action_list_projects,
    'get_paper': _action_get_paper,
    'get_paper_markdown': _action_get_paper_markdown,
    'set_read_status': _action_set_read_status,
    'set_tags': _action_set_tags,
    'enqueue_generate': _action_enqueue_generate,
    'enqueue_generate_batch': _action_enqueue_generate_batch,
    'get_graph': _action_get_graph,
    'build_graph': _action_build_graph,
    'list_tags': _action_list_tags,
    'get_knowledge': _action_get_knowledge,
    'append_knowledge': _action_append_knowledge,
    'append_paper_summary': _action_append_paper_summary,
    'search_knowledge': _action_search_knowledge,
    'get_task': _action_get_task,
    'list_explores': _action_list_explores,
    'get_explore': _action_get_explore,
    'generate_explore_roadmap': _action_generate_explore_roadmap,
}


def _read_payload() -> dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ServiceError('payload must be a JSON object', status_code=400)
    return data


def main() -> None:
    if len(sys.argv) < 2:
        sys.stderr.write(json.dumps({'status_code': 400, 'message': 'action is required'}, ensure_ascii=False))
        raise SystemExit(1)

    action = sys.argv[1]
    fn = _ACTIONS.get(action)
    if fn is None:
        sys.stderr.write(json.dumps({'status_code': 400, 'message': f'unknown action: {action}'}, ensure_ascii=False))
        raise SystemExit(1)

    try:
        payload = _read_payload()
        cfg = load_config()
        cfg.ensure_dirs()
        result = fn(payload, cfg)
    except ServiceError as exc:
        sys.stderr.write(json.dumps({'status_code': exc.status_code, 'message': exc.message}, ensure_ascii=False))
        raise SystemExit(1) from exc
    except Exception as exc:
        sys.stderr.write(json.dumps({'status_code': 500, 'message': str(exc)}, ensure_ascii=False))
        raise SystemExit(1) from exc

    sys.stdout.write(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
