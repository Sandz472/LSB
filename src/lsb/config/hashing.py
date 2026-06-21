"""Deterministic sha256 config_hash.

Invariant: same field values → same hex digest, regardless of Python version
patch, process, or dict insertion order.

Decimal → str(v.normalize())  avoids IEEE-754 repr drift
sort_keys=True                 eliminates dict-order sensitivity at every nesting level
ensure_ascii=True              canonical escaping across locales
None → JSON null               consistent serialisation of unset owner slots
class-name namespace           prevents field-name collisions across multiple cfgs
"""

from __future__ import annotations
import hashlib
import json
from dataclasses import asdict
from decimal import Decimal


def _canonical_value(v: object) -> object:
    if isinstance(v, Decimal):
        # normalize() collapses trailing zeros: Decimal("2.0").normalize() == Decimal("2")
        # so Decimal("2") and Decimal("2.0") produce the same string regardless
        # of whether the YAML source was written as 2 or 2.0.
        return str(v.normalize())
    return v  # str, int, bool, None — all stable in JSON


def config_hash(*cfgs) -> str:
    """Return sha256 of the canonical combined JSON of all *cfgs*.

    Each config is namespaced by its class name to prevent field collisions:
      config_hash(instr)        → {"InstrumentConfig": {...}}
      config_hash(instr, strat) → {"InstrumentConfig": {...}, "StrategyParams": {...}}

    sort_keys=True is applied at every nesting level by json.dumps.
    """
    combined = {
        type(cfg).__name__: {k: _canonical_value(v) for k, v in asdict(cfg).items()}
        for cfg in cfgs
    }
    canonical = json.dumps(combined, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()
