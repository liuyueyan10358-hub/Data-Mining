# PB-DLinear 实验复现

用于比较 DLinear、逐变量频带融合和日周期模板的多变量时间序列预测实验。代码提供统一的数据划分、训练、验证集选模和测试集评价流程，支持 ETTh1、ETTh2、ETTm1、ETTm2 与 Electricity。

## 文件说明

| 文件 | 功能 |
| --- | --- |
| `data.py` | 数据读取、SHA-256 校验、时间划分、训练集统计量标准化和滑动窗口索引 |
| `models.py` | DLinear 共享预测头、双频带融合与加性日周期模板 |
| `train.py` | 命令行入口、训练、保存最佳模型和汇总指标 |

GitHub 仓库中这些文件位于根目录。若使用原项目中的 `pb_dlinear_repro` 文件夹，请先进入该文件夹，再执行下列命令。

## 环境准备

脚本中记录的参考环境为 Python 3.9、PyTorch 2.5.1、NumPy 1.23.5、pandas 2.0.3。可在 Python 3.9 环境中安装对应依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install torch==2.5.1 numpy==1.23.5 pandas==2.0.3
python train.py --help
```

当前实现使用 CPU，默认使用 2 个 PyTorch 计算线程；可通过 `--threads` 调整。

## 数据准备

仓库不包含数据集，需要自行下载并通过 `--data-file` 指定路径：

- ETT：从 [ETDataset / ETT-small](https://github.com/zhouhaoyi/ETDataset/tree/main/ETT-small) 获取 `ETTh1.csv`、`ETTh2.csv`、`ETTm1.csv`、`ETTm2.csv`。读取时删除 `date` 列，其余列作为数值变量。
- Electricity：从 [multivariate-time-series-data](https://github.com/laiguokun/multivariate-time-series-data) 获取 `electricity/electricity.txt.gz`。支持逗号分隔、无表头的 `.txt` 文件及其 `.gz` 压缩文件。

例如，将数据存放为：

```text
datasets/
├── ETTh1.csv
├── ETTh2.csv
├── ETTm1.csv
├── ETTm2.csv
└── electricity.txt.gz
```

输入应按时间顺序排列、等间隔采样，且所有观测值均为有限数值。代码不会自动排序、重采样或填补缺失值。周期相位根据行号计算，不解析时间戳。

## 快速运行

以 ETTh1 为例，使用默认的 336 步历史输入、96 步预测和三个随机种子：

```bash
python train.py \
  --data etth1 \
  --data-file datasets/ETTh1.csv \
  --output-root runs
```

仅运行一个种子、一个模型和一个训练轮次，检查流程能否完成：

```bash
python train.py \
  --data etth1 \
  --data-file datasets/ETTh1.csv \
  --output-root runs \
  --conditions pb_seas_add \
  --seeds 2021 \
  --epochs 1
```

该简短运行仅用于检查流程，不能替代完整实验。

## 模型与消融条件

所有模型先用窗口大小为 25 的居中移动平均提取趋势，在已知历史窗口两端重复端点填充；残差为输入减去趋势。趋势和残差分别通过线性预测头，各预测头在变量之间共享参数。

| `--conditions` | 说明 |
| --- | --- |
| `dlinear25` | 两个频带预测固定以 `0.5 / 0.5` 融合 |
| `dlinear_scale` | 保持两个频带等权，每个变量学习一个正的总尺度 |
| `dlinear_pc` | 每个变量学习两频带的 softmax 权重及正的总尺度 |
| `seas_only` | 在固定等权双频带模型上增加日周期模板；名称中的 `only` 指仅添加周期模块，并非只使用周期预测 |
| `pb_seas_add` | 逐变量频带融合，加上日周期模板 |
| `official_dlinear` | 按 DLinear 结构实现的共享头求和基线，直接相加两频带预测 |
| `seas_harmonic` | 固定等权双频带模型加全局谐波模板，禁用局部日轮廓修正 |
| `pb_seas_harmonic` | 逐变量频带融合加全局谐波模板，禁用局部日轮廓修正 |

日周期模板由可学习的 3 阶正余弦谐波和当前输入窗口的局部日轮廓修正组成。局部轮廓最多使用最近 7 天、且不超过输入窗口的历史，按 3 天半衰期加权。小时数据的一日周期为 24 步，15 分钟数据为 96 步。

默认运行表中前六项；ETTm1 / ETTm2 在预测长度为 336 时，默认额外运行后两项。可显式指定需要比较的条件：

```bash
python train.py \
  --data etth1 \
  --data-file datasets/ETTh1.csv \
  --output-root runs \
  --conditions official_dlinear dlinear25 dlinear_pc pb_seas_add
```

`official_dlinear` 表示模型结构基线，训练和数据划分仍采用本仓库的统一协议，不能据此将结果直接等同于原论文结果。

## 实验协议与默认参数

- 按时间顺序划分：训练集取 `floor(0.7 × N)` 行，测试集取 `floor(0.2 × N)` 行，其余为验证集。
- 标准化均值与标准差仅由训练集计算，标准差加 `1e-8`。
- 每个窗口的预测目标完整落在所属划分内；验证和测试输入可使用边界之前的已知历史。
- 固定输入长度 `L = 336`，预测长度由数据集默认值或 `--pred-len` 指定。
- 使用 Adam、MSE 损失，初始学习率为 `0.001`，第 4、7、10……轮开始时依次减半。
- 训练批大小为 32，不足一批的尾部样本丢弃；评价批大小为 64。
- 默认种子为 `2021 2022 2023`；同一种子的各条件使用相同的训练窗口排列。
- 每个条件按最低验证集 MSE 保存最佳模型。所有模型完成验证集选模后，再统一计算测试集 MSE 和 MAE。
- 指标在标准化空间计算，并对窗口、预测步和变量的全部元素求平均。验证与测试窗口步长固定为 1。

| `--data` | 采样间隔 | 默认预测长度 | 默认训练窗口步长 | 默认训练轮数 |
| --- | --- | ---: | ---: | ---: |
| `etth1` | 1 小时 | 96 | 4 | 10 |
| `etth2` | 1 小时 | 336 | 8 | 10 |
| `ettm1` | 15 分钟 | 336 | 16 | 10 |
| `ettm2` | 15 分钟 | 336 | 16 | 10 |
| `electricity` | 1 小时 | 96 | 8 | 8 |

`--data-file` 和 `--output-root` 为必填参数。可通过 `--pred-len`、`--stride`、`--epochs`、`--seeds`、`--conditions` 和 `--threads` 覆盖相应设置。数据必须足以构造至少一整批训练窗口，以及完整的验证和测试窗口。

## 七组数据与预测长度设置

五个数据集分别运行默认预测长度，再补充 ETTh1 的 336 步和 ETTm1 的 96 步，共七组设置：

```bash
python train.py --data etth1 --data-file datasets/ETTh1.csv --output-root runs
python train.py --data etth2 --data-file datasets/ETTh2.csv --output-root runs
python train.py --data ettm1 --data-file datasets/ETTm1.csv --output-root runs
python train.py --data ettm2 --data-file datasets/ETTm2.csv --output-root runs
python train.py --data electricity --data-file datasets/electricity.txt.gz --output-root runs
python train.py --data etth1 --data-file datasets/ETTh1.csv --output-root runs --pred-len 336
python train.py --data ettm1 --data-file datasets/ETTm1.csv --output-root runs --pred-len 96
```

## 输出与结果核对

每次运行在 `--output-root` 下创建带 UTC 时间戳的独立目录：

```text
runs/<UTC时间戳>_etth1_h96/
├── 2021_dlinear25.pth
├── 2021_pb_seas_add.pth
├── ...
└── summary.json
```

- `<seed>_<condition>.pth`：该种子和条件在验证集上最优的模型参数。
- `summary.json`：数据文件 SHA-256、划分行数、窗口数量、超参数、依赖版本，以及每个种子和条件的最佳轮次、验证 MSE、测试 MSE / MAE、参数量。
- `mean_metrics`：各条件在所选种子上的指标算术平均值。

脚本保存模型参数和汇总指标，不输出逐窗口预测值或图表。仓库当前不附实验结果；模型效果应以实际运行生成的 `summary.json` 为准。比较不同运行时，应同时核对数据哈希、划分、预测长度、训练步长、轮数、条件及种子。
