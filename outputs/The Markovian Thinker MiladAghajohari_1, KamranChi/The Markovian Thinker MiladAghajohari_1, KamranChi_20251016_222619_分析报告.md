# 论文分析报告

## 1. 论文摘要
本论文提出了"马尔可夫思考者"范式，通过重新设计强化学习环境来解决长链思维推理中的计算效率问题。论文提出了Delethink方法，将推理过程组织成固定大小的块，在每个块边界重置上下文，只保留少量关键状态信息，从而将计算复杂度从二次降为线性，内存使用保持恒定。实验表明，该方法在保持推理质量的同时显著降低了计算成本。

## 2. 研究背景
强化学习已成为训练产生长链思维推理LLM的有效方法。然而，标准的RL"思考环境"中，状态是提示加上所有先前的推理标记，这使得状态无界，导致基于注意力的策略在思维延长时需要支付二次计算成本。现有工作通过多阶段训练、长度正则化目标或剪枝等方法来限制计算增长，但这些方法仍然在LongCoT框架下运行，本质上是二次的。

## 3. 研究方法

### 3.1 马尔可夫思考范式
核心思想是重新构建RL公式，使策略读取的有效状态有界，与总思考长度无关。政策在恒定大小的状态下推进推理，将"模型思考多长时间"与"必须处理多少上下文"解耦。

### 3.2 Delethink实现
Delethink通过将推理组织成固定大小的块序列来实例化这一范式：

**具体实现步骤：**
1. 第一个块中，模型像往常一样生成最多C个标记的响应
2. 如果响应以[EOS]结束，跟踪完成
3. 否则，从原始查询和前一个块输出的最后m个标记构建下一个提示
4. 重复此过程直到产生[EOS]或达到迭代上限I

**数学公式：**
- 状态转移动态重新定义为：
```
P(s_{t+1}=s'|s_t=s, a_t=a) = 
   1, 如果(s,a)∈B且s'=s_{:|q|:-m:}⊕s⊕a
   1, 如果(s,a)∉B且s'=s⊕a
   0, 其他情况
```

**策略梯度目标函数：**
```
J(θ) = E[1/ℓ(τ_g) Σ_{l=1}^{L} U(x_l,y_l;θ)]
```
其中U(x,y;θ)表示每个块的目标函数，遵循LLM中PPO的目标。

## 4. 实验设计

### 4.1 模型和数据集
- 模型：从R1-Distill 1.5B初始化
- 训练数据集：DeepScaleR，包含约40K个竞赛级数学问题-答案对
- 评估基准：AIME'24、AIME'25、HMMT'25、GPQA-Diamond、LiveCodeBench

### 4.2 基线比较
- 主要基线：具有24K标记预算的LongCoT-RL
- 附加基线：具有8K预算的LongCoT-RL

### 4.3 训练设置
- 每个RL步骤为128个提示采样8个轨迹
- 训练1000步，禁用KL惩罚(β=0)
- Delethink参数：C=8K，m=4K，I=5
- 在8×H100 GPU上训练

## 5. 实验结果

### 5.1 性能比较

**表1：任务性能比较**
| 方法 | AIME24 | AIME25 | HMMT25 | GPQA-Diamond | LiveCodeBench |
|------|---------|---------|---------|---------------|---------------|
| Delethink 24K | 0.33 | 0.28 | 0.25 | 0.35 | 0.21 |
| LongCoT-RL 24K | 0.30 | 0.25 | 0.23 | 0.34 | 0.20 |
| LongCoT-RL 8K | 0.25 | 0.21 | 0.18 | 0.30 | 0.17 |

**数据分析：**
- Delethink 24K在所有数学基准上优于LongCoT-RL 24K
- 在分布外任务上，Delethink仍然匹配或略微超越LongCoT-RL 24K
- LongCoT-RL 8K consistently表现较差，强调了扩展推理标记的必要性

### 5.2 测试时扩展

**表2：计算成本比较**
| 方法 | 平均思考长度 | H100月数 |
|------|-------------|-----------|
| LongCoT-RL | 96K | 27 |
| Delethink | 96K | 7 |

**数据分析：**
- Delethink实现了3.85倍的计算效率提升
- 在训练时限制之外，Delethink继续改进，而LongCoT达到平台期
- 吞吐量分析显示Delethink保持恒定吞吐量，而LongCoT随思考长度增加而下降

### 5.3 扩展至96K
- Delethink 96K仅用150个RL步骤就超越了Delethink 24K检查点的性能
- 平均思考长度达到36K(AIME'24)和42K(AIME'25)标记
- 证明了Delethink可以扩展到非常长的推理轨迹

## 6. 核心结论
1. 马尔可夫思考范式成功地将思考长度与上下文大小解耦，实现了线性计算和恒定内存
2. Delethink在保持推理质量的同时显著降低了计算成本
3. 现成的推理LLM在RL初始化时已经表现出马尔可夫跟踪能力，为有效训练提供了有利起点
4. 该方法可以扩展到接近10万标记的思考预算，为高效、可扩展的推理LLM开辟了道路

## 7. 创新点
1. **范式创新**：首次提出马尔可夫思考范式，从根本上重新思考RL推理环境设计
2. **计算效率**：将计算复杂度从二次降为线性，内存使用保持恒定
3. **实用方法**：提出的Delethink方法简单有效，可在现有基础设施上立即实现
4. **扩展性证明**：证明了该方法可以扩展到极长的推理轨迹

## 8. 局限性
1. **状态大小依赖**：性能在一定程度上依赖于选择的块大小和状态大小
2. **任务特定性**：在需要实时记忆的任务(如填字游戏)上表现有一定限制
3. **初始化要求**：依赖于基础模型已经具备一定的马尔可夫推理能力
4. **架构限制**：当前实现仍然基于Transformer架构，未充分利用非二次序列架构的潜力

## 9. 参考文献

| 作者 | 标题 | 年份 | 会议/期刊 | 来源链接 |
|------|------|------|-----------|-----------|
| Agarwal et al. | gpt-oss-120b & gpt-oss-20b model card | 2025 | ArXiv preprint | https://arxiv.org/abs/2508.10925 |
| Aggarwal & Welleck | L1: Controlling how long a reasoning model thinks with reinforcement learning | 2025 | ArXiv preprint | https://arxiv.org/abs/2503.04697 |
| AI21 Labs | Jamba-1.5: Hybrid transformer-mamba models at scale | 2024 | ArXiv preprint | https://arxiv.org/abs/2408.12570 |
| Beltagy et al. | Longformer: The long-document transformer | 2020 | ArXiv preprint | https://arxiv.org/abs/2004.05150 |
| Guo et al. | Deepseek-r1: Incentivizing reasoning capability in llms via reinforcement learning | 2025 | ArXiv preprint | https://arxiv.org/abs/2501.12948 |
| Katharopoulos et al. | Transformers are rnns: Fast autoregressive transformers with linear attention | 2020 | ICML | http://proceedings.mlr.press/v119/katharopoulos20a.html |
| Luo et al. | Deepscaler: Surpassing o1-preview with a 1.5b model by scaling rl | 2025 | Notion Blog | https://pretty-radio-b75.notion.site/DeepScaleR-Surpassing-O1-Preview-with-a-1-5B-Model-by-Scaling-RL |
| Yang et al. | Qwen3 technical report | 2025 | ArXiv preprint | https://arxiv.org/abs/2505.09388 |
| Zheng et al. | Sglang: Efficient execution of structured language model programs | 2024 | NeurIPS | http://papers.nips.cc/paper_files/paper/2024/hash/724be4472168f31ba1c9ac630f15dec8-Abstract-Conference.html |