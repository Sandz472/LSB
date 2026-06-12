import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from audit_history import (  # noqa: E402
    check_duplicate_timestamps,
    check_dst_anomalies,
    check_gaps,
    check_spread_outliers,
    check_weekend_bars,
)


def _candles(timestamps, **overrides):
    n = len(timestamps)
    df = pd.DataFrame(
        {
            "ts": pd.to_datetime(timestamps, utc=True),
            "open": overrides.get("open", [1.0] * n),
            "high": overrides.get("high", [1.0] * n),
            "low": overrides.get("low", [1.0] * n),
            "close": overrides.get("close", [1.0] * n),
            "volume": overrides.get("volume", [1.0] * n),
            "spread": overrides.get("spread", [None] * n),
        }
    )
    return df


def _hourly_range(start, n):
    return pd.date_range(start, periods=n, freq="1h", tz="UTC")


def test_check_duplicate_timestamps_flags_repeats():
    ts = list(_hourly_range("2024-02-06 00:00", 3)) + [pd.Timestamp("2024-02-06 01:00", tz="UTC")]
    df = _candles(ts)

    anomalies = check_duplicate_timestamps(df)

    assert len(anomalies) == 1
    assert anomalies[0].id == "DUP-0001"
    assert anomalies[0].check == "duplicate_timestamp"


def test_check_duplicate_timestamps_clean():
    df = _candles(_hourly_range("2024-02-06 00:00", 4))

    assert check_duplicate_timestamps(df) == []


def test_check_gaps_flags_midweek_gap():
    # Tuesday 08:00 -> 12:00 is a 4-hour gap, well outside the FX weekend window.
    ts = list(_hourly_range("2024-02-06 06:00", 3)) + list(_hourly_range("2024-02-06 12:00", 2))
    df = _candles(ts)

    anomalies = check_gaps(df, asset_class="fx")

    assert len(anomalies) == 1
    assert anomalies[0].id == "GAP-0001"
    assert anomalies[0].check == "gap>2"
    assert anomalies[0].requires_disposition is True


def test_check_gaps_ignores_fx_weekend_closure():
    # Friday 21:00 -> Sunday 22:00: the regular FX weekend close.
    ts = [pd.Timestamp("2024-02-09 21:00", tz="UTC"), pd.Timestamp("2024-02-11 22:00", tz="UTC")]
    df = _candles(ts)

    assert check_gaps(df, asset_class="fx") == []


def test_check_gaps_flags_synthetic_weekend_gap():
    # BOOM500-style synthetic: no weekend exemption, so the same gap is flagged.
    ts = [pd.Timestamp("2024-02-09 21:00", tz="UTC"), pd.Timestamp("2024-02-11 22:00", tz="UTC")]
    df = _candles(ts)

    anomalies = check_gaps(df, asset_class="synthetic")

    assert len(anomalies) == 1
    assert anomalies[0].requires_disposition is True


def test_check_weekend_bars_flags_saturday_for_fx():
    ts = [pd.Timestamp("2024-02-10 12:00", tz="UTC")]  # Saturday
    df = _candles(ts)

    anomalies = check_weekend_bars(df, asset_class="fx")

    assert len(anomalies) == 1
    assert anomalies[0].check == "weekend_bar"


def test_check_weekend_bars_skips_synthetic():
    ts = [pd.Timestamp("2024-02-10 12:00", tz="UTC")]  # Saturday

    df = _candles(ts)

    assert check_weekend_bars(df, asset_class="synthetic") == []


def test_check_dst_anomalies_flags_short_midweek_day_near_transition():
    # Tuesday 2024-04-02, 2 days after the EU DST transition (Sun 2024-03-31), 23 candles.
    ts = list(_hourly_range("2024-04-02 00:00", 23))
    df = _candles(ts)

    anomalies = check_dst_anomalies(df, asset_class="fx")

    assert len(anomalies) == 1
    assert anomalies[0].check == "dst_anomaly"


def test_check_dst_anomalies_ignores_recurring_gap_away_from_transition():
    # Tuesday 2024-03-12, far from any DST transition, 23 candles (e.g. a
    # recurring daily settlement gap) - not a DST artifact.
    ts = list(_hourly_range("2024-03-12 00:00", 23))
    df = _candles(ts)

    assert check_dst_anomalies(df, asset_class="fx") == []


def test_check_dst_anomalies_skips_full_day():
    ts = list(_hourly_range("2024-03-12 00:00", 24))  # Tuesday, full 24h
    df = _candles(ts)

    assert check_dst_anomalies(df, asset_class="fx") == []


def test_check_spread_outliers_flags_extreme_value():
    ts = _hourly_range("2024-02-06 00:00", 8)
    spreads = [1.0, 1.1, 0.9, 1.0, 1.05, 0.95, 1.0, 50.0]
    df = _candles(ts, spread=spreads)

    anomalies = check_spread_outliers(df)

    assert len(anomalies) == 1
    assert anomalies[0].check == "spread_outlier"


def test_check_spread_outliers_noop_when_all_null():
    ts = _hourly_range("2024-02-06 00:00", 8)
    df = _candles(ts)  # spread defaults to all None

    assert check_spread_outliers(df) == []
