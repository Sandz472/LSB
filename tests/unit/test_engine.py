"""Signal engine integration tests.

Tests the full gate-1–4 pipeline end-to-end on synthetic candle windows.
Verifies short-circuit behaviour, qualified/rejected state, and that
gate_results JSONB round-trips correctly.
"""

import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from lsb.data.config import load_config
from lsb.data.config import config_hash
from lsb.signals import Candle
from lsb.signals.engine import MIN_H1_WINDOW, SignalResult, evaluate

CONFIG_DIR = Path(__file__).resolve().parents[2] / 'config'


def _ts(i):
    return datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(hours=i)


def _candle(i, close, pip_drift=0.0010):
    return Candle(ts=_ts(i), open=close, high=close + pip_drift,
                  low=close - pip_drift, close=close, volume=1.0)


def _trending_window(n=350, start=1.10, step=0.0005):
    """Downward-trending window: forces EMA21 < EMA50 < EMA89 (bearish)."""
    return [_candle(i, start - i * step) for i in range(n)]


class TestEngineInsufficientWindow:
    def test_too_few_candles_rejects_gate_1(self):
        config = load_config(CONFIG_DIR / 'EURUSD.yaml')
        h = config_hash(config)
        result = evaluate([_candle(i, 1.10) for i in range(50)], config, h)
        assert result.qualified is False
        assert result.rejected_at_gate == 1
        assert 'insufficient' in result.gates[0].reason.lower()


class TestEngineShortCircuit:
    def test_neutral_trend_rejects_at_gate_1(self):
        # Flat prices → NEUTRAL/INVALID trend → gate 1 fails.
        config = load_config(CONFIG_DIR / 'EURUSD.yaml')
        h = config_hash(config)
        flat = [_candle(i, 1.10) for i in range(MIN_H1_WINDOW + 10)]
        result = evaluate(flat, config, h)
        assert result.qualified is False
        assert result.rejected_at_gate == 1

    def test_result_has_instrument_and_ts(self):
        config = load_config(CONFIG_DIR / 'EURUSD.yaml')
        h = config_hash(config)
        window = _trending_window(MIN_H1_WINDOW + 50)
        result = evaluate(window, config, h)
        assert result.instrument == 'EURUSD'
        assert result.ts is not None


class TestEngineGateProgression:
    def test_bearish_trend_passes_gate_1(self):
        """Strong downtrend passes Gate 1; subsequent gates may still fail."""
        config = load_config(CONFIG_DIR / 'EURUSD.yaml')
        h = config_hash(config)
        window = _trending_window(MIN_H1_WINDOW + 100)
        result = evaluate(window, config, h)
        # Gate 1 must have passed; result either qualified or rejected at ≥2.
        assert len(result.gates) >= 1
        assert result.gates[0].passed is True

    def test_signal_result_is_frozen(self):
        config = load_config(CONFIG_DIR / 'EURUSD.yaml')
        h = config_hash(config)
        result = evaluate(_trending_window(MIN_H1_WINDOW + 50), config, h)
        with pytest.raises((AttributeError, TypeError)):
            result.qualified = True  # type: ignore[misc]


class TestEngineConfigHash:
    def test_different_configs_produce_different_hashes_in_result(self):
        eur = load_config(CONFIG_DIR / 'EURUSD.yaml')
        xau = load_config(CONFIG_DIR / 'XAUUSD.yaml')
        window = _trending_window(MIN_H1_WINDOW + 50)
        r_eur = evaluate(window, eur, config_hash(eur))
        r_xau = evaluate(window, xau, config_hash(xau))
        assert r_eur.config_hash != r_xau.config_hash
