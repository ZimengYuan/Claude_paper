"""Paper Compass helpers for Todo paper scoring and readable reports."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import replace
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from scholaraio.generate import _get_paper_content
from scholaraio.ingest.metadata._api import query_crossref, query_openalex
from scholaraio.metrics import call_llm
from scholaraio.papers import best_citation, read_meta, read_summary, write_meta
from scholaraio.sources.arxiv import search_arxiv


SKILLS_ROOT = Path.home() / ".codex/skills"
SCORE_SKILL_DIR = SKILLS_ROOT / "paper-compass-score"
LEARNPATH_SKILL_DIR = SKILLS_ROOT / "paper-compass-learnpath"
MEMORY_DEFAULT_PATH = Path.home() / "Documents/know/memory.md"
PEER_COUNT = 5

_STOPWORDS = {
    "a", "an", "the", "of", "in", "on", "for", "and", "by", "to", "with", "its", "their", "from",
    "using", "via", "towards", "toward", "through", "into", "under", "over", "that", "this", "these",
}

_SCORE_DIMENSIONS = {
    "发表与 Venue 信号": "publication_signal",
    "作者与机构信号": "author_signal",
    "引用量与引用增速": "citation_traction",
    "被引论文质量": "citation_quality",
    "技术增量与新颖性": "novelty",
    "业界贡献 / 开源 / 产品信号": "industry_signal",
    "奠基潜力 / 方向性影响": "field_shaping",
}

_TOP_VENUE_KEYWORDS = (
    "nature",
    "science robotics",
    "science",
    "nature machine intelligence",
    "neurips",
    "nips",
    "icml",
    "iclr",
    "cvpr",
    "eccv",
    "iccv",
    "rss",
    "conference on robot learning",
    "corl",
    "transactions on robotics",
    "tro",
    "robotics and automation letters",
    "ral",
)

_STRONG_VENUE_KEYWORDS = (
    "icra",
    "iros",
    "aaai",
    "ijcai",
    "acm",
    "ieee",
    "journal",
    "letters",
    "transactions",
    "science advances",
    "nature communications",
)

_INDUSTRY_HINTS = (
    "open source",
    "open-source",
    "code release",
    "github",
    "benchmark",
    "dataset",
    "nvidia",
    "isaac",
    "platform",
    "product",
    "deployment",
    "sim-to-real",
    "sim2real",
)

_CONCEPT_RULES = [
    (("reinforcement learning", "policy", "actor-critic", "off-policy", "on-policy"), "强化学习与策略优化", "论文直接围绕策略更新、样本效率或在线控制展开，先搞懂策略学习目标和更新稳定性。", "⭐⭐⭐", "看懂状态-动作-回报、优势估计和策略更新目标。", "2h", False),
    (("imitation learning", "behavior cloning", "demonstration", "imitation"), "模仿学习与示范数据利用", "如果论文依赖演示数据或偏好反馈，先修模仿学习能帮助理解监督信号从哪里来。", "⭐⭐⭐", "看懂演示数据如何进入训练目标，以及和强化学习如何结合。", "1.5h", False),
    (("diffusion", "denois", "text-to-motion", "motion generation"), "扩散生成与时序动作建模", "扩散式动作生成/运动建模通常是论文的核心建模假设，不补这块很难读懂采样与条件控制。", "⭐⭐⭐⭐", "看懂噪声过程、条件注入和采样推断。", "2.5h", False),
    (("transformer", "autoregressive", "sequence model", "sequence modeling"), "Transformer 与自回归序列建模", "如果论文把控制或动作序列写成 token/序列问题，这部分是最低先修。", "⭐⭐⭐", "看懂序列表示、上下文建模和条件生成。", "2h", False),
    (("world model", "latent dynamics", "dynamics model", "model-based"), "世界模型与动力学建模", "论文若显式建模状态转移、潜变量或规划，就需要先理解模型误差如何影响控制。", "⭐⭐⭐⭐", "看懂状态转移建模、滚动预测和规划接口。", "2.5h", False),
    (("model predictive control", "mpc", "optimal control"), "模型预测控制与最优控制", "涉及 MPC/优化器/残差控制的论文，必须先理解时域优化和约束处理。", "⭐⭐⭐⭐", "看懂滚动优化、代价函数和约束项。", "2.5h", False),
    (("koopman",), "Koopman 表示与系统辨识", "如果论文显式引入 Koopman 或线性化动力学，这块决定你能不能读懂模型结构。", "⭐⭐⭐⭐", "看懂升维表示、线性演化和辨识假设。", "2h", True),
    (("humanoid", "whole-body", "legged", "locomotion"), "全身动力学与接触约束", "做人形/腿式控制时，接触、质心和关节约束是理解实验设置的底层前提。", "⭐⭐⭐", "看懂接触约束、平衡和全身控制目标。", "1.5h", True),
    (("tracking", "retargeting", "pose", "motion"), "轨迹跟踪与运动重定向", "如果论文处理 tracking/retargeting，这块能帮你区分控制器职责和学习器职责。", "⭐⭐⭐", "看懂参考轨迹、误差项和重定向映射。", "1.5h", True),
    (("video", "vision", "egocentric", "image"), "视觉表示与视频条件建模", "当论文从视频或视觉信号学习动作时，需要理解表征如何进入控制/生成模型。", "⭐⭐⭐", "看懂视觉编码、时序特征和条件接口。", "1.5h", True),
    (("force", "contact", "compliance", "wrench"), "力控与接触建模", "涉及力自适应、接触稳定性或柔顺控制时，这部分是实验成败的关键。", "⭐⭐⭐", "看懂力反馈、接触事件和控制增益的作用。", "1.5h", True),
    (("sim-to-real", "domain randomization", "real-world", "deployment"), "Sim-to-Real 与鲁棒性迁移", "如果论文声称现实机器人收益，这部分决定你怎么评估实验外推性。", "⭐⭐⭐", "看懂仿真偏差、随机化和部署假设。", "1.5h", True),
    (("distance field", "pose prior", "neural distance"), "几何先验与距离场建模", "使用距离场或姿态先验的论文，核心难点在几何表示而不是优化器本身。", "⭐⭐⭐⭐", "看懂隐式场表示、距离度量和先验约束。", "2h", True),
]

SCORE_SYSTEM_PROMPT = """你正在执行 paper-compass-score。请严格遵守提供的 rubric、模板和证据约束，只输出最终 Markdown 报告。不要输出代码块，不要补充额外解释；证据不足时明确写信息不足；不要编造 URL、证据或 peer。"""

REPORT_SYSTEM_PROMPT = """你正在执行 paper-compass-learnpath。请严格遵守提供的模板和约束，只输出最终 Markdown 报告。不要输出代码块，不要编造资源链接；没有把握时明确写信息不足。"""


def _clean_doi(value: str | None) -> str:
    text = str(value or "").strip()
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text, flags=re.IGNORECASE)
    return text.lower()


def _norm(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def _slugify(value: str | None, limit: int = 72) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", str(value or "").strip()).strip("-").lower()
    slug = re.sub(r"-+", "-", slug)
    if not slug:
        slug = "untitled"
    return slug[:limit].strip("-") or "untitled"


def _title_keywords(value: str | None, *, max_words: int = 8) -> list[str]:
    words = re.sub(r"[^a-zA-Z0-9\s-]+", " ", str(value or "")).replace("-", " ").split()
    out: list[str] = []
    for word in words:
        lower = word.lower()
        if lower in _STOPWORDS or len(lower) <= 2:
            continue
        out.append(word)
        if len(out) >= max_words:
            break
    return out


def _to_int(value: Any) -> int | None:
    if value in (None, "", False):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _json_copy(payload: Any) -> Any:
    return json.loads(json.dumps(payload, ensure_ascii=False))


def _round_tenth(value: float) -> float:
    return round(float(value) + 1e-8, 1)


def _clamp_score(value: float, max_score: float, min_score: float = 0.0) -> float:
    return _round_tenth(max(min_score, min(max_score, value)))


def _rating_band(score: float) -> str:
    if score >= 9.0:
        return "exceptional; strong evidence of long-term importance, possibly field-shaping"
    if score >= 8.0:
        return "very strong; high-priority reading candidate"
    if score >= 7.0:
        return "solid and worth reading, but not obviously field-defining"
    if score >= 6.0:
        return "selective reading; useful for specific needs"
    return "lower priority unless the user has a narrow reason to read it"


def _reading_priority(score: float) -> str:
    if score >= 7.0:
        return "高"
    if score >= 6.0:
        return "中"
    return "低"


@lru_cache(maxsize=1)
def load_skill_assets() -> dict[str, str]:
    assets = {
        "score_skill": SCORE_SKILL_DIR / "SKILL.md",
        "score_template": SCORE_SKILL_DIR / "references/template.zh.md",
        "score_rubric": SCORE_SKILL_DIR / "references/scoring-rubric.md",
        "learnpath_skill": LEARNPATH_SKILL_DIR / "SKILL.md",
        "learnpath_template": LEARNPATH_SKILL_DIR / "references/template.zh.md",
        "memory_format": LEARNPATH_SKILL_DIR / "references/memory-format.md",
    }
    loaded: dict[str, str] = {}
    for key, path in assets.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing installed skill asset: {path}")
        loaded[key] = path.read_text(encoding="utf-8").strip()
    return loaded


@lru_cache(maxsize=512)
def _cached_query_crossref(doi: str, title: str) -> dict[str, Any]:
    try:
        return _json_copy(query_crossref(doi=doi, title=title))
    except Exception:
        return {}


@lru_cache(maxsize=512)
def _cached_query_openalex(doi: str, title: str) -> dict[str, Any]:
    try:
        return _json_copy(query_openalex(doi=doi, title=title))
    except Exception:
        return {}


@lru_cache(maxsize=512)
def _cached_search_arxiv(query: str, top_k: int) -> list[dict[str, Any]]:
    try:
        return _json_copy(search_arxiv(query, top_k=top_k))
    except Exception:
        return []


def _extract_arxiv_id(meta: dict[str, Any]) -> str:
    doi = _clean_doi(meta.get("doi"))
    match = re.match(r"^10\.48550/arxiv\.(.+)$", doi, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    ids = meta.get("ids") or {}
    if isinstance(ids, dict):
        for key in ("arxiv", "arxiv_id"):
            value = str(ids.get(key) or "").strip()
            if value:
                return value
    title = str(meta.get("title") or "").strip()
    if not title:
        return ""
    for candidate in _cached_search_arxiv(title, 3):
        if _norm(candidate.get("title")) == _norm(title):
            return str(candidate.get("arxiv_id") or "").strip()
    return ""


def _crossref_venue(data: dict[str, Any]) -> str:
    containers = data.get("container-title") or []
    if isinstance(containers, list) and containers:
        return str(containers[0] or "").strip()
    return ""


def _openalex_venue(data: dict[str, Any]) -> str:
    primary = data.get("primary_location") or {}
    source = primary.get("source") or {}
    return str(source.get("display_name") or "").strip()


def resolve_external_metadata(meta: dict[str, Any], paper_dir: Path) -> dict[str, Any]:
    doi = _clean_doi(meta.get("doi"))
    title = str(meta.get("title") or "").strip()
    crossref = _cached_query_crossref(doi, title) if (doi or title) else {}
    openalex = _cached_query_openalex(doi, title) if (doi or title) else {}
    arxiv_id = _extract_arxiv_id(meta)

    venue = _crossref_venue(crossref) or _openalex_venue(openalex) or str(meta.get("journal") or "").strip()
    local_citations = best_citation(meta)
    citation_source = ""
    citation_count = None
    for source, value in (
        ("openalex", _to_int(openalex.get("cited_by_count"))),
        ("local", local_citations if local_citations > 0 else None),
        ("crossref", _to_int(crossref.get("is-referenced-by-count"))),
    ):
        if value is not None:
            citation_source = source
            citation_count = value
            break

    paper_url = str((paper_dir / "paper.md").resolve())
    if arxiv_id:
        paper_url = f"https://arxiv.org/abs/{arxiv_id}"
    elif doi:
        paper_url = f"https://doi.org/{doi}"

    impact_bits: list[str] = []
    if citation_count is not None:
        impact_bits.append(f"citations={citation_count} ({citation_source})")
    else:
        impact_bits.append("citations待验证")
    if venue:
        impact_bits.append(f"venue={venue}")

    openalex_id = str(openalex.get("id") or "").strip()
    return {
        "venue_name": venue or "venue待验证",
        "paper_url": paper_url,
        "citation_count": citation_count,
        "citation_source": citation_source or "unknown",
        "impact_text": " | ".join(impact_bits),
        "openalex_url": openalex_id.replace("https://openalex.org/", "https://openalex.org/works/") if openalex_id else "",
        "crossref_url": f"https://api.crossref.org/works/{doi}" if doi else "",
        "arxiv_id": arxiv_id,
    }


def _comparison_theme(meta: dict[str, Any]) -> str:
    title_words = _title_keywords(meta.get("title"), max_words=6)
    abstract_words = _title_keywords(meta.get("abstract"), max_words=4)
    merged: list[str] = []
    seen: set[str] = set()
    for word in [*title_words, *abstract_words]:
        lower = word.lower()
        if lower in seen:
            continue
        seen.add(lower)
        merged.append(word)
    return " ".join(merged[:8]) or str(meta.get("title") or "")


def _keyword_overlap(a: str, b: str) -> str:
    a_words = {word.lower() for word in _title_keywords(a, max_words=10)}
    b_words = {word.lower() for word in _title_keywords(b, max_words=10)}
    overlap = sorted(a_words & b_words)
    return ", ".join(overlap[:3])


def build_peer_set(meta: dict[str, Any]) -> dict[str, Any]:
    title = str(meta.get("title") or "").strip()
    theme = _comparison_theme(meta)
    current_year = datetime.now().year
    recent_cutoff = current_year - 2
    candidates: dict[str, dict[str, Any]] = {}

    for query in dict.fromkeys([theme, title]):
        if not query:
            continue
        for candidate in _cached_search_arxiv(query, 24):
            peer_title = str(candidate.get("title") or "").strip()
            if not peer_title or _norm(peer_title) == _norm(title):
                continue
            key = str(candidate.get("arxiv_id") or _norm(peer_title))
            if key in candidates:
                continue
            peer_doi = _clean_doi(candidate.get("doi"))
            peer_oa = _cached_query_openalex(peer_doi, peer_title) if (peer_doi or peer_title) else {}
            year = _to_int(candidate.get("year")) or _to_int(peer_oa.get("publication_year")) or 0
            citations = _to_int(peer_oa.get("cited_by_count")) or 0
            venue = _openalex_venue(peer_oa) or "N/A"
            candidates[key] = {
                "title": peer_title,
                "url": f"https://arxiv.org/abs/{candidate.get('arxiv_id')}" if candidate.get("arxiv_id") else "",
                "year": year,
                "venue": venue,
                "citations": citations,
            }

    ranked = sorted(candidates.values(), key=lambda item: (item["citations"], item["year"], item["title"]), reverse=True)
    selected: list[dict[str, Any]] = []
    used: set[str] = set()
    for item in ranked:
        if len(selected) >= PEER_COUNT:
            break
        if _norm(item["title"]) in used:
            continue
        used.add(_norm(item["title"]))
        category = "recent" if item["year"] >= recent_cutoff else "classic"
        overlap = _keyword_overlap(title, item["title"])
        reason = (
            f"近两年与目标论文在 {overlap or '问题设定'} 上最接近的相关工作。"
            if category == "recent"
            else f"该方向较早期的代表性工作，用于校准技术增量与方向延续性（关键词重合：{overlap or '同领域'}）。"
        )
        selected.append({**item, "category": category, "reason": reason})

    recent_count = sum(1 for row in selected if row["category"] == "recent")
    classic_count = sum(1 for row in selected if row["category"] == "classic")
    comparison_status = "complete" if len(selected) == PEER_COUNT and recent_count >= 2 and classic_count >= 1 else "incomplete"
    confidence = "high" if comparison_status == "complete" else "low"
    return {
        "theme": theme,
        "comparison_status": comparison_status,
        "confidence": confidence,
        "peers": selected,
    }


def load_memory_payload(memory_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(memory_path).expanduser() if memory_path else MEMORY_DEFAULT_PATH
    if path.exists():
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        return {"loaded": True, "path": str(path), "content": text}
    return {"loaded": False, "path": str(path), "content": ""}


def build_compass_context(paper_dir: Path, *, memory_path: str | Path | None = None, max_l4_chars: int = 9000) -> dict[str, Any]:
    meta = read_meta(paper_dir)
    content = _get_paper_content(paper_dir, max_l4_chars=max_l4_chars)
    external = resolve_external_metadata(meta, paper_dir)
    peer_pack = build_peer_set(meta)
    memory = load_memory_payload(memory_path)
    outline_lines = [line.strip() for line in str(content.get("l4") or "").splitlines() if line.lstrip().startswith("#")][:20]
    summary = read_summary(paper_dir) or meta.get("summary") or ""

    sources = [external.get("paper_url"), external.get("openalex_url"), external.get("crossref_url")]
    sources.extend(peer.get("url") for peer in peer_pack.get("peers") or [])
    available_sources = [src for idx, src in enumerate(sources) if src and src not in sources[:idx]]

    return {
        "meta": meta,
        "paper_dir": str(paper_dir),
        "content": {
            "l1": content.get("l1") or {},
            "abstract": str(content.get("l2") or "").strip(),
            "conclusion": str(content.get("l3") or "").strip(),
            "fulltext_excerpt": str(content.get("l4") or "").strip(),
            "outline": "\n".join(outline_lines),
            "summary": str(summary).strip(),
        },
        "external": external,
        "peer_pack": peer_pack,
        "memory": memory,
        "available_sources": available_sources,
    }


def _resolve_llm_config(cfg, model: str) -> tuple[Any, str]:
    model_name = (model or "").strip() or cfg.llm.model
    normalized = model_name.lower()
    backend = str(getattr(cfg.llm, "backend", "") or "").lower()
    if normalized.startswith("gpt-") or normalized.startswith(("o1", "o3", "o4")) or "codex" in normalized:
        backend = "codex-mcp"
    elif normalized.startswith("gemini-"):
        backend = "gemini-mcp"
    llm_cfg = replace(cfg.llm, backend=backend, model=model_name)
    api_key = "" if backend in {"gemini-mcp", "codex-mcp"} else cfg.resolved_api_key()
    return llm_cfg, api_key


def _format_peer_lines(peers: list[dict[str, Any]]) -> str:
    lines = []
    for index, peer in enumerate(peers, start=1):
        lines.append(
            f"P{index}: type={peer.get('category')} | title={peer.get('title')} | url={peer.get('url')} | year={peer.get('year')} | venue={peer.get('venue')} | citations={peer.get('citations')} | reason={peer.get('reason')}"
        )
    return "\n".join(lines)


def _score_prompt(context: dict[str, Any]) -> str:
    assets = load_skill_assets()
    meta = context["meta"]
    external = context["external"]
    peer_pack = context["peer_pack"]
    body = context["content"]
    source_lines = "\n".join(f"- {item}" for item in context["available_sources"]) or "- 信息不足"
    target_payload = {
        "title": meta.get("title") or "",
        "authors": meta.get("authors") or [],
        "year": meta.get("year"),
        "doi": meta.get("doi") or "",
        "venue_name": external.get("venue_name") or meta.get("journal") or "venue待验证",
        "paper_url_or_path": external.get("paper_url") or context["paper_dir"],
        "comparison_status": peer_pack.get("comparison_status") or "incomplete",
        "confidence": peer_pack.get("confidence") or "low",
        "impact": external.get("impact_text") or "citations待验证",
    }
    return f"""请根据下面上下文，严格执行已安装的 paper-compass-score 工作流，生成最终 Markdown 报告。

必须满足：
1. 全文使用中文。
2. 必须严格遵循模板的章节标题、顺序和字段。
3. Section 2 的 7 个维度得分必须精确相加得到 Section 1 的总分。
4. 只允许使用我提供的 peer 集合；不要自己再发明 peer。
5. 若 comparison_status=incomplete，则按 rubric 保守打分，总分不得高于 7.4。
6. 证据不足时明确写信息不足，不要臆造证据或 URL。
7. 只输出最终 Markdown，不要代码块，不要额外解释。

模板：
{assets['score_template']}

Rubric：
{assets['score_rubric']}

目标论文：
{json.dumps(target_payload, ensure_ascii=False, indent=2)}

对比集合：
{_format_peer_lines(peer_pack.get('peers') or []) or '信息不足'}

可用来源：
{source_lines}

论文摘要：
{body['abstract'] or '信息不足'}

论文结论：
{body['conclusion'] or '信息不足'}

论文结构大纲：
{body['outline'] or '信息不足'}

论文全文摘录：
{body['fulltext_excerpt'] or '信息不足'}
"""


def _report_prompt(context: dict[str, Any], score_report: str) -> str:
    assets = load_skill_assets()
    meta = context["meta"]
    external = context["external"]
    body = context["content"]
    memory = context["memory"]
    peer_pack = context["peer_pack"]
    source_lines = "\n".join(f"- {item}" for item in context["available_sources"]) or "- 信息不足"
    memory_block = memory["content"] if memory.get("loaded") else f"memory 未加载；默认路径 {memory.get('path')} 不存在。"
    target_payload = {
        "title": meta.get("title") or "",
        "authors": meta.get("authors") or [],
        "year": meta.get("year"),
        "venue_name": external.get("venue_name") or meta.get("journal") or "venue待验证",
        "paper_url_or_path": external.get("paper_url") or context["paper_dir"],
        "impact": external.get("impact_text") or "citations待验证",
        "comparison_theme": peer_pack.get("theme") or "",
    }
    return f"""请根据下面上下文，严格执行已安装的 paper-compass-learnpath 工作流，生成一份中文、可直接阅读的 report.md。

必须满足：
1. 严格按照模板章节输出。
2. 必学先修只保留真正理解本文所必需的概念，并尽量按依赖顺序排序。
3. 每个 must/bridge 概念都尽量给出 [Section] \"quote\" 证据；没有把握时写信息不足。
4. Section 4 的资源只能使用我提供的候选链接；没有合适资源就写信息不足，不要编造 URL。
5. Section 6 只能写关键实验结论: ...。
6. 只输出最终 Markdown，不要代码块，不要额外解释。

模板：
{assets['learnpath_template']}

memory 格式提示：
{assets['memory_format']}

目标论文：
{json.dumps(target_payload, ensure_ascii=False, indent=2)}

memory 内容：
{memory_block}

可用资源候选：
{source_lines}

已有评分报告：
{score_report or '信息不足'}

已有摘要：
{body['summary'] or '信息不足'}

论文摘要：
{body['abstract'] or '信息不足'}

论文结论：
{body['conclusion'] or '信息不足'}

论文结构大纲：
{body['outline'] or '信息不足'}

论文全文摘录：
{body['fulltext_excerpt'] or '信息不足'}
"""


def _text_sources(context: dict[str, Any]) -> list[tuple[str, str]]:
    body = context["content"]
    return [
        ("Summary", str(body.get("summary") or "").strip()),
        ("Abstract", str(body.get("abstract") or "").strip()),
        ("Conclusion", str(body.get("conclusion") or "").strip()),
        ("Fulltext", str(body.get("fulltext_excerpt") or "").strip()),
    ]


def _sentence_candidates(text: str, *, max_sentences: int = 12) -> list[str]:
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
    if not cleaned:
        return []
    parts = re.split(r"(?<=[。！？.!?])\s+", cleaned)
    return [part.strip().strip("-•") for part in parts if len(part.strip()) >= 20][:max_sentences]


def _evidence_quote(context: dict[str, Any], keywords: tuple[str, ...] = (), *, fallback: str = "信息不足") -> str:
    lowered = tuple(keyword.lower() for keyword in keywords if keyword)
    for label, text in _text_sources(context):
        for sentence in _sentence_candidates(text, max_sentences=18):
            lower = sentence.lower()
            if lowered and not any(keyword in lower for keyword in lowered):
                continue
            snippet = sentence[:180] + ("..." if len(sentence) > 180 else "")
            return f'[{label}] "{snippet}"'
    return fallback


def _context_blob(context: dict[str, Any]) -> str:
    meta = context["meta"]
    body = context["content"]
    return "\n".join(
        [
            str(meta.get("title") or ""),
            str(body.get("summary") or ""),
            str(body.get("abstract") or ""),
            str(body.get("conclusion") or ""),
            str(body.get("outline") or ""),
        ]
    ).lower()


def _format_score(value: float) -> str:
    return f"{_round_tenth(value):.1f}"


def _months_since(meta: dict[str, Any]) -> int:
    year = _to_int(meta.get("year"))
    if year is None:
        return 24
    return max((datetime.now().year - year) * 12 + 6, 6)


def _publication_score(context: dict[str, Any]) -> tuple[float, str, str]:
    meta = context["meta"]
    external = context["external"]
    venue = str(external.get("venue_name") or meta.get("journal") or "").strip()
    lower = venue.lower()
    if any(keyword in lower for keyword in _TOP_VENUE_KEYWORDS):
        score = 1.5
        why = "发表 venue 明确且属于领域旗舰信号，基础可信度和可见度都较高。"
    elif any(keyword in lower for keyword in _STRONG_VENUE_KEYWORDS):
        score = 1.2
        why = "venue 已明确且强度不错，但还不到最顶级的 field-defining 信号。"
    elif "arxiv" in lower or external.get("arxiv_id"):
        score = 0.6
        why = "当前主要仍是 arXiv / preprint 信号，发表强度需要保守看待。"
    elif venue:
        score = 0.9
        why = "有明确发表去向，但缺少更强的顶级 venue 佐证。"
    else:
        score = 0.3
        why = "发表 venue 信息不足，只能给保守分。"
    evidence = f"[Meta] venue={venue or '信息不足'} | source={external.get('paper_url') or context['paper_dir']}"
    return _clamp_score(score, 1.5), why, evidence


def _author_score(context: dict[str, Any], publication_score: float) -> tuple[float, str, str]:
    meta = context["meta"]
    authors = list(meta.get("authors") or [])
    citation_count = context["external"].get("citation_count") or best_citation(meta)
    if not authors:
        score = 0.2
        why = "作者信息不完整，无法验证稳定的作者/机构信号。"
    elif len(authors) >= 4 or publication_score >= 1.2:
        score = 0.8
        why = "作者列表完整且与强 venue 共同出现，说明团队具备较稳的执行力与领域进入门槛。"
    elif len(authors) >= 2:
        score = 0.6
        why = "有基本的协作团队形态，但缺少更强的历史 track record 证据。"
    else:
        score = 0.4
        why = "只有有限作者信号，暂时不足以支撑更高评分。"
    if citation_count and citation_count >= 100:
        score += 0.2
    evidence = f"[Meta] authors={', '.join(authors[:6]) if authors else '信息不足'}"
    return _clamp_score(score, 1.0), why, evidence


def _citation_traction_score(context: dict[str, Any]) -> tuple[float, str, str]:
    meta = context["meta"]
    citation_count = context["external"].get("citation_count")
    months = _months_since(meta)
    if citation_count is None:
        return 0.3, "缺少稳定的引用计数来源，只能按信息不足处理。", "信息不足"

    velocity = citation_count / months if months else citation_count
    if velocity >= 8 or citation_count >= 200:
        score, bucket = 2.0, "top band"
    elif velocity >= 4 or citation_count >= 100:
        score, bucket = 1.7, "strong upper band"
    elif velocity >= 2 or citation_count >= 40:
        score, bucket = 1.4, "above median"
    elif velocity >= 1 or citation_count >= 15:
        score, bucket = 1.1, "around median"
    elif citation_count > 0:
        score, bucket = 0.8, "below median"
    else:
        score, bucket = (0.5 if months <= 12 else 0.3), "very early or weak"
    why = f"按发表年限归一后，引用速度大致落在 {bucket}，能说明这篇工作已有一定外部关注度。"
    evidence = f"[API] citations={citation_count} | months_since_release≈{months}"
    return _clamp_score(score, 2.0), why, evidence


def _citation_quality_score(context: dict[str, Any], citation_traction: float) -> tuple[float, str, str]:
    meta = context["meta"]
    citation_count = context["external"].get("citation_count")
    months = _months_since(meta)
    if citation_count is None:
        score, why, evidence = 0.3, "没有可验证的 citing-paper 样本，无法给出更高的外部采纳质量分。", "信息不足"
    elif months <= 12 and citation_count < 5:
        score, why, evidence = 0.7, "论文还比较新，先给一个中性保守分，避免因为时间短被过度惩罚。", f"[API] recent paper | citations={citation_count}"
    elif citation_count >= 150:
        score, why, evidence = 1.2, "总引用量已经足够高，通常意味着后续跟进论文质量不会太弱。", f"[API] citations={citation_count}"
    elif citation_count >= 40:
        score, why, evidence = 0.9, "能看到一定规模的外部跟进，但距离强 follow-up 生态还差一层。", f"[API] citations={citation_count}"
    elif citation_count > 0:
        score, why, evidence = 0.6, "已有外部引用，但还不足以证明后续引用论文整体质量很强。", f"[API] citations={citation_count}"
    else:
        score, why, evidence = 0.3, "还没有形成清晰的外部跟进证据。", f"[API] citations={citation_count}"
    if citation_traction >= 1.7 and citation_count and citation_count >= 100:
        score += 0.1
    return _clamp_score(score, 1.5), why, evidence


def _novelty_score(context: dict[str, Any]) -> tuple[float, str, str]:
    meta = context["meta"]
    body = context["content"]
    blob = _context_blob(context)
    strong_markers = (
        "unified", "foundation", "benchmark", "world model", "diffusion", "omnicontrol",
        "zero-shot", "one-step", "residual", "pretraining", "distance field", "any joint", "generalist", "scaling",
    )
    moderate_markers = (
        "efficient", "stable", "fast", "imitation", "controller gains", "tracking", "retargeting", "policy optimization",
    )
    strong_hits = sum(1 for marker in strong_markers if marker in blob)
    moderate_hits = sum(1 for marker in moderate_markers if marker in blob)
    summary_len = len(str(body.get("summary") or ""))
    if strong_hits >= 3:
        score, why = 1.6, "从标题与 summary 看，论文更像是在方法范式或任务接口上做了显式重构，而不是局部调参。"
    elif strong_hits >= 1 or moderate_hits >= 3:
        score, why = 1.4, "技术增量清楚可见，既有方法名义上的新部件，也有任务层面的重新组织。"
    elif summary_len >= 1800:
        score, why = 1.2, "虽然未必是新范式，但 summary 能支撑它不是简单复述已有方法。"
    elif str(meta.get("paper_type") or "") == "todo-placeholder":
        score, why = 0.8, "当前只有 metadata/摘要级证据，先按保守的 bounded improvement 打分。"
    else:
        score, why = 1.0, "可以确认存在方法差异，但尚不足以判断为强范式迁移。"
    evidence = _evidence_quote(context, strong_markers + moderate_markers, fallback=_evidence_quote(context))
    return _clamp_score(score, 2.0), why, evidence


def _industry_score(context: dict[str, Any]) -> tuple[float, str, str]:
    blob = _context_blob(context)
    hits = [keyword for keyword in _INDUSTRY_HINTS if keyword in blob]
    robotics_hint = any(keyword in blob for keyword in ("robot", "humanoid", "sim-to-real", "deployment", "real-world"))
    if len(hits) >= 3:
        score, why = 0.8, "能看到 benchmark / 开源 / 平台化等多个外部生态信号，说明不只是论文内循环。"
    elif hits:
        score, why = 0.5, "有可信的生态或工程外溢信号，但尚不足以视为大规模外部采用。"
    elif robotics_hint:
        score, why = 0.2, "问题本身偏工程落地，但目前缺少已验证的开源或产品化证据。"
    else:
        score, why = 0.0, "没有看到明确的行业或开源外溢信号。"
    evidence = _evidence_quote(context, tuple(hits) if hits else ("benchmark", "open", "deployment", "real-world"))
    return _clamp_score(score, 1.0), why, evidence


def _field_shaping_score(publication_score: float, citation_traction: float, citation_quality: float, novelty: float, industry: float) -> tuple[float, str, str]:
    strong_signals = 0
    if publication_score >= 1.2:
        strong_signals += 1
    if citation_traction >= 1.4:
        strong_signals += 1
    if citation_quality >= 1.0:
        strong_signals += 1
    if novelty >= 1.4:
        strong_signals += 1
    if industry >= 0.5:
        strong_signals += 1
    if strong_signals >= 4:
        score, why = 0.8, "已经出现多个方向性信号，但距离真正的 field-defining 还差跨团队复用或更长时间验证。"
    elif strong_signals >= 2:
        score, why = 0.5, "论文有成为方向锚点的潜力，但证据更像 early promise，而不是已形成共识。"
    elif strong_signals >= 1:
        score, why = 0.2, "能看到一点方向性火花，但还谈不上明显 shaping the field。"
    else:
        score, why = 0.0, "目前没有足够证据支持更高的方向影响判断。"
    evidence = f"[Composite] publication={publication_score:.1f}; traction={citation_traction:.1f}; novelty={novelty:.1f}; industry={industry:.1f}"
    return _clamp_score(score, 1.0), why, evidence


def _cap_scores_for_incomplete_comparison(scores: dict[str, float], comparison_status: str) -> dict[str, float]:
    if comparison_status == "complete":
        return scores
    total = _round_tenth(sum(scores.values()))
    if total <= 7.4:
        return scores
    excess = _round_tenth(total - 7.4)
    floors = {
        "field_shaping": 0.2,
        "industry_signal": 0.2,
        "novelty": 1.0,
        "citation_quality": 0.6,
        "author_signal": 0.4,
        "citation_traction": 0.8,
    }
    for key in ("field_shaping", "industry_signal", "novelty", "citation_quality", "author_signal", "citation_traction"):
        while excess > 0 and scores[key] > floors[key]:
            scores[key] = _round_tenth(scores[key] - 0.1)
            excess = _round_tenth(excess - 0.1)
    return scores


def _fill_peer_rows(peer_pack: dict[str, Any]) -> list[dict[str, str]]:
    peers = list(peer_pack.get("peers") or [])
    rows: list[dict[str, str]] = []
    for index in range(PEER_COUNT):
        if index < len(peers):
            peer = peers[index]
            rows.append({
                "type": str(peer.get("category") or "信息不足"),
                "title": str(peer.get("title") or "信息不足"),
                "url": str(peer.get("url") or "信息不足"),
                "year": str(peer.get("year") or "N/A"),
                "venue": str(peer.get("venue") or "N/A"),
                "citations": str(peer.get("citations") or 0),
                "reason": str(peer.get("reason") or "信息不足"),
            })
        else:
            rows.append({
                "type": "信息不足",
                "title": "信息不足",
                "url": "信息不足",
                "year": "N/A",
                "venue": "N/A",
                "citations": "0",
                "reason": "当前没有足够的 peer 候选。",
            })
    return rows


def _source_list(context: dict[str, Any], *, limit: int = 3) -> list[str]:
    sources = []
    for source in context.get("available_sources") or []:
        if source and source not in sources:
            sources.append(source)
        if len(sources) >= limit:
            break
    while len(sources) < limit:
        sources.append("信息不足")
    return sources[:limit]


def _score_change_triggers(context: dict[str, Any]) -> str:
    external = context["external"]
    triggers = []
    if not external.get("citation_count"):
        triggers.append("拿到稳定的引用计数与随时间增长情况")
    if external.get("venue_name") in {"", "venue待验证"}:
        triggers.append("确认正式发表 venue 与是否有 distinction")
    if not any("github" in source.lower() for source in context.get("available_sources") or []):
        triggers.append("看到明确的开源、benchmark 采用或部署证据")
    return "；".join(triggers[:3]) or "如果后续出现跨团队复用、强 follow-up 或生态采用，分数还会上调。"


def _fallback_score_report(context: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    meta = context["meta"]
    external = context["external"]
    peer_pack = context["peer_pack"]
    publication, why_publication, evidence_publication = _publication_score(context)
    author, why_author, evidence_author = _author_score(context, publication)
    citation_traction, why_citation_traction, evidence_citation_traction = _citation_traction_score(context)
    citation_quality, why_citation_quality, evidence_citation_quality = _citation_quality_score(context, citation_traction)
    novelty, why_novelty, evidence_novelty = _novelty_score(context)
    industry, why_industry, evidence_industry = _industry_score(context)
    field_shaping, why_field_shaping, evidence_field_shaping = _field_shaping_score(publication, citation_traction, citation_quality, novelty, industry)

    scores = {
        "publication_signal": publication,
        "author_signal": author,
        "citation_traction": citation_traction,
        "citation_quality": citation_quality,
        "novelty": novelty,
        "industry_signal": industry,
        "field_shaping": field_shaping,
    }
    scores = _cap_scores_for_incomplete_comparison(scores, peer_pack.get("comparison_status") or "incomplete")
    final_score = _round_tenth(sum(scores.values()))
    rating_band = _rating_band(final_score)
    priority = _reading_priority(final_score)
    field_statement = (
        "multiple strong signals, likely direction-setting" if scores["field_shaping"] >= 0.8 else
        "early promise, not yet established" if scores["field_shaping"] >= 0.5 else
        "weak field-shaping evidence so far"
    )
    one_line_verdict = (
        "技术增量明确、值得优先扫读。" if final_score >= 8.0 else
        "整体扎实，值得进入 Todo 的前排阅读。" if final_score >= 7.0 else
        "更适合带着具体问题去读。" if final_score >= 6.0 else
        "除非你正好需要这条技术线，否则优先级不高。"
    )

    peer_rows = _fill_peer_rows(peer_pack)
    stronger_points = "方法 framing 更完整，且 summary 能支持它不是单点 trick。" if scores["novelty"] >= 1.4 else "当前看不出明显强于 peer 的一整档优势。"
    parity_points = "问题设定与实验组织和同主题 peer 大致处在同一工作带宽。"
    weaker_points = "peer 对比集合还不完整；若后续没有更强 follow-up 或生态采用，方向影响分会继续保守。"
    upside_drivers = "；".join([
        why_publication,
        why_novelty,
        why_citation_traction if scores["citation_traction"] >= 1.1 else "引用牵引目前仍偏保守",
    ])
    downside_items = []
    if (peer_pack.get("comparison_status") or "") != "complete":
        downside_items.append("peer 对比仍不完整，需要保守评分")
    if scores["citation_quality"] <= 0.9:
        downside_items.append("缺少更强 citing-paper 质量证据")
    if scores["industry_signal"] <= 0.5:
        downside_items.append("业界/开源外溢信号有限")
    downside_drivers = "；".join(downside_items) or "当前没有明显结构性短板，但也还没到显著 field-defining。"
    reading_decision = "值得优先读，尤其适合快速建立该方向当前方法边界。" if final_score >= 7.0 else "建议带着明确问题去读，而不是无目标通读。"
    best_fit_readers = "做人形/机器人控制、生成式动作建模、策略学习或相关 benchmark 复现的人。"
    not_best_fit_readers = "只想看已被社区完全证明的奠基论文，或者暂时不关心该任务线的人。"
    sources = _source_list(context)

    report = f"""# 论文价值分析报告

## 0. 论文快照

- 标题: {meta.get('title') or ''}
- 作者: {', '.join(meta.get('authors') or [])}
- 年份: {meta.get('year') or 'N/A'}
- 发表信息与 Venue: {external.get('venue_name') or meta.get('journal') or 'venue待验证'}
- 来源: {external.get('paper_url') or context['paper_dir']}
- 对比集合状态: {peer_pack.get('comparison_status') or 'incomplete'}
- 评分置信度: {peer_pack.get('confidence') or 'low'}

## 1. 最终结论

- 总分: {_format_score(final_score)}/10.0
- 等级: {rating_band}
- 阅读优先级: {priority}
- 奠基潜力判断: {field_statement}
- 一句话判断: {one_line_verdict}

## 2. 分项评分

| 维度 | 满分 | 得分 | 评分依据 | 关键证据 |
|---|---:|---:|---|---|
| 发表与 Venue 信号 | 1.5 | {_format_score(scores['publication_signal'])} | {why_publication} | {evidence_publication} |
| 作者与机构信号 | 1.0 | {_format_score(scores['author_signal'])} | {why_author} | {evidence_author} |
| 引用量与引用增速 | 2.0 | {_format_score(scores['citation_traction'])} | {why_citation_traction} | {evidence_citation_traction} |
| 被引论文质量 | 1.5 | {_format_score(scores['citation_quality'])} | {why_citation_quality} | {evidence_citation_quality} |
| 技术增量与新颖性 | 2.0 | {_format_score(scores['novelty'])} | {why_novelty} | {evidence_novelty} |
| 业界贡献 / 开源 / 产品信号 | 1.0 | {_format_score(scores['industry_signal'])} | {why_industry} | {evidence_industry} |
| 奠基潜力 / 方向性影响 | 1.0 | {_format_score(scores['field_shaping'])} | {why_field_shaping} | {evidence_field_shaping} |

## 3. 相似论文对比集合（5 篇）

| Peer | 类别 | 论文 | arXiv | 年份 | Venue | 引用量 | 选入理由 |
|---|---|---|---|---:|---|---:|---|
| P1 | {peer_rows[0]['type']} | {peer_rows[0]['title']} | {peer_rows[0]['url']} | {peer_rows[0]['year']} | {peer_rows[0]['venue']} | {peer_rows[0]['citations']} | {peer_rows[0]['reason']} |
| P2 | {peer_rows[1]['type']} | {peer_rows[1]['title']} | {peer_rows[1]['url']} | {peer_rows[1]['year']} | {peer_rows[1]['venue']} | {peer_rows[1]['citations']} | {peer_rows[1]['reason']} |
| P3 | {peer_rows[2]['type']} | {peer_rows[2]['title']} | {peer_rows[2]['url']} | {peer_rows[2]['year']} | {peer_rows[2]['venue']} | {peer_rows[2]['citations']} | {peer_rows[2]['reason']} |
| P4 | {peer_rows[3]['type']} | {peer_rows[3]['title']} | {peer_rows[3]['url']} | {peer_rows[3]['year']} | {peer_rows[3]['venue']} | {peer_rows[3]['citations']} | {peer_rows[3]['reason']} |
| P5 | {peer_rows[4]['type']} | {peer_rows[4]['title']} | {peer_rows[4]['url']} | {peer_rows[4]['year']} | {peer_rows[4]['venue']} | {peer_rows[4]['citations']} | {peer_rows[4]['reason']} |

## 4. 横向对比观察

- 明显强于 peer 的点: {stronger_points}
- 与 peer 大体持平的点: {parity_points}
- 明显落后于 peer 的点: {weaker_points}

## 5. 分数形成原因

- 主要加分项: {upside_drivers}
- 主要扣分项: {downside_drivers}
- 哪些新增证据会改变评分: {_score_change_triggers(context)}

## 6. 是否值得优先读

- 结论: {reading_decision}
- 适合优先阅读的人: {best_fit_readers}
- 不适合优先阅读的人: {not_best_fit_readers}

## 7. **Sources**:

- {sources[0]}
- {sources[1]}
- {sources[2]}
"""

    rating = {
        "scheme": "paper_compass_score",
        **scores,
        "overall_score": final_score,
        "rating_band": rating_band,
        "priority": priority,
        "field_shaping_statement": field_statement,
        "one_line_verdict": one_line_verdict,
        "notes": one_line_verdict,
    }
    return report.strip() + "\n", rating


def _candidate_concepts(context: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    blob = _context_blob(context)
    selected: list[dict[str, str]] = []
    for patterns, concept, why, difficulty, goal, eta, is_bridge in _CONCEPT_RULES:
        if not any(pattern in blob for pattern in patterns):
            continue
        selected.append({
            "concept": concept,
            "why": why,
            "section": "[Summary/Abstract] 与论文主线直接相关",
            "evidence": _evidence_quote(context, patterns),
            "difficulty": difficulty,
            "goal": goal,
            "time": eta,
            "role": "bridge" if is_bridge else "must",
            "action": "review" if is_bridge else "learn",
        })
    if not selected:
        selected = [
            {
                "concept": "任务设定与评价协议",
                "why": "先理解论文到底优化什么、在哪些基准上比较，才能正确读实验。",
                "section": "[Summary] 任务与实验设置",
                "evidence": _evidence_quote(context),
                "difficulty": "⭐⭐",
                "goal": "看懂任务输入输出、评价指标和 baseline 选择。",
                "time": "1h",
                "role": "must",
                "action": "learn",
            },
            {
                "concept": "模型结构与训练目标",
                "why": "即使没有全文，也至少要明确模型模块、损失项或奖励结构。",
                "section": "[Summary] 核心方法",
                "evidence": _evidence_quote(context),
                "difficulty": "⭐⭐⭐",
                "goal": "看懂模型组成、目标函数和关键超参。",
                "time": "1.5h",
                "role": "must",
                "action": "learn",
            },
        ]
    must = [row for row in selected if row["role"] == "must"][:4]
    bridge = [row for row in selected if row["role"] == "bridge"][:3]
    if not bridge:
        bridge = [{
            "concept": "相关 benchmark / 仿真平台背景",
            "why": "补这块能更快判断实验是否真的有外推价值。",
            "section": "[Summary] 实验部分",
            "evidence": _evidence_quote(context, ("benchmark", "sim", "robot", "experiment")),
            "difficulty": "⭐⭐",
            "goal": "知道实验平台、评价指标和现实约束。",
            "time": "45m",
            "role": "bridge",
            "action": "review",
        }]
    return must, bridge


def _memory_delta(context: dict[str, Any], must_rows: list[dict[str, str]]) -> tuple[list[str], list[str], list[str]]:
    memory = context.get("memory") or {}
    content = str(memory.get("content") or "").lower()
    if not memory.get("loaded") or not content:
        retained = [f"{must_rows[0]['concept']}：即使已有相近背景，也建议按本文的问题设定重新对齐。"] if must_rows else []
        return [], retained, [row["concept"] for row in must_rows[:2]]

    skipped: list[str] = []
    retained: list[str] = []
    new_gaps: list[str] = []
    for row in must_rows:
        tokens = [token.lower() for token in re.split(r"[^a-zA-Z0-9\u4e00-\u9fff]+", row["concept"]) if token]
        if any(token in content for token in tokens[:3]):
            skipped.append(row["concept"])
            retained.append(f"{row['concept']}：memory 里有相近背景，但本文用法更贴近 {context['meta'].get('title') or '当前论文'}。")
        else:
            new_gaps.append(row["concept"])
    return skipped[:2], retained[:2], new_gaps[:3]


def _quickstart_summary(context: dict[str, Any]) -> str:
    sentences: list[str] = []
    for _, text in _text_sources(context):
        sentences.extend(_sentence_candidates(text, max_sentences=4))
    if not sentences:
        return "先读摘要与 summary，确认论文到底优化了什么，再检查实验是否真的支持这个 claim。"
    selected: list[str] = []
    for sentence in sentences:
        if sentence not in selected:
            selected.append(sentence)
        if len(selected) >= 2:
            break
    return " ".join(selected[:2])


def _fallback_readable_report(context: dict[str, Any], score_report: str) -> str:
    meta = context["meta"]
    external = context["external"]
    must_rows, bridge_rows = _candidate_concepts(context)
    skipped, retained, new_gaps = _memory_delta(context, must_rows)
    sources = _source_list(context, limit=5)
    paper_url = external.get("paper_url") or context["paper_dir"]
    impact = external.get("impact_text") or "影响力信息不足"

    must_table = [
        f"| {index} | {row['concept']} | {row['why']} | {row['section']} | {row['evidence']} | {row['difficulty']} | {row['goal']} | {row['time']} |"
        for index, row in enumerate(must_rows, start=1)
    ]
    bridge_table = [
        f"| {row['concept']} | bridge | {row['section']} | {row['evidence']} | {row['difficulty']} | {row['action']} |"
        for row in bridge_rows
    ]

    peer_links = [peer.get("url") for peer in context.get("peer_pack", {}).get("peers", []) if peer.get("url")]
    resource_sections: list[str] = []
    for index, row in enumerate(must_rows[:2], start=1):
        review_link = peer_links[index - 1] if index - 1 < len(peer_links) else sources[min(index, len(sources) - 1)]
        resource_sections.append(
            "\n".join([
                f"### {row['concept']}",
                "",
                "- 原论文/综述:",
                f"  - {meta.get('title') or '目标论文'} - {paper_url}",
                f"  - 同主题 peer - {review_link or '信息不足'}",
                "- 视频（优先高质量，lang=zh 时可含中文社区）:",
                f"  - 信息不足 - {review_link or paper_url}",
                "- 说明:",
                "  - 先用目标论文建立术语，再用 peer 校准它在相邻方法中的位置。",
            ])
        )

    stage_a = "、".join(row["concept"] for row in must_rows[:2]) or "任务设定"
    stage_b = "、".join(row["concept"] for row in bridge_rows[:2]) or "实验协议"
    stage_c = "、".join(row["concept"] for row in must_rows[2:4]) or (must_rows[-1]["concept"] if must_rows else "论文特有机制")

    skipped_lines = "\n".join(f"  - {item}" for item in skipped) or "  - 暂无明确已掌握项，按默认先修序列处理。"
    retained_lines = "\n".join(f"  - {item}" for item in retained) or "  - 暂无，需要跟着论文语境重新过一遍核心术语。"
    gap_lines = "\n".join(f"  - {item}" for item in new_gaps) or "  - 当前最缺的是把任务设定、方法结构和实验协议对齐起来。"
    all_sources = [paper_url] + [src for src in sources if src != paper_url]
    source_lines = "\n".join(f"- {source}" for source in all_sources[:3])

    report = f"""# 论文先修罗盘报告模板

## 0. 论文快照

- 标题: {meta.get('title') or ''}
- 作者: {', '.join(meta.get('authors') or [])}
- 年份: {meta.get('year') or 'N/A'}
- 发表信息与venue: {external.get('venue_name') or meta.get('journal') or 'venue待验证'} | JCR 分区: N/A | CCF 等级: N/A
- 来源: {paper_url}
- **影响力**: {impact}

## 1. 必学先修知识（按顺序）

| 顺序 | 知识点 | 为什么必学 | 论文使用位置 | 证据锚点 | 难度 | 最小学习目标 | 预计时间 |
|---|---|---|---|---|---|---|---|
{chr(10).join(must_table)}

## 2. 桥接知识（可选但有帮助）

| 知识点 | 角色 | 论文使用位置 | 证据 | 难度 | 建议动作 |
|---|---|---|---|---|---|
{chr(10).join(bridge_table)}

## 3. 个性化增量（基于 memory.md）

- 已跳过（已掌握）:
{skipped_lines}
- 虽然熟悉但仍保留（论文特有增量）:
{retained_lines}
- 新出现的高优先级短板:
{gap_lines}

## 4. 推荐学习资源

{chr(10).join(resource_sections) if resource_sections else '信息不足'}

## 5. 建议学习顺序

1. 阶段 A（基础）: {stage_a}
2. 阶段 B（机制桥接）: {stage_b}
3. 阶段 C（论文特有）: {stage_c}

## 6. 30 分钟快速起步

关键实验结论: {_quickstart_summary(context)}

## 7. **Sources**:

{source_lines}
"""
    return report.strip() + "\n"


def _run_markdown_model(prompt: str, cfg, *, model: str, timeout: int, system: str, purpose: str) -> str:
    llm_cfg, api_key = _resolve_llm_config(cfg, model)
    result = call_llm(
        prompt=prompt,
        config=llm_cfg,
        api_key=api_key,
        system=system,
        json_mode=False,
        max_tokens=5000,
        timeout=timeout,
        purpose=purpose,
    )
    return result.content.strip()


def parse_compass_score_report(markdown: str) -> dict[str, Any]:
    rating: dict[str, Any] = {"scheme": "paper_compass_score"}
    for raw_line in str(markdown or "").splitlines():
        line = raw_line.strip()
        if line.startswith("- 总分:"):
            match = re.search(r"([0-9]+(?:\.[0-9])?)\s*/\s*10", line)
            if match:
                rating["overall_score"] = float(match.group(1))
        elif line.startswith("- 等级:"):
            rating["rating_band"] = line.split(":", 1)[1].strip()
        elif line.startswith("- 阅读优先级:"):
            rating["priority"] = line.split(":", 1)[1].strip()
        elif line.startswith("- 奠基潜力判断:"):
            rating["field_shaping_statement"] = line.split(":", 1)[1].strip()
        elif line.startswith("- 一句话判断:"):
            rating["one_line_verdict"] = line.split(":", 1)[1].strip()
        elif line.startswith("|"):
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if len(cells) < 5:
                continue
            key = _SCORE_DIMENSIONS.get(cells[0])
            if not key:
                continue
            try:
                rating[key] = float(cells[2])
            except ValueError:
                continue
    total = 0.0
    found = 0
    for key in _SCORE_DIMENSIONS.values():
        if key in rating:
            total += float(rating[key])
            found += 1
    if found:
        rating["overall_score"] = round(total, 1)
    if "one_line_verdict" in rating and "notes" not in rating:
        rating["notes"] = rating["one_line_verdict"]
    return rating


def generate_compass_score_report(cfg, paper_dir: Path, *, context: dict[str, Any] | None = None, model: str = "fallback", timeout: int = 180) -> tuple[str, dict[str, Any]]:
    context = context or build_compass_context(paper_dir)
    normalized = (model or "fallback").strip().lower()
    if normalized == "fallback":
        return _fallback_score_report(context)
    prompt = _score_prompt(context)
    try:
        report = _run_markdown_model(prompt, cfg, model=model, timeout=timeout, system=SCORE_SYSTEM_PROMPT, purpose="todo.compass.score")
        if "## 2. 分项评分" not in report:
            raise ValueError("score report missing Section 2")
        rating = parse_compass_score_report(report)
        if "overall_score" not in rating:
            raise ValueError("failed to parse score report")
        return report, rating
    except Exception:
        return _fallback_score_report(context)


def generate_compass_readable_report(cfg, paper_dir: Path, *, score_report: str, context: dict[str, Any] | None = None, model: str = "fallback", timeout: int = 180) -> str:
    context = context or build_compass_context(paper_dir)
    normalized = (model or "fallback").strip().lower()
    if normalized == "fallback":
        return _fallback_readable_report(context, score_report)
    prompt = _report_prompt(context, score_report)
    try:
        report = _run_markdown_model(prompt, cfg, model=model, timeout=timeout, system=REPORT_SYSTEM_PROMPT, purpose="todo.compass.report")
        if "## 1. 必学先修知识（按顺序）" not in report:
            raise ValueError("readable report missing Section 1")
        return report
    except Exception:
        return _fallback_readable_report(context, score_report)


def ensure_todo_placeholder_paper(
    cfg,
    *,
    title: str,
    authors: list[str] | None = None,
    year: int | None = None,
    journal: str = "",
    doi: str = "",
    abstract: str = "",
    read_status: str = "unread",
) -> Path:
    authors = list(authors or [])
    clean_doi = _clean_doi(doi)
    first_author = authors[0] if authors else "Todo"
    identity_seed = clean_doi or f"{_norm(title)}:{year or 'unknown'}:{_norm(first_author)}"
    paper_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"todo-placeholder:{identity_seed}"))
    author_slug = _slugify(first_author.split()[-1] if first_author else "Todo", limit=24).title()
    year_label = str(year or "Unknown")
    title_slug = _slugify(title, limit=60)
    dir_name = f"{author_slug}-{year_label}-{title_slug}"[:120].rstrip("-")

    paper_dir = cfg.papers_dir / dir_name
    paper_dir.mkdir(parents=True, exist_ok=True)

    existing: dict[str, Any] = {}
    if (paper_dir / "meta.json").exists():
        existing = read_meta(paper_dir)

    tags = list(existing.get("tags") or [])
    if "Todo占位" not in tags:
        tags.append("Todo占位")

    meta = {
        **existing,
        "id": existing.get("id") or paper_id,
        "title": title,
        "authors": authors,
        "first_author_lastname": first_author.split()[-1] if first_author else "Todo",
        "year": year,
        "journal": journal,
        "doi": clean_doi,
        "abstract": abstract,
        "paper_type": "todo-placeholder",
        "todo_placeholder": True,
        "read_status": read_status or existing.get("read_status") or "unread",
        "tags": tags,
    }
    write_meta(paper_dir, meta)

    placeholder_md = f"""# {title}

## Placeholder Note

This paper directory was created from the Zotero Todo collection because no local parsed paper was available yet. The generated materials in this folder must stay conservative and can mark 信息不足 when full text evidence is missing.

## Metadata Snapshot

- Authors: {', '.join(authors) if authors else 'Unknown'}
- Year: {year or 'Unknown'}
- Venue: {journal or 'Unknown'}
- DOI: {clean_doi or 'N/A'}
- Source: Zotero Todo

## Abstract

{abstract or '摘要缺失。'}
"""
    (paper_dir / "paper.md").write_text(placeholder_md.strip() + "\n", encoding="utf-8")
    return paper_dir
