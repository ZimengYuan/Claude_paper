#!/usr/bin/env python3
"""Sync local Todo paper summaries from high-quality Todo cards."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scholaraio.config import load_config
from scholaraio.papers import update_meta, write_summary
from scripts.generate_todo_cards import OUTPUT_PATH as TODO_CARDS_PATH
from scripts.generate_todo_cards import PAPER_DETAIL_DIR, _match_todo_papers


_SUMMARY_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (r"\bhumanoid whole-body control\b", "人形机器人全身控制"),
    (r"\bhuman egocentric video\b", "人类第一视角视频"),
    (r"\begocentric visual context\b", "第一视角视觉上下文"),
    (r"\bfuture whole-body motion prediction\b", "未来全身动作预测"),
    (r"\bvlm conditioned motion forecasting\b", "VLM 条件动作预测"),
    (r"\bmotion retargeting \+ robust tracking execution\b", "动作重定向与鲁棒跟踪执行"),
    (r"\bmotion retargeting\b", "动作重定向"),
    (r"\broot-guided policy interface\b", "根轨迹引导的策略接口"),
    (r"\bsdf-based retargeting refinement\b", "基于 SDF 的动作重定向修正"),
    (r"\bpersistent object estimation with digital twin\b", "结合数字孪生的持续物体估计"),
    (r"\bhybrid root trajectory planner\b", "混合根轨迹规划器"),
    (r"\btraining-time reference generator\b", "训练阶段参考轨迹生成器"),
    (r"\bstate-dependent teacher\b", "状态相关教师"),
    (r"\bstate-dependent tracking\b", "状态相关跟踪"),
    (r"\bmulti-modal robot learning\b", "多模态机器人学习"),
    (r"\bdirect gpu tensor views\b", "直接 GPU 张量视图"),
    (r"\bgpu-native\b", "GPU 原生"),
    (r"\bsim-to-real\b", "仿真到真实"),
    (r"\bhuman-in-the-loop\b", "人在回路"),
    (r"\bworld models?\b", "世界模型"),
    (r"\bmotion tracking policy\b", "动作跟踪策略"),
    (r"\bmotion tracking\b", "动作跟踪"),
    (r"\btracking policy\b", "跟踪策略"),
    (r"\bgoal-conditioned\b", "目标条件化"),
    (r"\blatent context\b", "潜在上下文"),
    (r"\brobot teleoperation\b", "机器人遥操作"),
    (r"\breference motion\b", "参考动作"),
    (r"\bdomain randomization\b", "域随机化"),
    (r"\bcontact state\b", "接触状态"),
    (r"\bcontact schedule\b", "接触时序"),
    (r"\bscene graph\b", "场景图"),
    (r"\bdemo collection\b", "示教数据采集"),
    (r"\bupper-body joint configuration\b", "上肢关节构型"),
    (r"\bbimanual interaction forces\b", "双手交互力"),
    (r"\bforce/torque sensors?\b", "力/力矩传感器"),
    (r"\bindustrial and research manipulators\b", "工业与科研机械臂"),
    (r"\bmotion naturalness\b", "动作自然性"),
    (r"\bfoothold/contact/joint targets\b", "落脚点、接触与关节目标"),
    (r"\bsparse foothold\b", "稀疏落脚点"),
    (r"\bplanar footholds\b", "平面落脚点"),
    (r"\bfoot-target\b", "足端目标"),
    (r"\bplanner-agnostic\b", "与规划器解耦的"),
    (r"\bstanding success\b", "站立成功率"),
    (r"\bfoot-placement\b", "足端落点"),
    (r"\bsparse terrain\b", "稀疏地形"),
    (r"\bfailure recovery\b", "失败恢复"),
    (r"\brecovery reflex\b", "恢复反应"),
)


_CONTRIBUTION_TITLE_TRANSLATIONS: dict[str, str] = {
    "balanced cross-entropy": "平衡交叉熵",
    "teacher-side alignment objective": "教师侧对齐目标",
    "proxy student for cheap capability estimation": "用代理学生做低成本能力估计",
    "shared action decoder and feature alignment": "共享动作解码器与特征对齐",
    "dual use of the kl signal": "KL 信号的双重用法",
    "motion moe": "运动专家混合",
    "meta-analysis": "元分析",
    "terrain-adaptive phase reward": "地形自适应相位奖励",
    "robot-centric heightmap perception": "机器人中心高度图感知",
    "direct joint-space policy with asymmetric critic": "配合非对称评论家的直接关节空间策略",
    "training stack for transferable locomotion": "面向可迁移 locomotion 的训练栈",
    "ego-centric latent world model": "第一视角潜在世界模型",
    "demonstration-free offline multi-task data": "无示范的离线多任务数据",
    "value-guided sampling mpc": "价值引导采样 MPC",
    "real-time humanoid deployment": "实时人形机器人部署",
    "torque-level residual blending": "力矩级残差融合",
    "physx direct-gpu tensor views": "PhysX 直接 GPU 张量视图",
    "temporally averaged gait loss": "时间平均步态损失",
    "embodiment descriptors": "本体描述符",
    "residual post-training": "残差式后训练",
    "flow-matching latent computation": "Flow Matching 潜在计算",
    "period-conditioned circular latent embedding": "周期条件圆形潜在嵌入",
    "single-step intrinsic reward for periodic motion": "面向周期运动的单步内在奖励",
    "adaptive period-range sampling": "自适应周期范围采样",
    "orthogonal composition with metra": "与 METRA 的正交组合",
    "hindsight goal relabeling": "后见目标重标记",
    "per-sample ratio clipping": "逐样本比例裁剪",
    "latent action barrier": "潜在动作屏障",
    "action-conditioned timestep modulation": "动作条件时间步调制",
    "4d gaussian rendering head": "4D 高斯渲染头",
    "film-modulated critic": "FiLM 调制评论家",
    "human egocentric video → future whole-body motion prediction": "人类第一视角视频到未来全身动作预测",
    "vlm conditioned motion forecasting": "VLM 条件动作预测",
    "motion retargeting + robust tracking execution": "动作重定向与鲁棒跟踪执行",
    "chunkwise parallel training + recurrent deployment": "分块并行训练与循环式部署",
    "constraint-aware whole-body controller": "约束感知的全身控制器",
    "root-guided policy interface": "根轨迹引导的策略接口",
    "sdf-based retargeting refinement": "基于 SDF 的动作重定向修正",
    "persistent object estimation with digital twin": "结合数字孪生的持续物体估计",
    "hybrid root trajectory planner": "混合根轨迹规划器",
    "linear policy net (lpn)": "线性策略网络（LPN）",
    "kinematic consistency optimization": "运动学一致性优化",
    "goal-in-context latent": "上下文目标潜变量",
    "ground-aware command optimization (gco)": "地面感知指令优化（GCO）",
    "parseval-guided residual policy adaptation": "Parseval 引导的残差策略适配",
    "center-of-mass-aware control": "质心感知控制",
    "physically grounded pretraining pipeline": "物理约束预训练流水线",
    "teleoperation-oriented general tracker": "面向遥操作的通用跟踪器",
    "two-level adaptive resampling": "两级自适应重采样",
    "rapid residual adaptation": "快速残差适配",
    "robotbridge deployment stack": "RobotBridge 部署栈",
    "strike manifold expansion": "击球流形扩展",
}


def _localize_contribution_title(title: str) -> str:
    raw = str(title or '').strip()
    if not raw:
        return '创新点'
    translated = _CONTRIBUTION_TITLE_TRANSLATIONS.get(raw.lower())
    if translated:
        return translated
    return _normalize_summary_text(raw)


def _normalize_summary_text(text: str) -> str:
    body = str(text or '').strip()
    if not body:
        return ''
    for pattern, replacement in _SUMMARY_REPLACEMENTS:
        body = re.sub(pattern, replacement, body, flags=re.IGNORECASE)
    body = body.replace(',那就是:', '，那就是：')
    body = body.replace('If only remember one thing:', '如果只记住一点：')
    body = re.sub(r'\s+([，。；：！？）])', r'\1', body)
    body = re.sub(r'([（])\s+', r'\1', body)
    body = re.sub(r'\s{2,}', ' ', body)
    return body.strip()


def _format_bullet(label: str, text: str) -> str:
    body = str(text or "").strip()
    return f"- **{label}**：{body}" if body else f"- **{label}**："


def render_todo_summary_markdown(card: dict[str, Any]) -> str:
    normalize = _normalize_summary_text
    contributions = []
    for item in card.get("technical_contributions") or []:
        title = _localize_contribution_title(str((item or {}).get("title") or "").strip() or "创新点")
        body = normalize(str((item or {}).get("body") or "").strip())
        contributions.append(f"- **{title}**：{body}" if body else f"- **{title}**")

    method = card.get("methodological_breakthrough") or {}
    results = card.get("key_results") or {}
    limitations = card.get("limitations") or {}

    parts = [
        f"# 论文总结：{str(card.get('title') or '').strip()}",
        "",
        "## 1. 核心创新点",
        "",
        normalize(str(card.get("core_innovation") or "").strip()),
        "",
        "## 2. 技术创新拆解",
        "",
        *(contributions or ["- **创新点 1**："]),
        "",
        "## 3. 方法论突破",
        "",
        _format_bullet("新颖性", normalize(str(method.get("novelty") or "").strip())),
        _format_bullet("关键技术", normalize(str(method.get("key_technique") or "").strip())),
        _format_bullet("理论支撑", normalize(str(method.get("theory") or "").strip())),
        "",
        "## 4. 实验验证",
        "",
        _format_bullet("主要基准/场景", normalize(str(results.get("benchmarks") or "").strip())),
        _format_bullet("性能提升", normalize(str(results.get("improvements") or "").strip())),
        _format_bullet("消融实验", normalize(str(results.get("ablation") or "").strip())),
        "",
        "## 5. 局限与启发",
        "",
        _format_bullet("当前局限", normalize(str(limitations.get("current") or "").strip())),
        _format_bullet("未来方向", normalize(str(limitations.get("future") or "").strip())),
        _format_bullet("可迁移性", normalize(str(limitations.get("transferability") or "").strip())),
        "",
        "## 6. 一句话总结",
        "",
        normalize(str(card.get("one_line_summary") or "").strip()),
        "",
    ]
    return "\n".join(parts).strip() + "\n"


def _load_todo_cards() -> dict[str, dict[str, Any]]:
    payload = json.loads(TODO_CARDS_PATH.read_text(encoding="utf-8"))
    cards = payload.get("cards") or []
    card_map: dict[str, dict[str, Any]] = {}
    for card in cards:
        route_id = str(card.get("paper_route_id") or card.get("route_id") or "").strip()
        if route_id:
            card_map[route_id] = card
    return card_map


def _update_static_paper_detail(route_id: str, summary_markdown: str) -> bool:
    detail_path = PAPER_DETAIL_DIR / f"{route_id}.json"
    if not detail_path.exists():
        return False
    payload = json.loads(detail_path.read_text(encoding="utf-8"))
    payload["summary"] = summary_markdown
    detail_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync Todo paper summary.md files from todo-cards.json")
    parser.add_argument("--limit", type=int, default=0, help="Only sync the first N matched local Todo papers")
    parser.add_argument("--skip-static", action="store_true", help="Do not update static paper detail JSON files")
    args = parser.parse_args()

    cfg = load_config()
    card_map = _load_todo_cards()
    items = [item for item in _match_todo_papers() if item.dir_name]
    if args.limit > 0:
        items = items[: args.limit]

    synced = 0
    updated_static = 0
    missing_cards: list[str] = []

    for item in items:
        card = card_map.get(item.route_id)
        if card is None:
            missing_cards.append(item.route_id)
            continue

        summary_markdown = render_todo_summary_markdown(card)
        paper_dir = cfg.papers_dir / item.dir_name
        write_summary(paper_dir, summary_markdown)
        update_meta(
            paper_dir,
            summary=summary_markdown,
            summary_source="todo_card",
            summary_generated_with_model=card.get("generated_with_model") or "",
            summary_generation_mode=card.get("generation_mode") or "",
            summary_generated_at=card.get("generated_at") or "",
        )
        synced += 1

        if args.skip_static is False and _update_static_paper_detail(item.route_id, summary_markdown):
            updated_static += 1

    print(f"Matched local Todo papers: {len(items)}", flush=True)
    print(f"Synced summary.md files: {synced}", flush=True)
    if args.skip_static:
        print("Static paper detail updates: skipped", flush=True)
    else:
        print(f"Static paper detail updates: {updated_static}", flush=True)
    if missing_cards:
        print(f"[WARN] Missing Todo cards for {len(missing_cards)} local Todo papers", flush=True)
        for route_id in missing_cards[:10]:
            print(f"  - {route_id}", flush=True)


if __name__ == "__main__":
    main()
