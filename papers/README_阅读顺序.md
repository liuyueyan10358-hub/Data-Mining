# 论文阅读顺序

先精读 DLinear，其余按任务选读；不需要先读完全部论文才能开始复现。
页码指本目录PDF的物理页序号。文件是作者公开的 arXiv 版本，未修改正文。

## DLinear / LTSF-Linear
- 原文：[Are Transformers Effective for Time Series Forecasting?](https://arxiv.org/abs/2205.13504v3)
- 本地文件：[01_DLinear_2023_2205.13504v3.pdf](01_DLinear_2023_2205.13504v3.pdf)
- 阅读安排：必读：PDF第1-4页方法，第5-8页实验与分析。

## Informer
- 原文：[Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting](https://arxiv.org/abs/2012.07436v3)
- 本地文件：[02_Informer_2021_2012.07436v3.pdf](02_Informer_2021_2012.07436v3.pdf)
- 阅读安排：选读：PDF第1页背景，第5-6页实验与ETT介绍。

## FEDformer
- 原文：[FEDformer: Frequency Enhanced Decomposed Transformer for Long-term Series Forecasting](https://arxiv.org/abs/2201.12740v3)
- 本地文件：[03_FEDformer_2022_2201.12740v3.pdf](03_FEDformer_2022_2201.12740v3.pdf)
- 阅读安排：改进前重点选读：PDF第2-4页分解与专家融合。

## N-HiTS
- 原文：[N-HiTS: Neural Hierarchical Interpolation for Time Series Forecasting](https://arxiv.org/abs/2201.12886v6)
- 本地文件：[04_NHiTS_2023_2201.12886v6.pdf](04_NHiTS_2023_2201.12886v6.pdf)
- 阅读安排：进阶选读：PDF第3-4页方法，第6-7页展示与消融。

## 阅读时记录什么
- 原论文解决的问题与核心假设。
- 模型输入、输出、数据划分和评价尺度。
- 可借鉴的思想，以及与我们方案的具体差异。
- 论文结论的适用条件与局限。

FEDformer 已有多窗口趋势提取与融合机制，因此多尺度本身不是可直接宣称的原创点。
这四篇是围绕当前学习目标挑选的起始文献，不是完整或最新的领域综述。
