# 交接给下一位 Agent（2026-04-08）

## 当前状态（最新）
- 首页已是 Todo 预览卡片页，旧 306 Library 卡片入口已移除。
- 二级总结页仍是 `todo/[id]`，再跳论文详情页。
- Todo 卡片文件：`scholaraio/web/public/site-data/todo-cards.json`

当前覆盖率：
- 可匹配 Todo 论文：`160`
- 已生成卡片：`144`
- 尚缺卡片：`16`
- 另有未匹配本地论文的 Zotero Todo：`8`（已跳过，不阻塞构建）

静态站已成功构建：`conda run -n node22 npm run generate`。

## 本轮关键改动
1. `scripts/generate_todo_cards.py` 已改为**不走 codex CLI**，改走项目统一 `call_llm()`。
2. 匹配策略改为：未匹配条目告警并跳过，不再整批中断。
3. `todo-cards.json` 当前 `collection.count == cards.length`，字段一致。

## 当前缺失的 16 张卡片（route_id | title）
1. `25c6fe90-bed2-4454-82bb-ee1c9fe463f4` | TOLEBI: Learning Fault-Tolerant Bipedal Locomotion via Online Status Estimation and Fallibility Rewards
2. `fb6729d4-5485-4dc7-b6b7-508272918fc3` | InterPrior: Scaling Generative Control for Physics-Based Human-Object Interactions
3. `109c8325-6b29-4a5a-b979-d6dea9bc5bdf` | Scalable and General Whole-Body Control for Cross-Humanoid Locomotion
4. `c8906839-17a5-44b7-b77c-409e89fe94eb` | CMR: Contractive Mapping Embeddings for Robust Humanoid Locomotion on Unstructured Terrains
5. `8e7b3e07-bf14-4b0a-ae8b-6d06427a68c1` | TTT-Parkour: Rapid Test-Time Training for Perceptive Robot Parkour
6. `3a7ed178-b7f9-4d02-a296-589e1a893a11` | RPL: Learning Robust Humanoid Perceptive Locomotion on Challenging Terrains
7. `0c2def8b-1094-4a79-8550-5a0363b8a87e` | HoRD: Robust Humanoid Control via History-Conditioned Reinforcement Learning and Online Distillation
8. `b3a6e667-563a-41bd-8662-cc9b5e046865` | HumanX: Toward Agile and Generalizable Humanoid Interaction Skills from Human Videos
9. `0d533bae-5657-4777-b9df-0961e93f2377` | HUSKY: Humanoid Skateboarding System via Physics-Aware Whole-Body Control
10. `9b2672ba-18db-4c54-923a-9670520a23a4` | RAPT: Model-Predictive Out-of-Distribution Detection and Failure Diagnosis for Sim-to-Real Humanoid Robots
11. `4e3c81bf-7242-47d4-a1d5-578c2307d426` | Toward Reliable Sim-to-Real Predictability for MoE-based Robust Quadrupedal Locomotion
12. `a7384887-81c5-4079-817c-63eb3552bd5c` | Fast-WAM: Do World Action Models Need Test-time Future Imagination?
13. `c6b43f73-e10e-4b5f-8345-44db93f51f8a` | PDF-HR: Pose Distance Fields for Humanoid Robots
14. `30eb3197-3c25-493d-a93a-bbfab16a072e` | ExpertGen: Scalable Sim-to-Real Expert Policy Learning from Imperfect Behavior Priors
15. `85a988b6-c7dd-4aa6-8948-8d964250abe0` | Pose-NDF: Modeling Human Pose Manifolds with Neural Distance Fields
16. `ae3bdbcf-d3f4-442a-9d62-6d83a560ac3a` | NRDF: Neural Riemannian Distance Fields for Learning Articulated Pose Priors

## 未匹配到本地论文的 8 条 Todo（已跳过）
1. Dynamic Whole-Body Dancing with Humanoid Robots -- A Model-Based Control Approach
2. FlashSAC: Fast and Stable Off-Policy Reinforcement Learning for High-Dimensional Robot Control
3. RK-MPC: Residual Koopman Model Predictive Control for Quadruped Locomotion in Offroad Environments
4. Human-Robot Copilot for Data-Efficient Imitation Learning
5. Drift-Based Policy Optimization: Native One-Step Policy Learning for Online Robot Control
6. Optimizing Neurorobot Policy under Limited Demonstration Data through Preference Regret
7. Heracles: Bridging Precise Tracking and Generative Synthesis for General Humanoid Control
8. DreamControl-v2: Simpler and Scalable Autonomous Humanoid Skills via Trainable Guided Diffusion Priors

## 仍需注意
- 不要恢复旧首页 306 Library 卡片入口。
- 首页只保留 Todo 预览卡片，完整总结放 `todo/[id]`。
- `.codex` 为环境文件，`.gitignore` 中保留忽略规则。
- 当前主要阻塞不是 Python/Conda，而是 MCP 模型调用链路不稳定。
