# 论文分析报告

## 1. 论文摘要
本论文提出了"马尔可夫思考者"范式，通过重新设计强化学习环境来解决长链思维推理中的计算瓶颈问题。传统的LongCoT方法随着思维令牌数量的增加，计算成本呈二次方增长。论文提出的Delethink方法将推理组织成固定大小的块，在每个块边界重置上下文，仅保留少量状态信息，从而实现线性计算复杂度和恒定内存使用。

## 2. 研究背景
强化学习已成为训练推理大语言模型的有效方法，能够产生长思维链。然而，标准的RL"思考环境"中，状态是提示加上所有先前的推理令牌，这使得状态无界，并导致基于注意力的策略在思维延长时需要支付二次计算成本。现有工作主要通过约束思考长度来应对这一问题，而本文提出了一个根本性问题：如果环境本身不产生二次增长会怎样？

## 3. 研究方法

### 3.1 马尔可夫思考范式
论文提出马尔可夫思考范式，其中策略在推进推理时仅依赖于恒定大小的状态，将思考长度与上下文大小解耦。这产生了线性计算和恒定内存的直接结果。

### 3.2 Delethink实现
Delethink是马尔可夫思考的具体实现，将推理组织成固定大小的块序列：
- 在每个块内，模型正常推理
- 在块边界，环境重置上下文，并使用来自前一个块的短延续重新初始化提示
- 策略学习在每个块末尾写入文本状态，以便在重置后能够无缝继续推理

### 3.3 算法实现
```python
算法1 Delethink步骤
输入: 查询q; 推理LLM π_θ; 思考上下文大小C; 马尔可夫状态大小m; 
       Delethink迭代上限I; 组大小G; 奖励函数R; 学习率η

T,R ← [], []  # Delethink轨迹, 奖励
生成Delethink轨迹:
for i ← 1 to G do
    x ← q  # 提示
    y ← π_θ(x; C)  # 生成最多C个令牌
    q ← q ⊕ y_[1:100]  # 连接y的前几个令牌
    τ ← [(x,y)]  # 组i的轨迹
    for t ← 1 to I-1 do
        if last(y) = [EOS] then break
        x ← q ⊕ y_[-m:]  # 保留最后m个思考令牌
        y ← π_θ(x, C-m)  # 生成最多C-m个令牌
        append(τ, (x,y))  # 将块附加到轨迹
    append(R, R(τ))  # 轨迹奖励
    append(T, τ)
```

### 3.4 策略梯度目标函数
论文推导了Delethink环境下的策略梯度估计器：

$$J(θ) = \mathbb{E}_{q∼D,τ∼π_θ(·|q)}[R(τ)] - βKL[π_θ ∥ π_{ref}]$$

具体优化目标为：
$$J(θ) = \mathbb{E}_{τ_1,...,τ_G∼π_{θ_{old}}(.|q)}\left[\frac{1}{G}\sum_{g=1}^G \frac{1}{ℓ(τ_g)}\sum_{l=1}^{L} U(x_l,y_l;θ)\right]$$

其中$U(x,y;θ)$表示每个块的目标函数，遵循PPO在LLMs中的标准形式。

## 4. 实验设计

### 4.1 模型和数据集
- 模型：从R1-Distill 1.5B初始化
- 训练数据集：DeepScaleR数据集，包含约40K个竞赛级数学问题-答案对
- 评估基准：AIME'24、AIME'25、HMMT'25、GPQA-Diamond、LiveCodeBench

### 4.2 基线比较
- 主要基线：LongCoT-RL，24K令牌预算
- 对比基线：LongCoT-RL，8K令牌预算
- 所有准确率数字均为Pass@1，从K个样本估计

### 4.3 训练设置
- 每个RL步骤为128个提示采样8条轨迹（每步共1024个情节）
- 训练1000步，禁用KL惩罚（β=0）
- 应用截断重要性采样以稳定学习
- 训练温度0.6
- Delethink参数：C=8K，m=C/2，I=5

## 5. 实验结果

### 5.1 性能比较

| 方法 | AIME24 | AIME25 | HMMT25 | GPQA-Diamond | LiveCodeBench |
|------|--------|--------|--------|--------------|---------------|
| Delethink 24K | 0.33 | 0.28 | 0.25 | 0.35 | 0.21 |
| LongCoT-RL 24K | 0.30 | 0.25 | 0.23 | 0.34 | 0.19 |
| LongCoT-RL 8K | 0.25 | 0.20 | 0.18 | 0.30 | 0.15 |

**数据分析**：Delethink 24K在所有数学基准测试中均优于LongCoT-RL 24K，在分布外任务上也匹配或略微超越LongCoT-RL 24K。LongCoT-RL 8K consistently表现较差，强调了扩展推理的必要性。

### 5.2 测试时扩展

| 思考预算 | Delethink AIME25 | LongCoT-RL 24K AIME25 |
|----------|------------------|----------------------|
| 16K | 0.23 | 0.22 |
| 24K | 0.28 | 0.25 |
| 48K | 0.30 | 0.25 |
| 72K | 0.31 | 0.25 |
| 96K | 0.32 | 0.25 |
| 128K | 0.33 | 0.25 |

**数据分析**：在训练时间限制内，Delethink 24K和LongCoT-RL都随着思考令牌的增加而提高准确性。超过该预算（阴影区域）后，只有Delethink继续改进，从24K扩展到128K，而LongCoT-RL 24K和8K在各自的训练限制处达到平稳。

### 5.3 计算效率

| 平均思考长度 | LongCoT-RL成本(H100月) | Delethink成本(H100月) |
|--------------|------------------------|----------------------|
| 16K | 3 | 2 |
| 24K | 7 | 3 |
| 48K | 15 | 4 |
| 72K | 21 | 5 |
| 96K | 27 | 7 |

**数据分析**：Delethink的RL环境设计保持峰值内存恒定，在思考扩展时维持吞吐量；LongCoT的内存线性增长，在较长预算下驱动吞吐量下降。在96K平均思考长度下，LongCoT-RL需要27 H100月，而Delethink仅需7 H100月。

### 5.4 计算复杂度分析

| 方法 | 思考令牌 | FLOPs | 内存 | 反向时间 | 生成时间 |
|------|----------|--------|------|----------|----------|
| Base | n | O(n²) | O(n) | T_B | T_G |
| LongCoT | nS | O(n²S²) | O(nS) | O(T_BS²) | O(T_GS²) |
| Delethink | nS | O(n²S) | O(n) | O(T_BS) | O(T_GS) |

## 6. 核心结论

1. **有效性**：Delethink在8K块中推理，但可以思考多达24K令牌，在相同24K思考预算下匹配并超越LongCoT-RL
2. **扩展性**：通过测试时扩展，Delethink继续改进而LongCoT达到平稳
3. **效率**：线性计算效果显著，在96K平均思考长度下，LongCoT-RL成本为27 H100月，而Delethink仅为7 H100月
4. **通用性**：分析显示现成的推理模型经常在各种基准测试中零样本采样马尔可夫轨迹

## 7. 创新点

1. **环境重新设计**：首次提出通过重新设计思考环境而非修改模型架构来解决计算瓶颈
2. **马尔可夫思考范式**：引入将思考长度与上下文大小解耦的新范式
3. **线性计算复杂度**：实现思考长度的线性计算和恒定内存
4. **零样本能力**：发现现成推理模型具有零样本马尔可夫思考能力

## 8. 局限性

1. **状态大小依赖**：性能依赖于适当的马尔可夫状态大小选择
2. **任务特定性**：在需要实时记忆的任务（如填字游戏）上表现受限
3. **实现复杂性**：需要特定的RL环境实现，增加了系统复杂性
4. **块边界开销**：在块边界需要重新编码，增加了额外计算

## 9. 参考文献

| 作者 | 标题 | 年份 | 会议/期刊 | 来源链接 |
|------|------|------|-----------|----------|
| Agarwal et al. | GPT-OSS-120B & GPT-OSS-20B Model Card | 2025 | ArXiv | https://arxiv.org/abs/2508.10925 |
| Aggarwal & Welleck | L1: Controlling How Long a Reasoning Model Thinks with Reinforcement Learning | 2025 | ArXiv | https://arxiv.org/abs/2503.04697 |
| AI21 Labs | Jamba-1.5: Hybrid Transformer-Mamba Models at Scale | 2024 | ArXiv | https://arxiv.org/abs/2408.12570 |
| Ao et al. | Optimizing LLM Inference: Fluid-Guided Online Scheduling with Memory Constraints | 2025 | ArXiv | https://arxiv.org/abs/2504.11320 |
| Balunović et al. | MathArena: Evaluating LLMs on Uncontaminated Math Competitions | 2025 | - | https://matharena.ai/ |
| Beltagy et al. | Longformer: The Long-Document Transformer | 2020 | ArXiv | https://arxiv.org/abs/2004.05150 |
| Cheng & Van Durme | Compressed Chain of Thought: Efficient Reasoning Through Dense Representations | 2024 | ArXiv | https://arxiv.org/abs/2412.13171 |
| Choromanski et al. | Rethinking Attention with Performers | 2021 | ICLR | https://openreview.net/forum?id=Ua6zuk0WRH |
| Cui et al. | The Entropy Mechanism of Reinforcement Learning for Reasoning Language Models | 2025 | ArXiv | https://arxiv.org/abs/2505.22617 |
| Dai et al. | S-GRPO: Early Exit via Reinforcement Learning in Reasoning Models | 2025 | ArXiv | https://arxiv.org/abs/2505.07686 |
| Dao & Gu | Transformers are SSMs: Generalized Models and Efficient Algorithms Through Structured State Space Duality | 2024 | ICML | https://openreview.net/forum?id=ztn8FCR1td |
| Ding et al. | Break the Chain: Large Language Models Can Be Shortcut Reasoners | 2024 | ArXiv | https://arxiv.org/abs/2406.06580 |
| Fan et al. | CoThink: Token-Efficient Reasoning via Instruct Models Guiding Reasoning Models | 2025 | ArXiv | https://arxiv.org/abs/2505.22017 |
| Gemini Team | Gemini 1.5: Unlocking Multimodal Understanding Across Millions of Tokens of Context | 2024 | ArXiv | https://arxiv.org/abs/2403.05530 |
| Gu & Dao | Linear-Time Sequence Modeling with Selective State Spaces | 2023 | ArXiv | https://arxiv.org/abs/2312.00752 |
| Gu et al. | Efficiently Modeling Long Sequences with Structured State Spaces | 2022 | ICLR | https://openreview.net/forum?id=uYLFoz1vlAC |
| Guo et al. | DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning | 2025 | ArXiv | https://arxiv.org/abs/2501.12948 |
| Han et al. | Token-Budget-Aware LLM Reasoning | 2024 | ArXiv | https://arxiv.org/abs/2412.18547 |
| Hooper et al. | KVQuant: Towards 10 Million Context Length LLM Inference with KV Cache Quantization | 2024 | NeurIPS | http://papers.nips.cc/paper/2024/hash/028fcbcf85435d39a40c4d61b42c99a4-Abstract-Conference.html |
| Hou et al. | ThinkPrune: Pruning Long Chain-of-Thought of LLMs via Reinforcement Learning | 2025 | ArXiv | https://arxiv.org/abs/2504.01296 |
| Hsieh et al. | RULER: What's the Real Context Size of Your Long-Context Language Models? | 2024 | ArXiv | https://arxiv.org/abs/2404.06654 |
| Jaech et al. | OpenAI o1 System Card | 2024 | ArXiv | https://arxiv.org/abs/2412.16720 |
| Jain et al. | LiveCodeBench: Holistic and Contamination Free Evaluation of Large Language Models for Code | 2025 | ICLR | https://openreview.net/forum?id=chfJJYC3iL |
| Katharopoulos et al. | Transformers are RNNs: Fast Autoregressive Transformers with Linear Attention | 2020 | ICML | http://proceedings.mlr.press/v119/katharopoulos20a.html |
| Kazemnejad et al. | VinePPO: Refining Credit Assignment in RL Training of LLMs | 2025 | ICML | https://openreview.net/forum?id=Myx2kJFzAn |
| Lambert et al. | Tulu 3: Pushing Frontiers in Open Language Model Post-Training | 2024 | ArXiv | https://arxiv.org/abs/2411.15124 |
| Leng et al. | CrossWordBench: Evaluating the Reasoning Capabilities of LLMs and LVLMs with Controllable Puzzle Generation | 2025 | ArXiv | https://arxiv.org/abs/2504.00043 |
| Li et al. | Adaptive Group Policy Optimization: Towards Stable Training and Token-Efficient Reasoning | 2025 | ArXiv | https://arxiv.org/abs/2503.15952 |
| Lieber et al. | Jamba: A Hybrid Transformer-Mamba Language Model | 2024 | ArXiv | https://arxiv.org/abs/2403.19887 |
| Lin et al. | TrimR: Verifier-based Training-free Thinking Compression for Efficient Test-time Scaling | 2025 | ArXiv | https://arxiv.org/abs/2505.17155 |
| Liu et al. | Can Language Models Learn to Skip Steps? | 2024 | NeurIPS | http://papers.nips.cc/paper/2024/hash/504fa7e518da9d1b53a233ed20a38b46-Abstract-Conference.html |
| Liu et al. | Understanding R1-Zero-like Training: A Critical Perspective | 2025 | ArXiv | https://arxiv.org/abs/2503.20783 |
| Liu et al. | KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache | 2024 | ICML | https://openreview.net/forum?id=L057s2Rq8O |
| Luo et al. | O1-Prune: Length-Harmonizing Fine-Tuning for O1-like Reasoning Pruning | 2025 | ArXiv | https://arxiv.org/abs/2501.12570 |
| Luo et al. | DeepScaleR: Surpassing o1-preview with a 1.5B Model by Scaling RL | 2025 | Notion Blog | https://pretty-radio-b75.notion.site/DeepScaleR-Surpassing-O1-Preview-with-a-1-5B-Model-by-Scaling-RL |
| MAA | American Invitational Mathematics Examination (AIME) 2024 | 2025 | - | https://maa.org/maa-invitational-competitions/ |
| Modarressi et al. | NoLima: Long-Context Evaluation Beyond Literal Matching | 2025 | ArXiv | https://arxiv.org/abs/2502.05167 |
| Moshkov et al. | AIMO-2 Winning Solution: Building State-of-the-Art Mathematical Reasoning Models with OpenMath Reasoning Dataset | 2025 | ArXiv | https://arxiv.org/abs/2504.16891 |
| OpenAI | GPT-5 System Card | 2025 | - | https://cdn.openai.com/gpt-5-system-card.pdf |
| Rein et al. | GPQA: A Graduate-Level Google-Proof Q&A Benchmark | 2024 | CLM | - |
| Shao et al. | DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models | 2024 | ArXiv | https://arxiv.org/abs/2402.03300 |
| Shen et al. | DAST: Difficulty-Adaptive Slow-Thinking for Large Reasoning Models | 2025 | ArXiv | https://arxiv.org/abs/2503.04472 |
| Sheng et al. | HybridFlow: A Flexible and Efficient RLHF Framework | 2024 | ArXiv | https://arxiv.org/abs/2409.19256 |
| Sutton et al. | Policy Gradient Methods for Reinforcement Learning with Function Approximation | 1999 | NeurIPS | - |
| Wang et al. | Linformer: Self-Attention with Linear Complexity | 2020 | ArXiv | https://arxiv.org/abs/2006.04768 |
| Williams | Simple Statistical Gradient-Following Algorithms for Connectionist Reinforcement Learning | 1992 | Machine Learning | - |
| Xia et al. | TokenSkip: Controllable Chain-of-Thought Compression in LLMs | 2025 | ArXiv | https://arxiv.org/abs/2502.12067 |
| Xiao et al. | Efficient Streaming Language Models with Attention Sinks | 2024 | ICLR | https://openreview.net/forum?id=NG7sS51zVF |
| Xiao et al. | LimoPro: Reasoning Refinement for Efficient and Effective Test-time Scaling | 2025 | ArXiv | https://arxiv.org/abs/2505.19187 |
| Yan et al. | InftyThink: Breaking the Length Limits of Long-Context Reasoning in Large Language Models | 2025 | ArXiv | https://arxiv.org/abs/2503.06692 |
| Yang et al. | Qwen3 Technical Report | 2025 | ArXiv | https://arxiv.org/abs/2505.09388 |
| Yang et al. | Post-Training Sparse Attention with Double Sparsity | 2024 | ArXiv | https://arxiv.org/abs/2408.07092 |
| Yang et al. | Gated Linear Attention Transformers with Hardware-Efficient Training | 2024 | ICML | https://openreview.net/forum?id=ia5XvxFUJT |
| Yao et al. | Your Efficient RL Framework Secretly Brings You Off-Policy RL Training | 2025 | - | https://fengyao.notion.site/off-policy-rl |
| Yu et al. | DAPO: An Open-Source LLM Reinforcement Learning System at Scale | 2025 | ArXiv | https://arxiv.org/abs/2503.14476 |
| Zaheer et al. | BigBird: Transformers for Longer Sequences | 2020 | NeurIPS | https://proceedings.neurips.cc/paper/2020/hash/c8512d142a2d849725f31a9a7a361ab9-Abstract.html |
| Zeng et al. | GLM-4.5: Agentic, Reasoning, and Coding (ARC) Foundation Models | 2025 | ArXiv | https://arxiv.org/abs/2508.06471 |
| Zhang et al. | H2O: Heavy-Hitter Oracle for Efficient Generative Inference of Large Language Models | 2023 | NeurIPS | http://papers.nips.cc/paper/2023/hash/6ceefa7b15572587b78ecfcebb2827f8-Abstract-Conference.html |
| Zhao et al. | Let LLMs Break Free from Overthinking via Self-Braking Tuning | 2025 | ArXiv | https://arxiv.org/abs/2505.14604 |
| Zhao et al. | PyTorch FSDP: Experiences on Scaling Fully Sharded Data Parallel | 2023 | ArXiv | https://arxiv.org/abs/2304.11277 |
| Zhao et al. | Exploring and Exploiting the Inherent Efficiency Within Large Reasoning Models for Self-Guided Efficiency Enhancement | 2025 | ArXiv | https://arxiv.org/abs/2506.15647 |
| Zheng et al. | SGLang: Efficient Execution of Structured Language Model Programs | 2024 | NeurIPS | http://papers.nips.cc/paper/2024/hash/724be4472168f31ba1c9ac630f15dec8-Abstract-Conference.html |
| Łan´cucki et al. | Inference-Time Hyper-Scaling with KV Cache Compression | 2025 | ArXiv | https://arxiv.org/abs/2506.05345 |