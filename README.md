# DLinear 课程项目

从学习指南第1页开始，逐步完成：基础 → 原理 → 原版复现 → 改进 → 实验 → 报告。

## 现在从哪里开始

打开 [第1课：认识时间序列](learning/guide01/README.md)。这一课只观察模拟数据，不训练模型。

```bash
python3 learning/guide01/lesson01.py
```

脚本只使用 Python 标准库，不需要先安装 PyTorch、NumPy 或显卡环境。

## 资料位置

第1课基础练习之后，进入 [第2课：持久性预测基准](learning/lesson02/README.md)：

```bash
python3 learning/lesson02/lesson02.py
```

接着进入 [第3课：线性预测与参数学习](learning/lesson03/README.md)。当前练习先固定权重，只训练偏置：

```bash
python3 learning/lesson03/bias_training.py
```

当前完成情况见 [学习进度](learning/学习进度.md)。

第4课从 [PyTorch前向预测对照](learning/lesson04/README.md) 开始，在现有d2l-zh环境运行：

```bash
python3 learning/lesson04/linear_equivalence.py
```

- `DLinear_学习路线与论文阅读指南.pdf`：8页学习指南。
- `papers/`：原论文及阅读顺序。
- `learning/guide01/`：第1页路线图对应的基础入门课、练习和运行结果。
- `learning/lesson02/`：不训练模型的预测基准，以及验证集上的误差评价。
- `learning/lesson03/`：从单个偏置的更新开始，逐步学习线性模型训练。
- `learning/lesson04/`：PyTorch线性层、自动求导与原版DLinear的衔接。
- `work/`、`tmp/`：资料制作过程中使用的中间文件。

当前已完成模拟数据上的线性模型训练，正在进行PyTorch计算对照。下一阶段进入原版DLinear工程与真实ETT数据实验。
# Data-Mining
