"""Deterministic sha256 config_hash.

Invariant: same field values → same hex digest, regardless of Python version
patch, process, or dict insertion order.

Decimal → str(v)       avoids IEEE-754 repr drift ("0.1" never becomes "0.1000...01")
sort_keys=True         eliminates dict-order sensitivity
ensure_ascii=True      canonical escaping across locales
None → JSON null       consistent serialisation of unset owner slots
"""

from __future__ import annotations
import hashlib
import json
from dataclasses import asdict
from decimal import Decimal


def _canonical_value(v: object) -> object:
    if isinstance(v, Decimal):
        # normalize() collapses trailing zeros: Decimal("2.0").normalize() == Decimal("2")
        # so Decimal("2") and Decimal("2.0") produce the same string "2" regardless
        # of whether the YAML source was written as 2 or 2.0.
        return str(v.normalize())
    return v  # str, int, bool, None — all stable in JSON


def config_hash(cfg) -> str:
    """Return the sha256 hex digest of the canonical JSON of *cfg*."""
    raw = {k: _canonical_value(v) for k, v in asdict(cfg).items()}
    canonical = json.dumps(raw, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()
