from __future__ import annotations

from scripts.update_learning_memory import ensure_memory_file, upsert_memory_entry
from scholaraio.todo_compass import parse_learning_memory


def test_update_learning_memory_upserts_entries_and_keeps_notes_parseable(tmp_path):
    memory_path = tmp_path / 'memory.md'

    assert ensure_memory_file(memory_path) is True
    assert upsert_memory_entry(memory_path, 'PPO', 'familiar', 'can read examples') is True
    assert upsert_memory_entry(memory_path, 'PPO', 'mastered', 'finished core workflow') is True

    text = memory_path.read_text(encoding='utf-8')

    assert text.count('- PPO:') == 1
    assert '- PPO: mastered  # finished core workflow' in text
    assert text.count('<!-- updated:') == 1
    assert parse_learning_memory(text)['PPO'] == 'mastered'
