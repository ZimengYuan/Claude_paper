# 交接给下一位 Agent（2026-04-08）

## 当前状态（最新）
- 2026-04-09 已重新同步当前 Zotero Todo：Todo 卡片现为 `171` 张。
- 之前“缺失 16”问题已处理完毕；当前新增的 3 张也已补齐到快照中。
- 当前未匹配到本地论文的 Todo 共 `11` 条，均已纳入卡片并生成 `todo-unmatched-*` 路由；论文跳转优先 `paper_route_id`，无本地论文时跳 DOI 外链。
- 当前 `todo-cards.json`：`cards.length = 171`，`collection.count = 171`。

## 本轮新增改动（2026-04-09）
1. `scholaraio/web/public/site-data/todo-cards.json`
	- 已从 `168` 张刷新到 `171` 张，新增 3 个 `todo-unmatched-*` 路由：
	- `todo-unmatched-0deea8df6f8bba65` | Chasing Autonomy: Dynamic Retargeting and Control Guided RL for Performant and Controllable Humanoid Running
	- `todo-unmatched-e26334f4a2b34934` | Make Tracking Easy: Neural Motion Retargeting for Humanoid Whole-body Control
	- `todo-unmatched-91d341bdd7c8a85b` | Tune to Learn: How Controller Gains Shape Robot Policy Learning
2. `scripts/check_snapshot_sync.py`
	- Todo 对齐检查口径改为“Todo 卡片数 vs Zotero Todo 总条目”，不再错误假设卡片只覆盖含 PDF 条目。
3. `tests/test_todo_cards_snapshot.py` / `tests/test_static_snapshot_integrity.py`
	- 去掉写死的 `168`，改成校验快照自洽性与索引连续性。

## 2026-04-08 既有改动
1. `scripts/generate_todo_cards.py`
	- 未匹配条目不再跳过，自动纳入卡片。
	- 增加 Crossref 在线摘要兜底（当本地无摘要时）。
	- 本地论文缺失 / 模型调用失败时启用启发式兜底卡片生成。
	- 新增 `paper_route_id` 字段（用于区分 Todo 详情路由与本地论文路由）。
2. `scholaraio/web/pages/index.vue`
	- 论文按钮逻辑：优先 `/paper/{paper_route_id}`，否则跳 `https://doi.org/{doi}`。
3. `scholaraio/web/pages/todo/[id].vue`
	- 与首页一致的论文跳转逻辑，支持 DOI 外链。

## 构建验证
- 已通过：`conda run -n node22 npm run generate`
- 首页已是 Todo 预览卡片页，旧 306 Library 卡片入口已移除。
- 二级总结页仍是 `todo/[id]`，再跳论文详情页。
- Todo 卡片文件：`scholaraio/web/public/site-data/todo-cards.json`

当前覆盖率：
- 当前 Zotero Todo 总条目：`171`
- 当前已生成卡片：`171`
- 其中未匹配本地论文：`11`

静态站已成功构建：`conda run -n node22 npm run generate`。

## 本轮关键改动
1. `scripts/generate_todo_cards.py` 已改为**不走 codex CLI**，改走项目统一 `call_llm()`。
2. 匹配策略改为：未匹配条目告警并跳过，不再整批中断。
3. `todo-cards.json` 当前 `collection.count == cards.length`，字段一致。

## 当前未匹配到本地论文的 11 条 Todo（已纳入卡片）
1. Dynamic Whole-Body Dancing with Humanoid Robots -- A Model-Based Control Approach
2. FlashSAC: Fast and Stable Off-Policy Reinforcement Learning for High-Dimensional Robot Control
3. RK-MPC: Residual Koopman Model Predictive Control for Quadruped Locomotion in Offroad Environments
4. Human-Robot Copilot for Data-Efficient Imitation Learning
5. Drift-Based Policy Optimization: Native One-Step Policy Learning for Online Robot Control
6. Optimizing Neurorobot Policy under Limited Demonstration Data through Preference Regret
7. Heracles: Bridging Precise Tracking and Generative Synthesis for General Humanoid Control
8. DreamControl-v2: Simpler and Scalable Autonomous Humanoid Skills via Trainable Guided Diffusion Priors
9. Chasing Autonomy: Dynamic Retargeting and Control Guided RL for Performant and Controllable Humanoid Running
10. Make Tracking Easy: Neural Motion Retargeting for Humanoid Whole-body Control
11. Tune to Learn: How Controller Gains Shape Robot Policy Learning

## 仍需注意
- 不要恢复旧首页 306 Library 卡片入口。
- 首页只保留 Todo 预览卡片，完整总结放 `todo/[id]`。
- `.codex` 为环境文件，`.gitignore` 中保留忽略规则。
- 当前主要阻塞不是 Python/Conda，而是 MCP 模型调用链路不稳定。
