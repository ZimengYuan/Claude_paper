### 研究脉络概览

人形机器人感知运动控制的发展，本质上是一个从“精确建模”到“数据驱动”、从“被动避障”到“主动感知”、从“单一策略”到“混合智能”的演进过程。早期研究通过强化学习（RL）和领域随机化（Domain Randomization）解决了 Sim-to-Real 的基础迁移问题，赋予机器人基础的高机动性。2024 年以后，随着去噪世界模型（Denoising World Model）和 Voxel-Grid 等 3D 表征的引入，机器人开始具备在复杂非结构化地形（楼梯、泥雪地、崎岖地面）稳定行走的能力。近年来，为了应对真实世界的感知不确定性（如动态障碍、传感器噪声），以混合专家系统（MoE）和视觉-前庭觉组合策略（VB-Com）为代表的复合智能架构逐渐成为主流。更进一步，视觉基础模型（VFM）和对比学习驱动的 CMoE 正在打破传统端到端策略的样本效率瓶颈，并向“超越腿长”的极限机动能力发起挑战。

---

### 阶段一：基础高机动性与 Sim-to-Real 迁移

#### 核心挑战

在人形机器人领域，精确物理模型的构建成本极高，且模型与现实之间存在不可避免的误差。如何绕过精确建模，直接训练出具有高鲁棒性、高速动态响应能力的运动策略，并将其零样本（Zero-shot）部署到现实世界，是首要难题。

#### 关键技术突破

- **自适应课程学习（Adaptive Curriculum）**：动态调整训练任务难度（如速度指令的分布），引导策略从易到难学习，有效提升了极端动作的稳定性。
- **在线系统辨识（Online System Identification）**：在运行过程中实时估计物理参数（摩擦、负载），使控制策略能自适应环境变化。

#### 代表论文

- [Rapid Locomotion via Reinforcement Learning](margolis-2022-rapid-locomotion-via-reinforcement-learning) (2022): 提出了基于 PPO 和自适应课程学习的经典框架，揭示了领域随机化结合在线系统辨识是实现高速、鲁棒人形运动的关键路径。

---

### 阶段二：复杂地形感知与去噪世界模型

#### 核心挑战

将人形机器人的运动能力从平坦地面拓展到野外环境（如积雪、斜坡、不锈钢楼梯）是迈向实际应用的关键一步。此时，策略必须理解局部地形的几何特征并进行实时反应，同时处理仿真到现实的迁移挑战。

#### 关键技术突破

- **去噪世界模型学习（Denoising World Model Learning, DWL）**：通过预测和修正未来状态来生成平滑且鲁棒的运动轨迹，有效抑制了传感器噪声和模型误差的累积。
- **端到端零样本迁移**：同一个神经网络策略可以在仿真中完成训练，并直接部署到真实机器人上。

#### 代表论文

- [Advancing Humanoid Locomotion: Mastering Challenging Terrains with Denoising World Model Learning](c5d5b46d-56aa-4c37-9640-6fb7eeba1953) (2024): 首次实现了人形机器人在野外积雪、斜坡、楼梯等挑战性地形上的稳定运动。

---

### 阶段三：3D 几何感知与 Voxel-Grid 表征

#### 核心挑战

前期基于深度图像（Depth Image）或高程图（Elevation Map）的感知方案存在视野狭窄、局部平坦化的问题。它们难以捕捉垂直障碍物、头顶约束和三维空间中的多层级结构。

#### 关键技术突破

- **Voxel-Grid 表示与 LiDAR 融合**：将稀疏的 3D 点云直接转化为体素网格（Voxel Grid）作为输入，保留了完整的环境拓扑信息。
- **Z-Grouped 2D CNN 策略**：针对体素网格的特点设计了专门的卷积架构，在保持 3D 一致性的同时降低了计算复杂度。

#### 代表论文

- [Gallant: Voxel Grid-based Humanoid Locomotion and Local-navigation across 3D Constrained Terrains](dedd36e7-8081-4a56-bc53-cf9cbe13be9b) (2025): 通过 Voxel-Grid 和 LiDAR 融合，突破了传统 2D 表征的局限，首次在楼梯攀爬任务上实现了接近 100% 的成功率。

---

### 阶段四：混合架构与多策略动态编排

#### 核心挑战

现实世界的感知系统并非完美无缺：动态地形变化和传感器噪声会严重干扰视觉策略。此外，单一策略难以在高度多样化的地形环境中保持高效。如何在“视觉引导的前瞻性”与“前庭觉的可靠性”之间取得平衡？

#### 关键技术突破

- **视觉-前庭觉组合策略（Vision-Blind Composite, VB-Com）**：将视觉策略和盲策略进行解耦与组合，根据实时感知置信度动态切换。
- **多专家混合系统（Mixture of Residual Experts, MoRE）**：通过多个专家网络分别处理不同地形特征，再由门控网络动态调度。

#### 代表论文

- [VB-Com: Learning Vision-Blind Composite Humanoid Locomotion Against Deficient Perception](594bbec9-78a3-4803-84ea-f055993b26a4) (2025): 针对感知失效场景，通过主动降级机制确保机器人在视觉退化时仍能依靠前庭觉维持稳定。
- [MoRE: Mixture of Residual Experts for Humanoid Lifelike Gaits Learning on Complex Terrains](c6874636-9a0a-46fe-bbab-0429a3365750) (2025): 通过多专家系统细分处理复杂地形，并结合步态奖励函数，显著增强了机器人在非结构化地形中的类人步态表现。

---

### 阶段五：视觉基础模型引导与极限机动能力

#### 核心挑战

端到端纯像素级学习存在样本效率极低和 sim-to-real 迁移脆弱的问题。如何让人形机器人完成“超越腿长”的高台攀爬（0.8m+）等极限任务，也是当前 RL 训练范式的巨大挑战。

#### 关键技术突破

- **视觉基础模型（Visual Foundation Model, VFM）先验**：利用冻结的 VFM 将单目 RGB 图像映射到高维 3D 隐空间，有效规避了深度估计的尺度模糊性问题。
- **对比式专家混合（CMoE）**：通过对比学习约束专家激活向量，解决了传统 MoE 门控网络均匀激活导致的专家特化性丧失问题。
- **攀爬式任务组合与广义棘轮奖励**：学习 climb-up、climb-down 等接触丰富的动作组合，通过跟踪最佳历史进度提供稠密监督信号。

#### 代表论文

- [GeoLoco: Leveraging 3D Geometric Priors from Visual Foundation Model for Robust RGB-Only Humanoid Locomotion](47de8671-2802-4d7e-800f-df10aa32aaa8) (2026): 利用 VFM 的几何先验实现了仅靠 RGB 相机的零样本 sim-to-real 迁移。
- [CMoE: Contrastive Mixture of Experts for Motion Control and Terrain Adaptation of Humanoid Robots](9ced0ae6-8ae0-487e-9e7e-c713f88b0d23) (2026): 通过对比学习革新了 MoE 的专家激活机制，使模型能够平滑穿越 20cm 高的台阶和 80cm 宽的缺口。
- [APEX: Learning Adaptive High-Platform Traversal for Humanoid Robots](164e7e11-a590-49d8-bad3-94629f011f42) (2026): 通过任务组合和广义棘轮奖励，实现了约 114% 腿长高度的 0.8m 平台的零样本攀爬。

---

### 未来趋势预测

1. **具身智能与世界模型的深度融合**：
   当前方法虽能解决感知和局部控制问题，但对全局任务理解能力不足。下一步将出现结合大规模世界模型的感知运动策略，使机器人能够理解“这扇门通向哪里”并做出最优路径规划。

2. **面向持续学习的通用人形运动基础模型**：
   类似于大语言模型（LLM）在文本领域的地位，预计将出现基于海量异构数据训练的“人形运动基础模型”。该模型具备对不同地形、步态和任务结构的通用理解能力，只需通过少量样本的微调即可适应全新的运动技能。

3. **主动感知（Active Perception）与多模态传感器的协同编排**：
   未来，机器人将具备根据任务需求主动调整传感器姿态（如主动转头、主动扫描地形）的感知策略。这需要将注意力机制（Attention）与运动控制进行更深度的耦合。
