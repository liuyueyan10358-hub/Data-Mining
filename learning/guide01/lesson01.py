"""第1课：时间序列、滑动窗口和滑动平均。只依赖Python标准库。"""

import argparse
from html import escape
import json
import math
from pathlib import Path
import random


def generate_series(length=480, seed=42):
    """模拟温度 = 缓慢趋势 + 每日波动 + 随机扰动，不代表真实ETT数据。"""
    rng = random.Random(seed)
    return [
        45 + 0.025 * hour + 4 * math.sin(2 * math.pi * hour / 24)
        + rng.gauss(0, 0.8)
        for hour in range(length)
    ]


def make_windows(values, history, horizon):
    """窗口每次移动1点；X为历史，Y为紧接其后的未来目标。"""
    if history < 1 or horizon < 1:
        raise ValueError("历史长度和预测长度必须是正整数")
    samples = []
    for start in range(len(values) - history - horizon + 1):
        boundary = start + history
        x = values[start:boundary]
        y = values[boundary:boundary + horizon]
        samples.append((x, y))
    return samples


def moving_average(values, window):
    """向后看的平均：当前值及之前window-1个值；不完整的开头返回None。"""
    if window < 1:
        raise ValueError("平均窗口必须为正整数")
    result = []
    for index in range(len(values)):
        if index + 1 < window:
            result.append(None)
        else:
            segment = values[index - window + 1:index + 1]
            result.append(sum(segment) / window)
    return result


def save_chart(path, title, series, x_domain, boundary=None, y_label='Temp. (C)',
               subtitle='Synthetic data only; no trained model or predictions',
               x_label='Hour since start', y_floor=None):
    """将少量教学数据画为独立SVG。无需安装绘图库。"""
    width, height = 940, 420
    left, top, right, bottom = 80, 82, 30, 66
    chart_w, chart_h = width - left - right, height - top - bottom
    values = [v for _, _, points in series for _, v in points if v is not None]
    y_min, y_max = min(values), max(values)
    pad = max((y_max - y_min) * 0.12, 1)
    y_min, y_max = y_min - pad, y_max + pad
    if y_floor is not None:
        y_min = max(y_min, y_floor)
    x_min, x_max = x_domain

    def sx(x):
        return left + (x - x_min) / (x_max - x_min) * chart_w

    def sy(y):
        return top + (y_max - y) / (y_max - y_min) * chart_h

    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 940 420" role="img" aria-labelledby="title desc">',
        f'<title id="title">{escape(title)}</title>',
        f'<desc id="desc">{escape(subtitle)}</desc>',
        '<rect width="940" height="420" fill="#ffffff"/>',
        '<g font-family="Arial, sans-serif" fill="#243746">',
        f'<text x="30" y="29" font-size="19">{escape(title)}</text>',
        f'<text x="30" y="50" font-size="12">{escape(subtitle)}</text>',
    ]
    for tick in range(5):
        value = y_min + (y_max - y_min) * tick / 4
        y = sy(value)
        svg += [f'<line x1="{left}" x2="{width-right}" y1="{y:.2f}" y2="{y:.2f}" stroke="#e4e9ed"/>',
                f'<text x="{left-10}" y="{y+4:.2f}" text-anchor="end" font-size="12">{value:.1f}</text>']
    for tick in range(5):
        value = x_min + (x_max - x_min) * tick / 4
        svg.append(f'<text x="{sx(value):.2f}" y="{height-bottom+24}" text-anchor="middle" font-size="12">{value:.0f}</text>')
    svg += [f'<rect x="{left}" y="{top}" width="{chart_w}" height="{chart_h}" fill="none" stroke="#b8c6cf"/>',
            f'<text x="20" y="{top+chart_h/2}" transform="rotate(-90 20 {top+chart_h/2})" text-anchor="middle" font-size="12">{escape(y_label)}</text>',
            f'<text x="{left+chart_w/2}" y="{height-14}" text-anchor="middle" font-size="13">{escape(x_label)}</text>']
    legend_x = left
    for name, color, points in series:
        svg += [f'<line x1="{legend_x}" x2="{legend_x+22}" y1="68" y2="68" stroke="{color}" stroke-width="2.5"/>',
                f'<text x="{legend_x+28}" y="72" font-size="12">{escape(name)}</text>']
        legend_x += 220
        coordinates = ' '.join(f'{sx(x):.2f},{sy(y):.2f}' for x, y in points if y is not None)
        svg.append(f'<polyline points="{coordinates}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>')
    if boundary is not None:
        pos = sx(boundary)
        svg += [f'<line x1="{pos:.2f}" x2="{pos:.2f}" y1="{top}" y2="{height-bottom}" stroke="#596d7a" stroke-dasharray="5 5"/>',
                f'<text x="{pos-7:.2f}" y="{top+18}" text-anchor="end" font-size="12">Forecast origin</text>']
    svg.append('</g></svg>')
    path.write_text('\n'.join(svg), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history', type=int, default=48, help='每个样本的历史小时数')
    parser.add_argument('--horizon', type=int, default=12, help='每个样本的未来小时数')
    parser.add_argument('--windows', type=int, nargs=2, default=[7, 25], help='比较两个滑动平均窗口')
    args = parser.parse_args()
    if args.history < 1 or args.horizon < 1 or min(args.windows) < 1:
        parser.error('所有窗口长度必须为正整数')
    # 保留较小练习规模；最短的数据段有96个点。
    if args.history + args.horizon > 96 or max(args.windows) > 120:
        parser.error('本课要求history+horizon不超过96，平均窗口不超过120')

    out = Path(__file__).resolve().parent / 'outputs'
    out.mkdir(exist_ok=True)
    series = generate_series()
    # 先按时间划分，再分别构建样本，避免把未来段的目标混入训练。
    splits = {'train': series[:288], 'validation': series[288:384], 'test': series[384:]}
    counts = {name: len(make_windows(values, args.history, args.horizon)) for name, values in splits.items()}
    averages = {window: moving_average(series, window) for window in args.windows}
    example_start = 72
    boundary = example_start + args.history
    target_end = boundary + args.horizon
    x = series[example_start:boundary]
    y = series[boundary:target_end]
    # 运行时检查：样本严格位于训练段，X与Y在时间上相邻且不重叠。
    assert target_end <= 288 and len(x) == args.history and len(y) == args.horizon
    errors = []
    for smoothed in averages.values():
        errors.extend(abs(series[i] - (v + (series[i] - v))) for i, v in enumerate(smoothed) if v is not None)

    save_chart(out / '01_input_target.svg', 'One sample: known history and future target', [
        (f'History input ({args.history} h)', '#147d92', list(enumerate(x, example_start))),
        (f'Future target ({args.horizon} h)', '#bd681e', list(enumerate(y, boundary))),
    ], (example_start, target_end - 1), boundary=boundary - 0.5)
    visible = range(120, 240)
    save_chart(out / '02_smoothing.svg', 'Moving average: responsiveness and smoothness', [
        ('Observed temperature', '#9ba7af', [(i, series[i]) for i in visible]),
        (f'Trailing mean ({args.windows[0]} h)', '#147d92', [(i, averages[args.windows[0]][i]) for i in visible]),
        (f'Trailing mean ({args.windows[1]} h)', '#bd681e', [(i, averages[args.windows[1]][i]) for i in visible]),
    ], (120, 239))
    toy = make_windows([10, 20, 30, 40, 50, 60, 70], 3, 2)
    summary = {
        'data_type': 'synthetic teaching example, not ETT; no model trained',
        'seed': 42, 'total_points': len(series), 'history': args.history, 'horizon': args.horizon,
        'average_windows': args.windows, 'split_points': {k:len(v) for k,v in splits.items()},
        'sample_counts': counts, 'toy_examples': [{'X':a, 'Y':b} for a,b in toy],
        'example_input_hours_inclusive': [example_start, boundary-1],
        'example_target_hours_inclusive': [boundary, target_end-1],
        'example_input': x, 'example_target': y,
        'reconstruction_max_error': max(errors),
    }
    (out / 'lesson01_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('第1课：认识时间序列（模拟数据；未训练模型）')
    print(f'数据：{len(series)}小时，按时间切成训练288 / 验证96 / 测试96')
    print(f'每个样本：过去{args.history}小时 → 未来{args.horizon}小时')
    print(f'各段样本数：{counts}')
    print(f'示例：输入第{example_start}-{boundary-1}小时；目标第{boundary}-{target_end-1}小时（从0计时）')
    print(f'平滑窗口：{args.windows}；结果目录：{out}')
    print('先打开两张SVG，再完成README中的三个问题。')


if __name__ == '__main__':
    main()
