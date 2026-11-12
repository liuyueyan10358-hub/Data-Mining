"""Two-band DLinear, per-channel fusion, and an additive daily template."""

import torch
from torch import nn
from torch.nn import functional as F

KERNEL = 25
HARMONICS = 3
RECENT_DAYS = 7
HALF_LIFE_DAYS = 3


def moving_average(x):
    pad = KERNEL // 2
    padded = torch.cat((x[:, :1].repeat(1, pad, 1), x, x[:, -1:].repeat(1, pad, 1)), dim=1)
    return F.avg_pool1d(padded.permute(0, 2, 1), KERNEL, stride=1).permute(0, 2, 1)


class SharedDLinear(nn.Module):
    """Shared-head sum baseline from the DLinear architecture (arXiv:2205.13504)."""

    def __init__(self, seq_len, pred_len):
        super().__init__()
        self.Linear_Seasonal = nn.Linear(seq_len, pred_len)
        self.Linear_Trend = nn.Linear(seq_len, pred_len)

    def forward(self, x):
        trend = moving_average(x)
        seasonal_output = self.Linear_Seasonal((x - trend).permute(0, 2, 1))
        trend_output = self.Linear_Trend(trend.permute(0, 2, 1))
        return (seasonal_output + trend_output).permute(0, 2, 1)


class BandLinear(nn.Module):
    """Each band has one affine head shared across all input variables."""

    def __init__(self, seq_len, pred_len, channels, per_channel):
        super().__init__()
        self.pred_len = pred_len
        self.channels = channels
        self.heads = nn.ModuleList(nn.Linear(seq_len, pred_len) for _ in range(2))
        self.scores = nn.Parameter(torch.zeros(channels, 2)) if per_channel else None
        self.log_scale = nn.Parameter(torch.zeros(channels)) if per_channel else None

    def fusion_weights(self, batch):
        if self.scores is None:
            return self.heads[0].weight.new_full((batch, self.channels, 2), 0.5)
        weights = torch.softmax(self.scores, -1) * torch.exp(self.log_scale).unsqueeze(-1)
        return weights.unsqueeze(0).expand(batch, -1, -1)

    def forward(self, x):
        trend = moving_average(x)
        bands = torch.stack((x - trend, trend), dim=1)
        predictions = torch.stack(
            [head(bands[:, i].permute(0, 2, 1)).permute(0, 2, 1)
             for i, head in enumerate(self.heads)],
            dim=1,
        )
        weights = self.fusion_weights(x.shape[0]).permute(0, 2, 1).unsqueeze(2)
        return (predictions * weights).sum(1)


class BandLinearSeas(BandLinear):
    """Add a global harmonic template and a window-local daily profile."""

    def __init__(self, seq_len, pred_len, channels, per_channel, period):
        super().__init__(seq_len, pred_len, channels, per_channel)
        self.period = period
        angle = (torch.arange(period).float()[:, None]
                 * torch.arange(1, HARMONICS + 1).float()[None, :] * 2 * torch.pi / period)
        self.register_buffer('basis', torch.cat((angle.cos(), angle.sin()), dim=1))
        self.q = nn.Parameter(torch.zeros(2 * HARMONICS, channels))
        self.alpha_seas = nn.Parameter(torch.zeros(channels))
        self.lam = nn.Parameter(torch.ones(channels))

    def future_template(self, x, phase):
        """phase contains the first forecast step's position within the daily cycle."""
        batch_size, length, _ = x.shape
        period = self.period
        steps = torch.arange(length, device=x.device)
        recent = min(length, RECENT_DAYS * period)
        past_idx = (phase[:, None] - length + steps[-recent:]) % period
        future_idx = (phase[:, None] + torch.arange(self.pred_len, device=x.device)) % period

        weights = torch.exp2((steps[-recent:].to(x.dtype) - (length - 1))
                             / (HALF_LIFE_DAYS * period))
        phase_weights = F.one_hot(past_idx, period).to(x.dtype) * weights[None, :, None]
        numerator = torch.bmm(phase_weights.transpose(1, 2), x[:, -recent:])
        denominator = phase_weights.sum(1).unsqueeze(-1).clamp_min(torch.finfo(x.dtype).tiny)
        profile = numerator / denominator
        correction = (profile - profile.mean(1, keepdim=True)) * torch.tanh(self.alpha_seas)
        wave = (self.basis @ self.q)[None] + correction
        batch = torch.arange(batch_size, device=x.device)[:, None]
        return wave[batch, future_idx]

    def forward(self, x, phase):
        return super().forward(x) + self.lam.view(1, 1, -1) * self.future_template(x, phase)
