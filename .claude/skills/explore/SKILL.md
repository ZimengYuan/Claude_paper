---
name: explore
description: Analyze the current local ScholarAIO library for trend overview, representative papers, topic readiness, and roadmap generation based on the main topic model.
version: 2.0.0
author: ZimoLiao/scholaraio
license: MIT
tags: ["academic", "research", "literature", "trends", "local-library"]
---
# 本地主库趋势分析

`explore` 现在只分析当前 ScholarAIO 主库，不再从 OpenAlex 或 `data/explore/` 拉取外部文献。

## 作用

围绕当前 `data/papers/` 与主 `data/topic_model/`，回答三件事：
- 这批论文覆盖了哪些年份、作者和期刊
- 当前主库里哪些代表论文最值得先读
- 是否已经具备生成 roadmap 的条件

## CLI

```bash
scholaraio explore info
scholaraio explore info --top 15
scholaraio explore info --name current-library
```

说明：
- `--name` 仅支持 `current-library`（也兼容 `main` / `library` / `current` / `local`）
- roadmap 生成依赖主 topic model，而不是独立 explore 库

## Web

Web 端 `/explore` 页面现在直接展示：
- 当前主库概览
- 趋势统计与代表论文
- roadmap 就绪状态与生成结果

## 不再支持

以下旧能力已移除：
- `explore fetch`
- `explore search`
- `explore embed`
- `explore topics`
- 基于 `data/explore/<name>/` 的外部文献库
