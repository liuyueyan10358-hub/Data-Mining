"""第1课加练：把趋势和残差分开，再检查它们能否还原观测值。"""

import argparse
import json
from pathlib import Path

from lesson01 import generate_series, moving_average, save_chart


def decompose(values, window):
    """本练习使用向后看的滑动平均，边界处理与原版DLinear不同。"""
    trend = moving_average(values, window)
    residual = []
    reconstructed = []
    for index in range(len(values)):
        if trend[index] is None:
            residual.append(None)
            reconstructed.append(None)
        else:
            residual.append(values[index] - trend[index])
            reconstructed.append(trend[index] + residual[index])
    return trend, residual, reconstructed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--window', type=int, default=49)
    args = parser.parse_args()
    if not 1 <= args.window <= 120:
        parser.error('本练习的窗口大小应在1到120之间')

    values = generate_series()
    trend, residual, reconstructed = decompose(values, args.window)
    output = Path(__file__).resolve().parent / 'outputs'
    output.mkdir(exist_ok=True)
    visible = range(120, 240)
    save_chart(output / '03_trend.svg', 'Observed data and estimated trend', [
        ('Observed temperature', '#9ba7af', [(i, values[i]) for i in visible]),
        (f'Trailing mean ({args.window} h)', '#bd681e', [(i, trend[i]) for i in visible]),
    ], (120, 239))
    save_chart(output / '04_residual.svg', 'Residual = observed data - estimated trend', [
        ('Residual', '#147d92', [(i, residual[i]) for i in visible]),
        ('Zero reference', '#9ba7af', [(i, 0) for i in visible]),
    ], (120, 239), y_label='Residual (C)')

    errors = [abs(values[i] - reconstructed[i]) for i in range(len(values)) if reconstructed[i] is not None]
    max_error = max(errors)
    # 检查分解没有丢失已知数据，不评价任何未来预测能力。
    if max_error > 1e-10:
        raise RuntimeError('趋势与残差未能正确还原观测值，请检查实现')
    summary = {
        'data_type': 'synthetic; decomposition only; no model trained',
        'window': args.window,
        'moving_average_type': 'trailing; differs from DLinear centered smoothing',
        'complete_points': len(errors),
        'reconstruction_max_error': max_error,
        'interpretation': 'Near-zero reconstruction error verifies decomposition algebra, not forecasting accuracy.',
    }
    (output / 'lesson01b_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('第1课加练：分解与重构（模拟数据；未训练模型）')
    print(f'平均窗口：{args.window}小时')
    print(f'完整分解点数：{len(errors)}；最大重构误差：{max_error:.3g}')
    print('请打开03_trend.svg与04_residual.svg，观察趋势和残差。')
    print('重构正确不等于未来预测准确。')


if __name__ == '__main__':
    main()
