from pathlib import Path
import hashlib, json, re
from xml.sax.saxutils import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from pypdf import PdfReader

ROOT = Path('/Users/yueyan_liu/Desktop/Data Mining/project')
OUT = ROOT / 'DLinear_学习路线与论文阅读指南.pdf'
pdfmetrics.registerFont(TTFont('CN', '/System/Library/Fonts/STHeiti Light.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('CNB', '/System/Library/Fonts/STHeiti Medium.ttc', subfontIndex=0))
pdfmetrics.registerFontFamily('CN', normal='CN', bold='CNB', italic='CN', boldItalic='CNB')
NAVY = colors.HexColor('#143248')
TEAL = colors.HexColor('#007E87')
INK = colors.HexColor('#263847')
GRAY = colors.HexColor('#617481')
PALE = colors.HexColor('#EEF5F6')
LINE = colors.HexColor('#D7E3E8')
ORANGE = colors.HexColor('#B26532')
WIDTH = A4[0]-88
styles = {
 'title': ParagraphStyle('title', fontName='CNB', fontSize=25, leading=34, textColor=NAVY, spaceAfter=13, wordWrap='CJK'),
 'sub': ParagraphStyle('sub', fontName='CN', fontSize=11, leading=18, textColor=GRAY, spaceAfter=12, wordWrap='CJK'),
 'h1': ParagraphStyle('h1', fontName='CNB', fontSize=20, leading=27, textColor=NAVY, spaceAfter=13, wordWrap='CJK'),
 'h2': ParagraphStyle('h2', fontName='CNB', fontSize=12.5, leading=19, textColor=TEAL, spaceBefore=12, spaceAfter=6, wordWrap='CJK', keepWithNext=True),
 'body': ParagraphStyle('body', fontName='CN', fontSize=10.5, leading=17.5, textColor=INK, spaceAfter=7, wordWrap='CJK'),
 'small': ParagraphStyle('small', fontName='CN', fontSize=9, leading=14, textColor=GRAY, spaceAfter=6, wordWrap='CJK'),
 'cell': ParagraphStyle('cell', fontName='CN', fontSize=9.3, leading=14.5, textColor=INK, wordWrap='CJK'),
 'head': ParagraphStyle('head', fontName='CNB', fontSize=9.3, leading=14.5, textColor=colors.white, wordWrap='CJK'),
 'box': ParagraphStyle('box', fontName='CN', fontSize=10.5, leading=17, textColor=NAVY, wordWrap='CJK'),
}
story=[]
def p(t, style='body'):
 story.append(Paragraph(t, styles[style]))
def h(t): p(t,'h2')
def item(n,t): p(f'<font color="#007E87"><b>{n}.</b></font>  {t}')
def box(title,text):
 t=Table([[Paragraph(f'<b>{title}</b><br/>{text}', styles['box'])]], colWidths=[WIDTH])
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('BOX',(0,0),(-1,-1),0.5,LINE),('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
 story.append(t);story.append(Spacer(1,9))
def table(headers, rows, widths):
 data=[[Paragraph(escape(x),styles['head']) for x in headers]]+[[Paragraph(x,styles['cell']) for x in r] for r in rows]
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F4F7F9')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,-1),(-1,-1),0.5,LINE)]))
 story.append(t);story.append(Spacer(1,7))
def new(num,title,subtitle):
 if story:story.append(PageBreak())
 p(f'{num}  /  学习与实践','small');p(title,'h1');p(subtitle,'sub')
def link(label,url): return f'<link href="{escape(url)}" color="#007E87">{escape(label)}</link>'

# 1
p('数据挖掘课程大作业','small')
p('DLinear 学习路线<br/>与论文阅读指南','title')
p('从理解原理到可复现实验，再到一个有证据支持的小改进。<br/>整理日期：2026-10-31  |  项目：cure-lab/LTSF-Linear','sub')
box('建议起点','默认具备基础 Python，PyTorch 经验较少。按每天约 2 小时、2-3 周安排；这是一份进度参考，达到验收标准后再进入下一阶段。')
table(['阶段 / 时间参考','核心任务','应留下的成果'],[
 ['01 基础 · 第1-2天','窗口、数据划分、线性层与训练','两份小练习；概念笔记'],
 ['02 原理 · 第3-4天','精读 DLinear；对照模型代码','模型图；3分钟原理讲解'],
 ['03 复现 · 第5-6天','ETTh1 完整训练与评价','配置、日志、指标、预测图'],
 ['04 研究 · 第7-9天','比较基准；读相关工作','误差分析；半页研究假设'],
 ['05 改进 · 第10-13天','最小改动；对比与消融','结果总表；重复运行记录'],
 ['06 表达 · 第14天起','报告、图表、PPT 与排练','报告；12分钟汇报材料'],
],[124,195,WIDTH-319])
h('把范围控制在课程项目内')
p('先做 ETTh1、一个输入长度和一个预测长度；跑通后扩展到 ETTh2 与更多预测长度。主改进先验证多尺度分解，输入相关的融合模块作为可选扩展。')
p('课程关注：完整性30%、可视化20%、创新性30%、分工与到场10%、PPT与时长10%。最多4人；报告总页数≥6、正文≥5，小四字体、1.2倍行距；最后一周汇报约12分钟，提问约3分钟。','small')
p('本指南是学习计划，不是最终提交报告；具体截止日期和提交方式仍以老师通知为准。','small')

# 2
new('02','先掌握必要基础','阶段1-2  |  学会描述问题，再理解模型')
h('先学会这五个概念')
table(['概念','用自己的话解释'],[
 ['滑动窗口','用过去 L 个观测值作为输入，后续 H 个观测值作为预测目标；窗口沿时间轴移动。'],
 ['时间划分','训练集在前、验证集居中、测试集在后；验证集用于选方案，测试集用于最终评价。'],
 ['标准化','只在训练集拟合均值和标准差，再用于验证与测试；记录指标使用的数值尺度。'],
 ['MAE / MSE','MAE 衡量平均绝对误差；MSE 对大误差更敏感，二者均为越小越好。'],
 ['PyTorch 训练','张量与维度、nn.Linear、损失函数、清空梯度、反向传播、优化器更新。'],
],[92,WIDTH-92])
h('完成两个小练习')
item('1','生成带趋势与周期的模拟序列，画原序列、滑动平均和残差；比较不同平滑窗口。')
item('2','训练一个简单线性模型，用过去24个点预测下一个点；保留训练和验证误差曲线。')
h('DLinear 的核心流程')
box('历史输入 → 分解 → 两条线性分支 → 相加预测','趋势 = MovingAverage(输入)<br/>残差 = 输入 - 趋势<br/>预测 = Linear_Trend(趋势) + Linear_Residual(残差)')
p('源码将残差分支称为 Seasonal，但它未必是纯季节成分。模型沿时间维度直接输出整个未来窗口；共享参数模式下，各变量使用相同的预测权重。[1]')
p('维度示例：输入 [B, 96, 7]，预测未来192步时输出 [B, 192, 7]。B 是每批样本数，7是数值变量数。')
box('验收标准','能解释一个样本的输入和标签；能说明未来信息泄漏是什么；能画出 DLinear 结构，并在3分钟内解释分解、线性映射和维度变化。')

# 3
new('03','跑通原项目与数据流','阶段3  |  第一轮以正确运行和保存结果为目标')
p('项目入口：'+link('GitHub · LTSF-Linear','https://github.com/cure-lab/LTSF-Linear')+'<br/>数据入口：'+link('GitHub · ETDataset','https://github.com/zhouhaoyi/ETDataset'))
table(['阅读顺序','重点检查'],[
 ['run_longExp.py','参数入口：model、seq_len、pred_len、features、enc_in，以及设备选择。'],
 ['data_provider/data_loader.py','按时间划分数据；训练集标准化；__getitem__ 如何生成窗口与标签。'],
 ['models/DLinear.py','moving_avg、series_decomp、forward；原实现固定分解窗口为25。'],
 ['exp/exp_main.py','模型注册、训练与验证、早停、预测切片、测试指标及结果保存。'],
 ['scripts/EXP-LongForecasting/','参考现有实验脚本，先复制并精简成一次运行，不批量启动全部实验。'],
],[187,WIDTH-187])
h('推荐的第一次运行')
item('1','准备隔离环境，记录 Python、PyTorch 和其他依赖版本；仓库固定了旧版 torch==1.9.0，需按机器兼容情况验证。')
item('2','检查 ETTh1.csv 的日期顺序、时间间隔、缺失与重复记录；画一周油温 OT 曲线，保存数据检查摘要。')
item('3','使用 DLinear、ETTh1、多变量输入多变量输出（M）、seq_len=96、pred_len=96、enc_in=7、batch_size=32，先用 CPU 试跑3轮。')
item('4','确认损失有限且训练正常，再完成一次正式训练；保存实际配置、日志、模型、预测与真实值。')
h('必须看懂的两个细节')
p('数据加载器返回的 seq_y 可能同时包含历史标签段和未来段。训练损失必须与真正的未来预测目标对齐；检查预测和标签切片，而不是只看 shape 相同。')
p('ETT 专用加载器有固定的训练/验证/测试边界。沿用并记录实际边界；验证/测试窗口使用边界前的历史上下文是合理的，预测目标不能进入训练。')
box('验收标准','一次完整运行成功；有 MAE/MSE 与预测曲线；知道评价的是全部7个变量还是仅OT，并能追踪一个样本如何从CSV到损失函数。')

# 4
new('04','把改进写成可检验的假设','阶段4-5  |  改动少、动机清楚、归因明确')
box('候选研究问题','固定单一平滑窗口，是否难以同时适应快变和慢变的历史片段？多尺度趋势信息能否改善某些预测长度或变化场景下的误差？这是待验证假设，不是已有结论。')
h('先读相关工作，再确定创新边界')
p('先精读 DLinear，再选读 FEDformer 的分解机制。FEDformer 已包含多窗口趋势提取与专家融合思想，因此“增加多个滑动平均窗口”本身不能宣称首次提出。[1][3]')
table(['版本','改动','应回答的问题'],[
 ['A 原版','固定窗口25的 DLinear','基准表现如何？'],
 ['B 窗口对照','尝试少量不同单尺度窗口','提升是否只是换了更合适的窗口？'],
 ['C 最小改进','多个窗口分解，先平均融合趋势，再按同样流程预测','多尺度是否优于合理调参后的单尺度？'],
 ['D 可选扩展','根据历史输入的变化特征生成融合权重','不同输入片段是否确实需要不同尺度？'],
],[78,229,WIDTH-307])
h('实现顺序与公平比较')
item('1','先固定原始模型与基准结果，再另建改进模型文件；把新增模型接入模型注册和相应训练调用路径，保留原模型可复现。')
item('2','窗口数量先控制为3个；可从7、25、49等奇数候选开始。候选仅用于验证集比较，不视为最佳设置。')
item('3','固定共享/独立参数模式。尽可能保持预测头和训练预算一致；若新增独立预测头，需报告额外参数量。')
p('数学提醒：滑动平均与线性预测的固定权重组合仍可能等价于一个线性映射，不能直接声称表达能力增强。输入相关的非线性门控可能改变这一点，但也增加过拟合风险，必须通过对照验证。')
box('验收标准','形成半页研究假设：原方法局限、相关工作、我们的具体差异、验证方法。若没有稳定提升，报告适用条件与失败原因，不挑选单次最好结果。')

# 5
new('05','让实验结果能够支持结论','阶段5  |  从最小对比逐步扩大，不一次跑满全部组合')
table(['层次','建议配置与目的'],[
 ['第一层：流程检查','ETTh1、L=96、H=96、1个种子；持久性基准、Linear、NLinear、DLinear。'],
 ['第二层：改进筛选','保持相同数据划分；比较调参后的单尺度、多尺度平均，必要时加入输入相关融合；只看验证集选方案。'],
 ['第三层：正式评价','ETTh1 / ETTh2；固定L=96，H取96、192、336；主要学习模型各用3个预定种子。算力允许时再扩展L。'],
 ['第四层：解释结果','做窗口与融合方式消融；分析不同变量、预测长度、平稳/快变片段上的误差。'],
],[112,WIDTH-112])
h('统一这六件事')
item('1','相同的数据划分、输入长度、预测长度与预测目标；各方法使用一致的评价范围。')
item('2','标准化只在训练集拟合；所有方法统一在标准化尺度报告主指标，必要时补充OT原单位指标。')
item('3','用验证集选择窗口、学习率、早停轮次；冻结方案后再汇总测试结果。')
item('4','学习率等超参数给予可比的搜索预算；记录参数量、每轮耗时、总训练耗时及运行设备。')
item('5','主要结果报告3个种子的均值与标准差；耗时区分训练、数据读取、测试与绘图。')
item('6','曲线选取规则预先固定；保存同一时间段的所有模型预测，同时展示成功与失败案例。')
h('实验记录的最小字段')
p('实验编号 / 代码版本 / 数据集 / 目标变量 / L与H / 分解窗口 / 融合方式 / 随机种子 / 学习率 / 批量大小 / 最佳轮次 / MAE / MSE / 参数量 / 耗时 / 备注。')
box('计算预算与验收','4个学习模型 × 2份数据 × 3种预测长度 × 3个种子 = 72次训练；持久性基准无需训练，窗口搜索与可选门控需另计。先测3轮耗时再安排批量实验。验收：结果可重跑，提升来源能由消融解释。')

# 6
new('06','四篇论文怎么读','按任务阅读  |  页码为本目录下载PDF的物理页序号')
p('论文原文位于 papers/，保留作者公开的 arXiv 版本。先完成[1]，其余按阶段选读；不要求复现四篇论文的全部模型。','small')
h('[1] DLinear / LTSF-Linear · 必读')
p('<b>Are Transformers Effective for Time Series Forecasting?</b><br/>Ailing Zeng 等；AAAI 2023；arXiv:2205.13504v3。')
p('重点：PDF第1-4页的问题与方法，第5-8页的比较、分析与效率；附录按需查阅。输出：三种线性模型的差异表、DLinear结构图、原实验设置摘要。')
p('文件：01_DLinear_2023_2205.13504v3.pdf<br/>'+link('原文与版本信息','https://arxiv.org/abs/2205.13504v3'),'small')
h('[2] Informer · 数据与任务背景选读')
p('<b>Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting</b><br/>Haoyi Zhou 等；AAAI 2021；arXiv:2012.07436v3。')
p('重点：PDF第1页理解长序列预测背景，第5-6页查看实验与ETT介绍。先了解任务、数据与评价，注意不同论文的实验协议未必一致；稀疏注意力推导可暂缓。输出：ETT数据来源及协议核对笔记。')
p('文件：02_Informer_2021_2012.07436v3.pdf<br/>'+link('原文与版本信息','https://arxiv.org/abs/2012.07436v3'),'small')
h('[3] FEDformer · 改进前重点选读')
p('<b>FEDformer: Frequency Enhanced Decomposed Transformer for Long-term Series Forecasting</b><br/>Tian Zhou 等；ICML 2022；arXiv:2201.12740v3。')
p('重点：PDF第2-4页的分解与专家融合机制。先追踪多个平滑窗口如何组合，频域模块可按需深入。输出：它与候选多尺度DLinear的相同点、差异和引用位置。')
p('文件：03_FEDformer_2022_2201.12740v3.pdf<br/>'+link('原文与版本信息','https://arxiv.org/abs/2201.12740v3'),'small')
h('[4] N-HiTS · 多尺度与消融设计进阶选读')
p('<b>N-HiTS: Neural Hierarchical Interpolation for Time Series Forecasting</b><br/>Cristian Challu 等；AAAI 2023；arXiv:2201.12886v6。')
p('重点：PDF第3-4页的多速率采样与分层插值，第6-7页的分解展示和消融。输出：区分多尺度平滑、采样与插值，并借鉴如何用实验解释组件作用。')
p('文件：04_NHiTS_2023_2201.12886v6.pdf<br/>'+link('原文与版本信息','https://arxiv.org/abs/2201.12886v6'),'small')

# 7
new('07','把学习成果变成报告与汇报','阶段6  |  边做边记录，最后整理叙事')
h('书面报告的建议结构')
table(['章节','应回答的问题'],[
 ['背景与相关工作','预测什么、为什么值得做？DLinear和相关多尺度方法各自解决什么？'],
 ['数据与预处理','数据来自哪里，跨度与变量如何？缺失、划分、标准化和窗口如何处理？'],
 ['原方法与改进','原模型怎样运行？改进的具体动机、结构、公式与新增开销是什么？'],
 ['实验设置与结果','基准、超参数、种子与指标是什么？主要比较和消融是否支持假设？'],
 ['分析、结论与局限','哪些场景有效或无效？提升是否稳定？下一步可以验证什么？'],
 ['分工与参考文献','每位成员完成了什么？代码、数据与论文引用是否清楚？'],
],[126,WIDTH-126])
h('优先制作四组图')
p('数据与趋势分解图；同一时间段的真实值和预测曲线；不同预测长度下的误差图；窗口/融合消融图。每张图注明数据、变量、单位或标准化尺度，图题写清比较对象。')
h('12分钟汇报的时间分配')
p('问题与数据2分钟 → 原方法2分钟 → 改进方法3分钟 → 实验与分析4分钟 → 结论与分工1分钟。另备约3分钟回答2-3个问题；排练时留出切页与讲解停顿。')
h('答辩前应能回答')
item('1','为什么需要多尺度？与FEDformer等已有方法有什么具体区别？')
item('2','比较是否公平？是否只是调参、额外参数或某个随机种子带来的提升？')
item('3','为什么有些数据或预测长度没有提升？更复杂的融合是否值得额外成本？')
box('提交前核对','报告页数、字体和行距符合课件要求；分工明确、全员到场；图表来自真实实验；代码与结果可对应；PPT不超时。以老师后续通知补充截止日期、提交方式和代码要求。')
p('说明：本计划提供学习与研究建议，不预设改进一定有效。论文原文、仓库与实际运行配置应分别引用，避免把复现贡献写成方法原创。','small')

# 8
new('08','资源索引与每日执行卡','随手查阅  |  把大任务拆成可以验收的小任务')
h('项目内文件')
p('DLinear_学习路线与论文阅读指南.pdf：本指南。<br/>papers/：四篇原始论文，按阅读顺序编号。<br/>papers/README_阅读顺序.md：论文索引、重点和来源。<br/>papers/sources.json：版本、下载地址、页数与SHA-256校验值。')
h('官方入口')
for label,url in [
 ('[5] LTSF-Linear 仓库与实验说明','https://github.com/cure-lab/LTSF-Linear'),
 ('[6] ETT 数据集与变量说明','https://github.com/zhouhaoyi/ETDataset'),
 ('[7] DLinear 核心实现','https://github.com/cure-lab/LTSF-Linear/blob/main/models/DLinear.py'),
 ('[8] 数据加载器与划分逻辑','https://github.com/cure-lab/LTSF-Linear/blob/main/data_provider/data_loader.py'),
 ('[9] 实验入口与参数','https://github.com/cure-lab/LTSF-Linear/blob/main/run_longExp.py')]:
 p(link(label,url))
h('每日执行卡：建议用10分钟收尾')
table(['字段','填写内容'],[
 ['今天只完成一件事','写清可验证动作，例如：追踪一个窗口从CSV到标签的切片。'],
 ['今天留下什么','记录笔记、图、日志或代码版本；不要只记“已学习”。'],
 ['今天确认了什么','区分原文结论、自己的观察和仍未验证的猜想。'],
 ['遇到什么问题','记录完整错误、运行配置与已尝试的方法。'],
 ['明天的第一步','拆成30-60分钟能推进的小任务。'],
],[118,WIDTH-118])
box('现在开始的最小行动','先阅读[1]的前4页，并画出“历史序列 → 趋势与残差 → 两个线性层 → 未来序列”的流程图。随后用一个短序列算一次滑动平均，再进入环境配置和首次试跑。')
p('课程要求依据：用户提供的课程要求截图。官方代码说明核对日期：2026-10-31。论文采用固定 arXiv 版本，下载清单记录在 sources.json。','small')

def chrome(canvas, doc):
 canvas.saveState(); w,h=A4
 canvas.setFillColor(TEAL); canvas.rect(44,h-30,27,3,fill=1,stroke=0)
 canvas.setFont('CN',8);canvas.setFillColor(GRAY)
 canvas.drawString(80,h-32,'DLinear / 课程项目学习指南')
 canvas.setStrokeColor(LINE);canvas.line(44,39,w-44,39)
 canvas.drawString(44,25,'学习 · 复现 · 改进 · 验证')
 canvas.drawRightString(w-44,25,f'{doc.page:02d} / 08')
 canvas.restoreState()

doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=53,bottomMargin=52,
 title='DLinear 学习路线与论文阅读指南',author='课程项目学习资料',subject='六阶段学习路径、论文导读与实验规划')
doc.build(story,onFirstPage=chrome,onLaterPages=chrome)
reader=PdfReader(OUT)
print('Created',OUT,'pages',len(reader.pages))
if len(reader.pages)!=8: raise RuntimeError('Unexpected pagination; inspect layout before delivery')

papers=[
 ('01_DLinear_2023_2205.13504v3.pdf','DLinear / LTSF-Linear','Are Transformers Effective for Time Series Forecasting?','2205.13504v3','必读：PDF第1-4页方法，第5-8页实验与分析。'),
 ('02_Informer_2021_2012.07436v3.pdf','Informer','Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting','2012.07436v3','选读：PDF第1页背景，第5-6页实验与ETT介绍。'),
 ('03_FEDformer_2022_2201.12740v3.pdf','FEDformer','FEDformer: Frequency Enhanced Decomposed Transformer for Long-term Series Forecasting','2201.12740v3','改进前重点选读：PDF第2-4页分解与专家融合。'),
 ('04_NHiTS_2023_2201.12886v6.pdf','N-HiTS','N-HiTS: Neural Hierarchical Interpolation for Time Series Forecasting','2201.12886v6','进阶选读：PDF第3-4页方法，第6-7页展示与消融。'),
]
manifest=[]; lines=['# 论文阅读顺序','','先精读 DLinear，其余按任务选读；不需要先读完全部论文才能开始复现。','页码指本目录PDF的物理页序号。文件是作者公开的 arXiv 版本，未修改正文。','']
for fn,short,title,ver,note in papers:
 f=ROOT/'papers'/fn
 r=PdfReader(f)
 manifest.append(dict(file=fn,title=title,arxiv_version=ver,source=f'https://arxiv.org/abs/{ver}',download_url=f'https://arxiv.org/pdf/{ver}',download_date='2026-10-31',pages=len(r.pages),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),reading_focus=note))
 lines.extend([f'## {short}',f'- 原文：[{title}](https://arxiv.org/abs/{ver})',f'- 本地文件：[{fn}]({fn})',f'- 阅读安排：{note}',''])
lines.extend(['## 阅读时记录什么','- 原论文解决的问题与核心假设。','- 模型输入、输出、数据划分和评价尺度。','- 可借鉴的思想，以及与我们方案的具体差异。','- 论文结论的适用条件与局限。','','FEDformer 已有多窗口趋势提取与融合机制，因此多尺度本身不是可直接宣称的原创点。','这四篇是围绕当前学习目标挑选的起始文献，不是完整或最新的领域综述。'])
(ROOT/'papers'/'sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'papers'/'README_阅读顺序.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
