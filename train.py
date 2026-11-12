"""Reproduce the PB-DLinear comparison under strict chronological splits."""

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

import numpy as np
import torch

from data import PERIOD, SAMPLING, load_series, sha256, split_bounds, standardize, starts
from models import (HALF_LIFE_DAYS, HARMONICS, KERNEL, RECENT_DAYS,
                    BandLinear, BandLinearSeas, SharedDLinear)

L = 336
TRAIN_BATCH = 32
EVAL_BATCH = 64
LR = 1e-3
DEFAULT_CONDITIONS = (
    'dlinear25', 'dlinear_scale', 'dlinear_pc', 'seas_only', 'pb_seas_add', 'official_dlinear',
)
HARMONIC_CONDITIONS = ('seas_harmonic', 'pb_seas_harmonic')
DEFAULT_HORIZONS = {'etth1': 96, 'etth2': 336, 'ettm1': 336, 'ettm2': 336, 'electricity': 96}
DEFAULT_STRIDES = {'etth1': 4, 'etth2': 8, 'ettm1': 16, 'ettm2': 16, 'electricity': 8}


def make_batch(xs, idx, horizon, period):
    ii = torch.as_tensor(idx)
    x = xs[ii[:, None] + torch.arange(L)]
    y = xs[ii[:, None] + L + torch.arange(horizon)]
    return x, y, (ii + L) % period


def predict(model, x, phase):
    return model(x, phase) if isinstance(model, BandLinearSeas) else model(x)


def evaluate(model, xs, idx, horizon, period, *, include_mae=False):
    model.eval()
    sse = sae = 0.0
    n = 0
    with torch.no_grad():
        for i in range(0, len(idx), EVAL_BATCH):
            x, y, phase = make_batch(xs, idx[i:i + EVAL_BATCH], horizon, period)
            error = (predict(model, x, phase) - y).double()
            sse += float(error.square().sum())
            n += error.numel()
            if include_mae:
                sae += float(error.abs().sum())
    return (sse / n, sae / n) if include_mae else sse / n


def build_model(name, channels, horizon, period):
    if name == 'official_dlinear':
        return SharedDLinear(L, horizon)
    per_channel = name in ('dlinear_scale', 'dlinear_pc', 'pb_seas_add', 'pb_seas_harmonic')
    if name in ('seas_only', 'pb_seas_add', *HARMONIC_CONDITIONS):
        model = BandLinearSeas(L, horizon, channels, per_channel, period)
        if name in HARMONIC_CONDITIONS:
            model.alpha_seas.requires_grad_(False)
    else:
        model = BandLinear(L, horizon, channels, per_channel)
        if name == 'dlinear_scale':
            model.scores.requires_grad_(False)
    return model


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            'Public data sources\n'
            '  ETT CSV files: https://github.com/zhouhaoyi/ETDataset/tree/main/ETT-small\n'
            '  electricity.txt.gz: https://github.com/laiguokun/multivariate-time-series-data\n\n'
            'For the seven comparison settings, run once per dataset with its default horizon,\n'
            'then run ETTh1 with --pred-len 336 and ETTm1 with --pred-len 96.\n'
            'Verified with Python 3.9, PyTorch 2.5.1, NumPy 1.23.5 and pandas 2.0.3.'
        ),
    )
    parser.add_argument('--data', choices=SAMPLING, default='etth1')
    parser.add_argument('--data-file', type=Path, required=True)
    parser.add_argument('--output-root', type=Path, required=True)
    parser.add_argument('--pred-len', type=int, help='Forecast steps. Defaults to 96 or 336 by dataset.')
    parser.add_argument('--seeds', type=int, nargs='+', default=[2021, 2022, 2023])
    parser.add_argument('--epochs', type=int, help='Defaults to 8 for Electricity and 10 for ETT.')
    parser.add_argument('--stride', type=int, help='Training window stride. Defaults by dataset.')
    parser.add_argument('--conditions', nargs='+', choices=DEFAULT_CONDITIONS + HARMONIC_CONDITIONS)
    parser.add_argument('--threads', type=int, default=2)
    args = parser.parse_args()

    horizon = DEFAULT_HORIZONS[args.data] if args.pred_len is None else args.pred_len
    stride = DEFAULT_STRIDES[args.data] if args.stride is None else args.stride
    epochs = (8 if args.data == 'electricity' else 10) if args.epochs is None else args.epochs
    conditions = args.conditions
    if conditions is None:
        conditions = DEFAULT_CONDITIONS
        if args.data in ('ettm1', 'ettm2') and horizon == 336:
            conditions += HARMONIC_CONDITIONS
    if min(horizon, stride, epochs, args.threads) <= 0:
        parser.error('Forecast steps, stride, epochs and threads must be positive.')
    if not all(0 <= seed < 2**32 for seed in args.seeds):
        parser.error('Each seed must fit in an unsigned 32-bit integer.')
    if len(set(args.seeds)) != len(args.seeds) or len(set(conditions)) != len(conditions):
        parser.error('Seeds and conditions must be unique.')

    torch.set_num_threads(args.threads)
    sampling = SAMPLING[args.data]
    period = PERIOD[sampling]
    try:
        source_hash = sha256(args.data_file)
        series = load_series(args.data, args.data_file)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    bounds = split_bounds(len(series))
    windows = starts(L, horizon, bounds)
    tr, va, te = windows['train'][::stride], windows['val'], windows['test']
    if len(tr) < TRAIN_BATCH or len(va) == 0 or len(te) == 0:
        parser.error('Need at least one full training batch and complete validation and test windows.')
    channels = series.shape[1]
    xs = torch.as_tensor(standardize(series, bounds[0]), dtype=torch.float32)
    print(f'{args.data} C={channels} H={horizon} period={period} '
          f'train={len(tr)} val={len(va)} test={len(te)}', flush=True)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    out = args.output_root / f'{timestamp}_{args.data}_h{horizon}'
    out.mkdir(parents=True)

    results = []
    for seed in args.seeds:
        generator = torch.Generator().manual_seed(seed)
        orders = [torch.randperm(len(tr), generator=generator).numpy() for _ in range(epochs)]
        for name in conditions:
            random.seed(seed)
            np.random.seed(seed)
            torch.manual_seed(seed)
            model = build_model(name, channels, horizon, period)
            optimizer = torch.optim.Adam(model.parameters(), lr=LR)
            best_mse = float('inf')
            best_state = None
            for epoch, order in enumerate(orders, start=1):
                lr = LR * 0.5 ** ((epoch - 1) // 3)
                for group in optimizer.param_groups:
                    group['lr'] = lr
                model.train()
                for i in range(0, len(order) - TRAIN_BATCH + 1, TRAIN_BATCH):
                    batch = tr[order[i:i + TRAIN_BATCH]]
                    x, y, phase = make_batch(xs, batch, horizon, period)
                    optimizer.zero_grad()
                    loss = torch.nn.functional.mse_loss(predict(model, x, phase), y)
                    loss.backward()
                    optimizer.step()
                mse = evaluate(model, xs, va, horizon, period)
                if mse < best_mse:
                    best_mse, best_epoch = mse, epoch
                    best_state = {key: value.detach().clone() for key, value in model.state_dict().items()}
            if best_state is None:
                raise RuntimeError(f'{name} seed={seed} produced no finite validation MSE.')
            checkpoint = f'{seed}_{name}.pth'
            torch.save(best_state, out / checkpoint)
            results.append({
                'seed': seed, 'condition': name, 'val_mse': best_mse,
                'best_epoch': best_epoch, 'checkpoint': checkpoint,
                'parameters': sum(p.numel() for p in model.parameters()),
                'trainable_parameters': sum(p.numel() for p in model.parameters() if p.requires_grad),
            })
            print(f'  seed={seed} {name:17s} val={best_mse:.6f} epoch={best_epoch}', flush=True)

    # Select all checkpoints on validation MSE before evaluating the test split.
    for record in results:
        model = build_model(record['condition'], channels, horizon, period)
        state = torch.load(out / record['checkpoint'], map_location='cpu', weights_only=True)
        model.load_state_dict(state)
        mse, mae = evaluate(model, xs, te, horizon, period, include_mae=True)
        record['test_mse'], record['test_mae'] = mse, mae
        print(f'  seed={record["seed"]} {record["condition"]:17s} '
              f'test MSE={mse:.6f} MAE={mae:.6f}', flush=True)

    averages = {}
    for name in conditions:
        group = [record for record in results if record['condition'] == name]
        averages[name] = {metric: mean(record[metric] for record in group)
                          for metric in ('val_mse', 'test_mse', 'test_mae')}
    summary = {
        'protocol': 'strict_forecast_v1',
        'data': args.data, 'source_sha256': source_hash, 'sampling': sampling, 'channels': channels,
        'L': L, 'H': horizon, 'period': period, 'kernel': KERNEL,
        'split': 'ratio', 'split_rows': dict(zip(('train', 'val', 'test'), bounds)),
        'windows': {'train': len(tr), 'val': len(va), 'test': len(te)},
        'stride': stride, 'epochs': epochs, 'seeds': args.seeds,
        'conditions': list(conditions), 'harmonics': HARMONICS,
        'template_recent_days': RECENT_DAYS, 'template_half_life_days': HALF_LIFE_DAYS,
        'optimizer': 'Adam', 'lr': LR, 'lr_half_life_epochs': 3,
        'train_batch_size': TRAIN_BATCH, 'eval_batch_size': EVAL_BATCH, 'threads': args.threads,
        'checkpoint_selection': 'minimum_validation_mse',
        'torch_version': torch.__version__, 'numpy_version': np.__version__,
        'results': results, 'mean_metrics': averages,
    }
    pending = out / 'summary.json.tmp'
    with pending.open('x', encoding='utf-8') as handle:
        json.dump(summary, handle, indent=2, allow_nan=False)
        handle.write('\n')
    pending.replace(out / 'summary.json')
    print(f'Saved checkpoints and summary to {out}', flush=True)


if __name__ == '__main__':
    main()
