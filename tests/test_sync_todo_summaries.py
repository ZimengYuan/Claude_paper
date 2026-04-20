from __future__ import annotations

from scripts.sync_todo_summaries import render_todo_summary_markdown


def test_render_todo_summary_markdown_uses_card_sections() -> None:
    card = {
        "title": "Example Paper",
        "core_innovation": "核心创新内容",
        "technical_contributions": [
            {"title": "创新点 1", "body": "贡献 1"},
            {"title": "创新点 2", "body": "贡献 2"},
        ],
        "methodological_breakthrough": {
            "novelty": "新颖性说明",
            "key_technique": "关键技术说明",
            "theory": "理论支撑说明",
        },
        "key_results": {
            "benchmarks": "基准说明",
            "improvements": "提升说明",
            "ablation": "消融说明",
        },
        "limitations": {
            "current": "局限说明",
            "future": "未来方向说明",
            "transferability": "迁移性说明",
        },
        "one_line_summary": "一句话总结",
    }

    markdown = render_todo_summary_markdown(card)

    assert markdown.startswith("# 论文总结：Example Paper")
    assert "## 1. 核心创新点" in markdown
    assert "## 4. 实验验证" in markdown
    assert "- **创新点 1**：贡献 1" in markdown
    assert "- **性能提升**：提升说明" in markdown
    assert markdown.rstrip().endswith("一句话总结")


def test_render_todo_summary_markdown_localizes_common_english_terms() -> None:
    card = {
        "title": "Example Paper",
        "core_innovation": "训练阶段 reference generator 让 tracking policy 更稳定。",
        "technical_contributions": [
            {
                "title": "Human egocentric video → future whole-body motion prediction",
                "body": "robot teleoperation data is reduced while benchmark performance improves.",
            }
        ],
        "methodological_breakthrough": {
            "novelty": "state-dependent tracking with reward shaping",
            "key_technique": "multi-modal robot learning and sim-to-real",
            "theory": "理论支撑说明",
        },
        "key_results": {
            "benchmarks": "two benchmarks",
            "improvements": "better performance than baselines",
            "ablation": "tracking policy ablation",
        },
        "limitations": {
            "current": "teleoperation cost",
            "future": "world model",
            "transferability": "whole-body robots",
        },
        "one_line_summary": "tracking policy for whole-body robots",
    }

    markdown = render_todo_summary_markdown(card)

    assert "人类第一视角视频到未来全身动作预测" in markdown
    assert "跟踪策略" in markdown
    assert "多模态机器人学习" in markdown
    assert "仿真到真实" in markdown
    assert "世界模型" in markdown
