# 论文分析报告：FOGS: First-Order Gradient Supervision with Learning-based Graph for Traffic Flow Forecasting

## 1. 论文摘要
本文提出了一种新的交通流预测方法FOGS，通过基于学习的图构建和梯度监督来解决现有方法的局限性。主要贡献包括：
- 提出基于学习的时空相关图构建方法，结合道路网络和时序模式
- 引入一阶梯度监督(FOGS)，利用趋势而非具体流量值进行模型训练
- 在四个真实数据集上验证了方法的优越性

## 2. 研究背景
交通流预测是智能交通系统的核心技术，现有方法存在两个主要问题：
- 人工构建的相关图难以准确提取交通数据中的复杂模式
- 交通流数据分布不规则，使用有限训练数据容易导致欠拟合
- 大多数方法未能充分利用时序信息，仅考虑整体时间相似性

## 3. 研究方法

### 3.1 时序相关图构建
- 将一周分解为Nω个连续时间槽
- 为每个传感器构建Nω维特征向量，每个元素对应时间槽内的平均历史流量
- 基于欧氏距离构建k近邻时序相关图C = (V, E_time)

### 3.2 目标函数
使用skip-gram方法学习传感器嵌入：
```
max ∑ log Pr(N_S(v)|h(v))
h v∈V
```
其中Pr(N_S(v)|h(v)) = ∏ Pr(u|h(v))
                u∈N_S(v)

### 3.3 随机游走采样策略
定义转移概率：
```
Pr(v_j+1|τ_j) ∝ π(τ_j, v_j+1), if (v_j, v_j+1) ∈ R
```
其中π(τ_j, v_j+1)根据d_R(v_j+1)的值和(v_0, v_j+1)是否在C中确定

### 3.4 一阶梯度监督
定义趋势：
```
z_jt = (y_jt - x_jT) / x_jT, t = 1,2,...,K
```
构建时空相关图G：
- 计算相关性矩阵M(i,j) = cos(h(v_i), h(v_j))
- 基于k近邻构建图G，并进行归一化

### 3.5 模型框架
使用MAE损失函数：
```
L(Z, Ž) = ∑∑ |Z_ij - Ž_ij| / (|V|×K)
```

## 4. 实验设计

### 4.1 数据集
| 数据集 | 天数 | 传感器数 | 边数 | 数据量 |
|---------|------|----------|------|--------|
| PEMS03 | 91   | 358      | 547  | 26208  |
| PEMS04 | 59   | 307      | 340  | 16992  |
| PEMS07 | 98   | 883      | 866  | 28224  |
| PEMS08 | 62   | 170      | 295  | 17856  |

### 4.2 实验设置
- 数据分割：训练:验证:测试 = 7:1:2
- 预测设置：T = K = 12（使用1小时数据预测下1小时）
- 参数：p = q = 1, k = 10, 嵌入维度=128, L=25, Δ=10

### 4.3 基线方法
- ASTGCN：基于注意力的时空图卷积网络
- DCRNN：扩散卷积循环神经网络
- STGCN：时空图卷积网络
- STSGCN：时空同步图卷积网络
- STFGNN：时空融合图神经网络

## 5. 实验结果

### 表2：性能对比结果
| 数据集 | 指标 | ASTGCN | DCRNN | STGCN | STSGCN | STFGNN | FOGS(ours) |
|---------|-------|---------|--------|--------|---------|---------|------------|
| PEMS03 | MAE   | 18.05   | 17.86  | 17.52  | 17.17   | 16.80   | **15.06**  |
|        | MAPE  | 17.02   | 18.30  | 17.08  | 16.17   | 16.23   | **14.11**  |
|        | RMSE  | 30.13   | 29.74  | 30.23  | 28.58   | 28.44   | **24.25**  |
| PEMS04 | MAE   | 21.85   | 23.54  | 22.72  | 20.98   | 19.85   | **19.35**  |
|        | MAPE  | 14.11   | 17.18  | 14.56  | 13.73   | 12.99   | **12.71**  |
|        | RMSE  | 34.54   | 36.25  | 35.56  | 33.58   | 31.89   | **31.33**  |
| PEMS07 | MAE   | 25.22   | 23.87  | 24.58  | 23.39   | 21.51   | **20.62**  |
|        | MAPE  | 11.41   | 10.50  | 10.65  | 9.83     | 9.02     | **8.58**   |
|        | RMSE  | 38.83   | 37.27  | 37.51  | 37.79   | 35.67   | **33.96**  |
| PEMS08 | MAE   | 18.70   | 18.41  | 18.14  | 16.35   | 16.75   | **14.92**  |
|        | MAPE  | 11.64   | 12.17  | 11.38  | 10.54   | 10.58   | **9.42**   |
|        | RMSE  | 28.66   | 28.28  | 27.97  | 25.64   | 26.35   | **24.09**  |

### 表3：消融实验结果
| 数据集 | 指标 | Baseline | Graph | Trend |
|---------|-------|----------|--------|--------|
| PEMS03 | MAE   | 16.80    | 15.53  | **15.06** |
|        | MAPE  | 16.23    | 14.82  | **14.11** |
|        | RMSE  | 28.44    | 27.24  | **24.25** |
| PEMS04 | MAE   | 19.85    | 19.48  | **19.34** |
|        | MAPE  | 12.99    | 12.81  | **12.71** |
|        | RMSE  | 31.89    | 31.56  | **31.20** |

### 结果分析
- FOGS在所有数据集和指标上均优于基线方法
- 在PEMS03数据集上，FOGS相比最佳基线STFGNN在RMSE指标上提升14.73%
- 消融实验显示：学习图结构和趋势监督都能提升性能，趋势监督贡献更大
- 在道路网络更稀疏的PEMS04和PEMS07数据集上提升相对较小

## 6. 核心结论
1. 基于学习的图构建能更好地捕捉时空相关性
2. 使用趋势监督能有效解决交通流数据分布不规则的问题
3. FOGS方法在多个真实数据集上实现了最先进的性能
4. 趋势分布比流量分布更集中，提供更好的监督信息

## 7. 创新点
1. **基于学习的图构建**：结合道路网络和精细粒度时序模式
2. **一阶梯度监督**：利用趋势而非具体流量值进行训练
3. **改进的随机游走策略**：同时考虑空间邻近性和时序相似性
4. **端到端框架**：统一处理时空相关性和预测任务

## 8. 局限性
1. 在道路网络稀疏的数据集上性能提升有限
2. 缺失数据处理方法相对简单
3. 未考虑外部因素（如天气、事件）的影响
4. 计算复杂度较高，可能影响实时应用

## 9. 参考文献

| 作者 | 标题 | 年份 | 会议/期刊 | 来源 |
|-------|------|------|-----------|------|
| Bai et al. | STG2Seq: Spatial-temporal graph to sequence model for multi-step passenger demand forecasting | 2019 | IJCAI | - |
| Chen et al. | Freeway performance measurement system: Mining loop detector data | 2001 | TRR | - |
| Fang et al. | GSTNet: Global spatial-temporal network for traffic flow prediction | 2019 | IJCAI | - |
| Fang et al. | Spatial-temporal graph ODE networks for traffic flow forecasting | 2021 | KDD | - |
| Gong et al. | Potential passenger flow prediction: A novel study for urban transportation development | 2020 | AAAI | - |
| Grover et al. | node2vec: Scalable feature learning for networks | 2016 | KDD | - |
| Guo et al. | Attention based spatial-temporal graph convolutional networks for traffic flow forecasting | 2019 | AAAI | - |
| Han et al. | A graph-based approach for trajectory similarity computation in spatial networks | 2021 | KDD | - |
| He et al. | Towards fine-grained flow forecasting: A graph attention approach for bike sharing systems | 2020 | WWW | - |
| Li et al. | Diffusion convolutional recurrent neural network: Data-driven traffic forecasting | 2018 | ICLR | - |
| Li et al. | Traffic flow prediction with vehicle trajectories | 2021 | AAAI | - |
| Li et al. | Spatial-temporal fusion graph neural networks for traffic flow forecasting | 2021 | AAAI | - |
| Liu et al. | Community-aware multi-task transportation demand prediction | 2021 | AAAI | - |
| Lv et al. | Traffic flow prediction with big data: A deep learning approach | 2015 | TITS | - |
| Mikolov et al. | Distributed representations of words and phrases and their compositionality | 2013 | NIPS | - |
| Song et al. | Spatial-temporal synchronous graph convolutional networks: A new framework for spatial-temporal network data forecasting | 2020 | AAAI | - |
| Wu et al. | Short-term traffic flow forecasting with spatial-temporal correlation in a hybrid deep learning framework | 2016 | CoRR | - |
| Wu et al. | Graph wavenet for deep spatial-temporal graph modeling | 2019 | IJCAI | - |
| Yao et al. | Modeling spatial-temporal dynamics for traffic prediction | 2018 | CoRR | - |
| Yao et al. | Deep multi-view spatial-temporal network for taxi demand prediction | 2018 | AAAI | - |
| Ye et al. | Coupled layer-wise graph convolution for transportation demand prediction | 2021 | AAAI | - |
| Yu et al. | Deep learning: A generic approach for extreme condition traffic forecasting | 2017 | ICDM | - |
| Yu et al. | Spatio-temporal graph convolutional networks: A deep learning framework for traffic forecasting | 2018 | IJCAI | - |
| Zhang et al. | Deep spatio-temporal residual networks for citywide crowd flows prediction | 2017 | AAAI | - |
| Zhang et al. | Flow prediction in spatio-temporal networks based on multitask deep learning | 2020 | TKDE | - |
| Zhou et al. | Predicting multi-step citywide passenger demands using attention-based neural networks | 2018 | WSDM | - |
| Zhou et al. | Modeling heterogeneous relations across multiple modes for potential crowd flow prediction | 2021 | AAAI | - |