"""Learning materials generation module.

Generates study materials from papers:
- summary.md: Detailed paper summary
- method.md: Methodology explanation
- reflection.md: Reflection template
- user.md: User notes template

Uses LLM for content generation based on paper content (L1-L4).
"""

from __future__ import annotations

import logging
from pathlib import Path

from .config import Config
from .loader import load_l1, load_l2, load_l3, load_l4
from .papers import (
    read_meta,
    set_alphaxiv_summary,
    summary_path,
    method_path,
    reflection_path,
    user_notes_path,
    write_summary,
    write_method,
    write_reflection,
    write_user_notes,
)

_log = logging.getLogger(__name__)


# ============================================================================
#  Prompt Templates
# ============================================================================

SUMMARY_SYSTEM = """You are an academic paper summarizer. Generate a comprehensive summary of the paper in Markdown format.

IMPORTANT: Write in Simplified Chinese (简体中文). Do NOT include the paper title or authors in your output. Start directly with the content.
Use standard LaTeX for equations (e.g., $E=mc^2$ or $$E=mc^2$$). 
DO NOT use any HTML tags, KaTeX/MathML artifacts, or style attributes. 
Keep the output as clean Markdown.

Include:
1. 核心创新点 (Core Innovation)

用1-2句话概括本文最关键的创新



这篇论文解决了什么之前没解决的问题?

或者用什么新方法解决了已有问题?

2. 技术创新拆解 (Technical Contributions)

列出 2-4 个具体的技术创新点:



创新点 1: [简述] - 为什么这个创新重要?

创新点 2: [简述] - 解决了什么限制?

创新点 3: [简述] - 带来了什么提升?

3. 方法论突破 (Methodological Breakthrough)

新颖性: 与现有方法(SOTA)的本质区别是什么?

关键技术: 实现创新的核心技术手段(算法/架构/机制)

理论支撑: 是否有新的理论分析或证明?

4. 实验验证 (Key Results)

主要数据集: 在哪些benchmark上验证?

性能提升: 相比baseline的关键指标提升(用数字说话)

消融实验: 哪个组件贡献最大?

5. 局限与启发 (Limitations & Insights)

当前局限: 作者承认或隐含的limitation

未来方向: 这个工作开启了什么新的研究方向?

可迁移性: 这个创新能否应用到其他领域?

6. 一句话总结

如果只能记住一件事,那就是: [用一句话总结这篇论文为什么值得关注]。对于这一句话尽量地技术化，不要有太多虚内容！！

Use clear headings and bullet points. Keep it concise but informative."""


METHOD_SYSTEM = """You are an academic methodology analyst. Explain the paper's methods in detail.

IMPORTANT: Write in Simplified Chinese (简体中文). Do NOT include the paper title or authors in your output. Start directly with the content.

CRITICAL INSTRUCTION: DO NOT generate or attempt to re-write complex mathematical formulas or LaTeX blocks. Instead, refer to their location in the original paper.
- Use references like: "见论文第 X 节关于 [变量名/过程名] 的定义" 或 "详见 [章节名] 中的核心公式".
- If you need to mention a simple variable, use plain text or very simple LaTeX like $x_t$.
- For complex equations (like those involving summations, integrals, or multi-line structures), describe what they represent and point the reader to the exact section in the paper.

Include:
1. **问题形式化**: 描述问题是如何定义的，并指引到论文中的相关章节/公式。
2. **技术方法**: 描述核心算法/架构，引用论文中的关键图表或公式编号。
3. **实现细节**: 关键的技术选择和参数，引用文中提到的具体设置。
4. **实验设置**: 数据集、评估指标、基线方法。
5. **技术优势**: 这个方法为什么效果好？
6. **技术弱点**: 潜在的问题或局限性。

Be precise and technical, but keep the Markdown clean by avoiding complex rendering."""


REFLECTION_SYSTEM = """You are a research mentor. Create a reflection template for studying this paper.

Include sections for:
1. **Initial Impressions**: First thoughts after reading
2. **Key Takeaways**: Most important learnings
3. **Questions**: Questions raised while reading
4. **Connections**: How does this relate to your research?
5. **Action Items**: Next steps (reproduce, extend, cite, etc.)
6. **Rating**: Overall assessment (1-5 stars)

Leave space for the user to fill in their responses."""


USER_NOTES_SYSTEM = """Create a user notes template for this paper.

Include sections for:
1. **Citation Info**: Quick reference (authors, year, venue)
2. **One-sentence Summary**: Brief description in one sentence
3. **Key Concepts**: Important terms and definitions
4. **Figures/Tables**: Notable visualizations
5. **Interesting Quotes**: Worthwhile excerpts
6. **Personal Notes**: Your thoughts and insights
7. **Related Papers**: Connected works in your library

Use a structured template format."""


RATING_SYSTEM = """You are an expert academic paper reviewer. Rate this paper based on the following criteria:

1. **Innovation (创新性)**: 1-10分 - 论文的原创性和技术突破程度
2. **Technical Quality (技术质量)**: 1-10分 - 方法论的正确性和完整性
3. **Experimental Validation (实验验证)**: 1-10分 - 实验设计的充分性和结果的可信度
4. **Writing Quality (写作质量)**: 1-10分 - 论文表达清晰度和组织结构
5. **Relevance (相关性)**: 1-10分 - 与你研究方向的关联程度

Return ONLY a JSON object with the following format:
{
  "innovation": X,
  "technical_quality": X,
  "experimental_validation": X,
  "writing_quality": X,
  "relevance": X,
  "overall_score": X,
  "strengths": ["优点1", "优点2"],
  "weaknesses": ["缺点1", "缺点2"],
  "notes": "简短评语"
}

Calculate overall_score as the weighted average: innovation*0.3 + technical_quality*0.25 + experimental_validation*0.2 + writing_quality*0.1 + relevance*0.15"""


SENSEMAKING_SYSTEM = """你是一个论文意义建构伙伴。你的任务是基于论文内容和给定的用户画像(Profile)，模拟一场认知重构对话，并最终输出可视化的认知轨迹 JSON。

Sensemaking ≠ 理解。Sensemaking = 认知重构 (Cognitive Restructuring)。
你的全部工作围绕认知变化(Delta)展开。

用户画像(Profile): {profile}

请模拟三幕对话的过程：
1. 理解 (Comprehension): 核心主张、学习机制、用户视角关联。
2. 冲突 (Collision): 挖掘用户的隐含假设与论文发现之间的摩擦点。
3. 重构 (Reconstruction): 总结认知变化 delta 和具体的行动改变 one_change。

最后，请严格按照以下格式输出 JSON 对象（不要有任何 markdown 包装，直接输出 {{ }}）：

{{
  "meta": {{
    "paper_title": "论文标题",
    "profile_read": "一句话复述对用户 profile 的理解",
    "session_date": "YYYY-MM-DD"
  }},
  "act1_comprehension": {{
    "core_claim": "核心主张",
    "learning_mechanism": "学习者做什么 → 系统响应 → 学习者变化",
    "user_perspective": "论文与用户项目的具体关联"
  }},
  "act2_collision": {{
    "user_schema_before": "用户原有的假设",
    "paper_challenge": "论文挑战该假设的发现",
    "friction": "认知摩擦点说明",
    "user_stance": "agree",
    "user_reasoning": "模拟用户的认同理由",
    "probe_exchange": [
      {{ "probe": "AI 追问", "response": "用户深度的回答" }}
    ]
  }},
  "act3_reconstruction": {{
    "before": "原有认知",
    "after": "新认知",
    "delta": "认知变化的核心",
    "one_change": "具体打算改变的一件事"
  }}
}}"""


# ============================================================================
#  Generation Functions
# ============================================================================


def _get_paper_content(paper_dir: Path, max_l4_chars: int = 50000) -> dict:
    """Load paper content at different levels.

    Args:
        paper_dir: Path to paper directory.
        max_l4_chars: Maximum characters to include from L4 content.

    Returns:
        Dict with 'l1', 'l2', 'l3', 'l4' content.
    """
    meta = read_meta(paper_dir)
    l1 = {
        "title": meta.get("title", ""),
        "authors": meta.get("authors", []),
        "year": meta.get("year", ""),
        "journal": meta.get("journal", ""),
        "doi": meta.get("doi", ""),
        "abstract": meta.get("abstract", ""),
    }

    l2 = meta.get("abstract", "")
    l3 = meta.get("conclusion", "") or meta.get("l3_content", "")
    l4 = load_l4(paper_dir / "paper.md") if (paper_dir / "paper.md").exists() else ""

    # Truncate L4 if too long
    if len(l4) > max_l4_chars:
        l4 = l4[:max_l4_chars] + "\n\n... [truncated]"

    return {"l1": l1, "l2": l2, "l3": l3, "l4": l4}


def _call_llm_for_content(
    content: dict,
    system_prompt: str,
    cfg: Config,
    prompt_template: str,
) -> str:
    """Call LLM to generate content based on paper content.

    Args:
        content: Dict with paper content at different levels.
        system_prompt: System prompt for the LLM.
        cfg: ScholarAIO config.
        prompt_template: User prompt template with {l1}, {l2}, {l3}, {l4} placeholders.

    Returns:
        Generated content.
    """
    from scholaraio.metrics import call_llm

    # Build prompt with available content
    prompt = prompt_template.format(
        title=content["l1"].get("title", ""),
        authors=", ".join(content["l1"].get("authors", [])),
        year=content["l1"].get("year", ""),
        journal=content["l1"].get("journal", ""),
        doi=content["l1"].get("doi", ""),
        abstract=content["l2"],
        conclusion=content["l3"],
        full_text=content["l4"],
    )

    try:
        result = call_llm(
            prompt=prompt,
            config=cfg,
            system=system_prompt,
            json_mode=False,
            max_tokens=8000,
            timeout=cfg.llm.timeout_clean,
            purpose="generate.material",
        )
        return _clean_generated_content(result.content)
    except Exception as e:
        _log.error("LLM generation failed: %s", e)
        raise


def _clean_generated_content(text: str) -> str:
    """Clean up HTML/KaTeX artifacts from LLM output.

    Args:
        text: Raw generated content.

    Returns:
        Cleaned Markdown content.
    """
    import re

    # 1. Handle character entities and zero-width spaces EARLY
    # This allows us to catch escaped tags in the next steps
    text = text.replace("&#x27;", "'").replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("\u200b", "") # zero-width space
    text = text.replace("\u200e", "").replace("\u200f", "") # LTR/RTL marks
    text = text.replace("\u0332", "") # combining low line

    # 2. Extract content from annotation tags if they exist
    # This often contains the clean LaTeX we actually want
    def extract_tex(match):
        tex = match.group(1)
        return tex
    text = re.sub(r'<annotation encoding="application/x-tex">([\s\S]*?)</annotation>', extract_tex, text)

    # 3. Aggressively remove all HTML tags except standard Markdown or simple inline ones
    # We remove all <...>, but try to keep text inside them.
    # Note: This is a bit brute-force but effective for the artifacts we see.
    text = re.sub(r'<[^>]+>', "", text)

    # 4. Remove obvious KaTeX/MathML error messages and artifacts
    text = re.sub(r"in math mode at position \d+: [^̲]+̲", "", text)
    text = re.sub(r"style=\\[\"'].*?\\[\"']", "", text) # Handle escaped styles
    text = re.sub(r"style=['\"].*?['\"]", "", text) # Handle normal styles
    
    # 5. Fix common corrupted LaTeX patterns (like \text missing backslash)
    # Sometimes LLM outputs {  ext{...}} or similar due to encoding issues
    text = re.sub(r'{\s*ext{', r'{\\text{', text)
    text = re.sub(r'{\s*au{', r'{\\tau{', text)
    # If the text has many single backslashes followed by letters that should be double for Markdown
    # we don't do blind replacement, but we fix the most common ones.

    # 6. Remove remaining artifacts that look like broken HTML brackets
    text = re.sub(r'\\?"?\s*style="[^"]*"\s*>?', "", text)
    text = re.sub(r'\\?"?\s*aria-hidden="[^"]*"\s*>?', "", text)
    
    # 7. Final cleanup of whitespace and empty lines
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def generate_summary(paper_dir: Path, cfg: Config, force: bool = False) -> str:
    """Generate summary.md for a paper.

    Args:
        paper_dir: Path to paper directory.
        cfg: ScholarAIO config.
        force: Overwrite existing file.

    Returns:
        Path to generated summary.md.
    """
    output_path = summary_path(paper_dir)

    if output_path.exists() and not force:
        _log.info("summary.md already exists, skipping (use force=True to overwrite)")
        return str(output_path)

    content = _get_paper_content(paper_dir)

    prompt_template = """Generate a detailed summary of this paper:

Title: {title}
Authors: {authors}
Year: {year}
Journal: {journal}
DOI: {doi}

Abstract:
{abstract}

Conclusion:
{conclusion}

Full Text (first portion):
{full_text}

Provide a comprehensive summary following the system instructions."""

    result = _call_llm_for_content(
        content=content,
        system_prompt=SUMMARY_SYSTEM,
        cfg=cfg,
        prompt_template=prompt_template,
    )

    write_summary(paper_dir, result)
    _log.info("Generated summary.md for %s", paper_dir.name)

    # Also save to meta.json for API access
    from .papers import update_meta
    import datetime
    update_meta(paper_dir, summary=result, generated_at=datetime.datetime.now().isoformat())

    return str(output_path)


def generate_method(paper_dir: Path, cfg: Config, force: bool = False) -> str:
    """Generate method.md for a paper.

    Args:
        paper_dir: Path to paper directory.
        cfg: ScholarAIO config.
        force: Overwrite existing file.

    Returns:
        Path to generated method.md.
    """
    output_path = method_path(paper_dir)

    if output_path.exists() and not force:
        _log.info("method.md already exists, skipping (use force=True to overwrite)")
        return str(output_path)

    content = _get_paper_content(paper_dir)

    prompt_template = """Generate a detailed methodology explanation for this paper:

Title: {title}
Authors: {authors}
Year: {year}

Abstract:
{abstract}

Conclusion:
{conclusion}

Full Text:
{full_text}

Provide a detailed methodology explanation following the system instructions."""

    result = _call_llm_for_content(
        content=content,
        system_prompt=METHOD_SYSTEM,
        cfg=cfg,
        prompt_template=prompt_template,
    )

    write_method(paper_dir, result)
    _log.info("Generated method.md for %s", paper_dir.name)

    # Also save to meta.json for API access
    from .papers import update_meta
    import datetime
    update_meta(paper_dir, method_summary=result, generated_at=datetime.datetime.now().isoformat())

    return str(output_path)


def generate_reflection(paper_dir: Path, cfg: Config, force: bool = False) -> str:
    """Generate reflection.md for a paper.

    Args:
        paper_dir: Path to paper directory.
        cfg: ScholarAIO config.
        force: Overwrite existing file.

    Returns:
        Path to generated reflection.md.
    """
    output_path = reflection_path(paper_dir)

    if output_path.exists() and not force:
        _log.info("reflection.md already exists, skipping (use force=True to overwrite)")
        return str(output_path)

    content = _get_paper_content(paper_dir)

    prompt_template = """Create a reflection template for studying this paper:

Title: {title}
Authors: {authors}
Year: {year}
Journal: {journal}

Abstract:
{abstract}

Provide a reflection template following the system instructions. Leave space for user responses."""

    result = _call_llm_for_content(
        content=content,
        system_prompt=REFLECTION_SYSTEM,
        cfg=cfg,
        prompt_template=prompt_template,
    )

    write_reflection(paper_dir, result)
    _log.info("Generated reflection.md for %s", paper_dir.name)

    return str(output_path)


def generate_user_notes(paper_dir: Path, cfg: Config, force: bool = False) -> str:
    """Generate user.md for a paper.

    Args:
        paper_dir: Path to paper directory.
        cfg: ScholarAIO config.
        force: Overwrite existing file.

    Returns:
        Path to generated user.md.
    """
    output_path = user_notes_path(paper_dir)

    if output_path.exists() and not force:
        _log.info("user.md already exists, skipping (use force=True to overwrite)")
        return str(output_path)

    content = _get_paper_content(paper_dir)

    prompt_template = """Create a user notes template for this paper:

Title: {title}
Authors: {authors}
Year: {year}
Journal: {journal}
DOI: {doi}

Abstract:
{abstract}

Provide a structured notes template following the system instructions."""

    result = _call_llm_for_content(
        content=content,
        system_prompt=USER_NOTES_SYSTEM,
        cfg=cfg,
        prompt_template=prompt_template,
    )

    write_user_notes(paper_dir, result)
    _log.info("Generated user.md for %s", paper_dir.name)

    return str(output_path)


def generate_all(paper_dir: Path, cfg: Config, force: bool = False) -> dict[str, str]:
    """Generate learning materials for a paper.

    Currently generates: summary, method, rating, sensemaking (if tagged)
    (reflection and user_notes disabled by default - enable manually if needed)

    Args:
        paper_dir: Path to paper directory.
        cfg: ScholarAIO config.
        force: Overwrite existing files.

    Returns:
        Dict mapping material type to file path.
    """
    results = {}

    try:
        results["summary"] = generate_summary(paper_dir, cfg, force)
    except Exception as e:
        _log.warning("Failed to generate summary: %s", e)

    try:
        results["method"] = generate_method(paper_dir, cfg, force)
    except Exception as e:
        _log.warning("Failed to generate method: %s", e)

    try:
        results["rating"] = str(generate_rating(paper_dir, cfg, force))
    except Exception as e:
        _log.warning("Failed to generate rating: %s", e)

    # Automatically generate sensemaking if paper is tagged with "精读"
    from .papers import get_tags
    tags = get_tags(paper_dir)
    if "精读" in tags:
        try:
            results["sensemaking"] = generate_sensemaking(paper_dir, cfg, force)
        except Exception as e:
            _log.warning("Failed to generate sensemaking: %s", e)

    # Reflection and user_notes are disabled by default
    # Use generate_reflection() or generate_user_notes() explicitly if needed

    return results


def generate_sensemaking(paper_dir: Path, cfg: Config, force: bool = False) -> str:
    """Generate sensemaking.json for a paper.

    Args:
        paper_dir: Path to paper directory.
        cfg: ScholarAIO config.
        force: Overwrite existing file.

    Returns:
        Path to generated sensemaking.json.
    """
    from .papers import sensemaking_path, write_sensemaking
    output_path = sensemaking_path(paper_dir)

    if output_path.exists() and not force:
        _log.info("sensemaking.json already exists, skipping (use force=True to overwrite)")
        return str(output_path)

    content = _get_paper_content(paper_dir)
    
    # Try to get user profile from config
    profile = cfg.user.profile if hasattr(cfg, "user") else "一个关注 AI 教育和认知科学的研究者"

    prompt = f"""Perform a paper sensemaking analysis:

Title: {content["l1"].get("title", "N/A")}
Abstract: {content["l2"]}
Conclusion: {content["l3"]}
Full Text (snippet): {content["l4"][:5000]}

Generate the sensemaking JSON based on the system prompt and the user profile: {profile}"""

    from scholaraio.metrics import call_llm
    import json
    import re

    try:
        result = call_llm(
            prompt=prompt,
            config=cfg,
            system=SENSEMAKING_SYSTEM.format(profile=profile),
            json_mode=True,
            max_tokens=2000,
            timeout=max(cfg.llm.timeout, cfg.llm.timeout_clean),
            purpose="generate.sensemaking",
        )

        text = result.content.strip()
        if text.startswith("```"):
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
        
        sensemaking_data = json.loads(text)
        write_sensemaking(paper_dir, sensemaking_data)
        _log.info("Generated sensemaking.json for %s", paper_dir.name)

        return str(output_path)

    except Exception as e:
        _log.error("Sensemaking generation failed: %s", e)
        raise


def generate_rating(paper_dir: Path, cfg: Config, force: bool = False) -> dict:
    """Generate rating for a paper using LLM.

    Args:
        paper_dir: Path to paper directory.
        cfg: ScholarAIO config.
        force: Overwrite existing rating.

    Returns:
        Dict with rating scores.
    """
    from .papers import read_meta, update_meta
    import json
    import re

    meta = read_meta(paper_dir)
    existing_rating = meta.get("rating")
    if existing_rating and not force:
        _log.info("Rating already exists, skipping (use force=True to overwrite)")
        return existing_rating

    # Build prompt with paper info
    prompt = f"""Rate this academic paper:

Title: {meta.get('title', 'N/A')}
Authors: {', '.join(meta.get('authors', []))}
Year: {meta.get('year', 'N/A')}
Journal: {meta.get('journal', 'N/A')}

Abstract:
{meta.get('abstract', 'N/A')[:2000]}

Provide your rating in JSON format as specified in the system prompt."""

    from scholaraio.metrics import call_llm

    try:
        result = call_llm(
            prompt=prompt,
            config=cfg,
            system=RATING_SYSTEM,
            json_mode=True,
            max_tokens=1000,
            timeout=cfg.llm.timeout,
            purpose="generate.rating",
        )

        # Parse JSON response
        text = result.content.strip()
        # Handle cases where LLM returns ```json ... ```
        if text.startswith("```"):
            # Remove any leading/trailing code block markers
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
        
        rating_data = json.loads(text)

        # Update meta.json
        update_meta(paper_dir, rating=rating_data)
        _log.info("Generated rating for %s", paper_dir.name)

        return rating_data

    except Exception as e:
        _log.error("Rating generation failed: %s", e)
        raise


def generate_readme(paper_dir: Path, cfg: Config, force: bool = False) -> str:
    """Generate README.md with paper overview.

    Args:
        paper_dir: Path to paper directory.
        cfg: ScholarAIO config.
        force: Overwrite existing file.

    Returns:
        Path to generated README.md.
    """
    readme_path = paper_dir / "README.md"

    if readme_path.exists() and not force:
        _log.info("README.md already exists, skipping (use force=True to overwrite)")
        return str(readme_path)

    meta = read_meta(paper_dir)

    readme_content = f"""# {meta.get('title', 'Untitled')}

## Metadata

- **Authors**: {', '.join(meta.get('authors', []))}
- **Year**: {meta.get('year', 'N/A')}
- **Journal**: {meta.get('journal', 'N/A')}
- **DOI**: {meta.get('doi', 'N/A')}

## Abstract

{meta.get('abstract', 'No abstract available.')}

## Generated Materials

- [summary.md](./summary.md) - Detailed paper summary
- [method.md](./method.md) - Methodology explanation
- [reflection.md](./reflection.md) - Reflection template
- [user.md](./user.md) - User notes

## Original Paper

- [paper.md](./paper.md) - Full paper content (Markdown)
"""

    readme_path.write_text(readme_content, encoding="utf-8")
    _log.info("Generated README.md for %s", paper_dir.name)

    return str(readme_path)
