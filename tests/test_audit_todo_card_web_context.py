from scripts.audit_todo_card_web_context import audit_card


def _base_card(**overrides):
    card = {
        "route_id": "paper-1",
        "collection_index": 1,
        "title": "Example Paper",
        "analysis_source": "fulltext",
        "source_confidence": "high",
        "generation_mode": "llm",
        "core_innovation": "提出一个清晰的方法机制。",
        "technical_contributions": [{"title": "模块", "body": "减少训练不稳定性。"}],
        "methodological_breakthrough": {
            "novelty": "不同于直接模仿，本文学习闭环控制。",
            "key_technique": "使用在线参考轨迹和鲁棒训练。",
            "theory": "提供工程分析。",
        },
        "key_results": {
            "benchmarks": "在 12 个 benchmark 上验证。",
            "improvements": "平均误差 2.3 cm。",
            "ablation": "移除关键模块后成功率下降 18%。",
        },
        "limitations": {
            "current": "需要特定传感输入。",
            "future": "可测试更多硬件平台。",
            "transferability": "相近控制任务需要重新验证。",
        },
        "one_line_summary": "值得关注的是闭环训练机制。",
    }
    card.update(overrides)
    return card


def test_metadata_only_card_requires_priority_web_context() -> None:
    finding = audit_card(
        _base_card(
            analysis_source="metadata",
            source_confidence="limited",
            key_results={
                "benchmarks": "摘要未披露具体 benchmark。",
                "improvements": "摘要未披露具体数值。",
                "ablation": "摘要未披露消融。",
            },
        )
    )

    assert finding is not None
    assert finding.priority == 1
    assert "metadata-only or limited source" in finding.reasons


def test_specific_fulltext_card_does_not_require_web_context() -> None:
    assert audit_card(_base_card()) is None


def test_web_supplemented_fulltext_card_is_accepted() -> None:
    assert audit_card(_base_card(analysis_source="fulltext+web")) is None


def test_web_supplemented_metadata_card_is_accepted() -> None:
    assert audit_card(
        _base_card(
            analysis_source="metadata+web",
            source_confidence="medium",
            key_results={
                "benchmarks": "公开项目页确认使用真实机器人平台验证。",
                "improvements": "公开摘要报告比基线更稳定，但没有给出统一百分比。",
                "ablation": "项目页提供组件对照说明。",
            },
        )
    ) is None
