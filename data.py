"""Load public series and keep each forecast target within its assigned split."""

import gzip
import hashlib

import numpy as np

SAMPLING = {'etth1': 'h', 'etth2': 'h', 'ettm1': '15min', 'ettm2': '15min', 'electricity': 'h'}
PERIOD = {'h': 24, '15min': 96}


def load_series(name, path):
    if name == 'electricity':
        open_text = gzip.open if path.suffix == '.gz' else open
        with open_text(path, 'rt', encoding='utf-8') as handle:
            values = np.loadtxt(handle, delimiter=',', dtype=np.float64, ndmin=2)
    else:
        import pandas as pd

        frame = pd.read_csv(path)
        columns = [column for column in frame.columns if column != 'date']
        values = frame[columns].to_numpy(np.float64)
    if not values.size or not np.isfinite(values).all():
        raise ValueError('Expected a nonempty series with only finite numeric observations.')
    return values


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def split_bounds(n):
    n_train = int(n * 0.7)
    n_test = int(n * 0.2)
    return n_train, n - n_train - n_test, n_test


def standardize(x, n_train):
    mu = x[:n_train].mean(0)
    sd = x[:n_train].std(0) + 1e-8
    return (x - mu) / sd


def starts(length, horizon, bounds):
    n_train, n_val, n_test = bounds
    val_end = n_train + n_val
    return {
        'train': np.arange(0, n_train - length - horizon + 1),
        'val': np.arange(max(0, n_train - length), val_end - length - horizon + 1),
        'test': np.arange(max(0, val_end - length), val_end + n_test - length - horizon + 1),
    }
