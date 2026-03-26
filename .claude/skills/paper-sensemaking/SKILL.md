---
name: paper-sensemaking
description: Guide a three-act paper sensemaking conversation and generate or interpret sensemaking.json for a paper. Use when the user wants to explore how a paper changes their prior beliefs, asks for sensemaking, or wants to use ScholarAIO's existing sensemaking generation pipeline.
version: 1.0.0
author: edu-ai-builders / ScholarAIO
license: MIT
tags: ["academic", "research", "sensemaking", "cognitive-restructuring", "paper-analysis"]
---
# 论文意义建构 (Sensemaking)

## Skill 类型
**Prompt-based conversational skill** (L2 - 多步骤工作流)

## 这个 Skill 做什么
不同于传统的"摘要"工具，本 Skill 旨在通过**认知重构** (Sensemaking) 帮助你发现论文如何改变了你的既有认知。它不只是告诉你论文说了什么，而是通过三幕式对话，挖掘论文与你背景之间的“认知摩擦”，最终导出可视化的认知轨迹 JSON。

核心差异：**Sensemaking ≠ 理解，= 认知重构 (Cognitive Restructuring)**

## 使用方式

### Step 1: 触发与背景设定
在对话框输入指令，并提供你的背景（Profile）：

```
/sensemaking
profile: [你的一句话背景，例如：初中数学老师，正在设计几何证明的反馈工具]
paper_ref: [论文 UUID / DOI / 目录名，或者直接粘贴论文全文]
```

### Step 2: 论文加载 (AI 行为)
如果提供了 `paper_ref`，AI 将使用 `show_paper(paper_ref=..., layer=4)` 获取全文内容。如果未提供，AI 会要求你提供背景或粘贴论文。

### Step 3: 完成三幕对话 (人在循环中)
AI 将引导你走过以下流程，每幕结束后请进行回应：

| 幕 | 名称 | 核心目标 |
|----|------|----------|
| 一 | **理解** (Comprehension) | 确认核心主张、学习机制及论文与你视角的关联。 |
| 二 | **冲突** (Collision) | 挖掘你的隐含假设与论文发现之间的摩擦，引导你表态。 |
| 三 | **重构** (Reconstruction) | 总结认知变化 (Delta)，收集具体的行动承诺。 |

### Step 4: 结果导出与可视化
对话结束后，AI 将输出一个完整的 JSON。你可以：
1. 打开 `artifact/sensemaking-canvas.html`。
2. 粘贴 JSON。
3. 点击“渲染认知轨迹”进行可视化。

## 指令集 (JSON 输出后)

- `/深挖 [某个冲突点]`：基于 Socratic 提问继续深度探讨。
- `/prd`：将达成的“行动改变” (one_change) 展开为产品需求文档草稿。
- `/对比 [另一篇 paper]`：对比两篇论文带来的认知变化差异。

## 组件清单
- `prompt/system-prompt.md`: 核心执行逻辑 (注入式 System Prompt)
- `artifact/sensemaking-canvas.html`: 可视化画布
- `assets/pedagogy-reference.md`: 教学法参考库
- `assets/paper-archetypes.md`: 论文原型分类

---
作者：Yi · 爱思考的伊伊子
[edu-ai-builders](https://github.com/edu-ai-builders) · 教育AI智造者
集成于 ScholarAIO 系统

## 已有系统接入

这个 skill 不只是对话说明，ScholarAIO 代码里已经有对应功能：
- CLI: `scholaraio gen-sensemaking <paper-id>`
- CLI: `scholaraio close-read <paper-id>` 会连同 `sensemaking` 一起生成
- 后台生成队列支持 `sensemaking` 类型
- 论文目录支持读写 `sensemaking.json`

如果用户要的是“直接生成 sensemaking 结果”，优先走现有生成链；如果用户要的是“围绕一篇论文做三幕式认知重构对话”，按本 skill 的对话流程执行。

