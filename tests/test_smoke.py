"""A0 smoke test: the package imports and exposes a version.

Keeps `pytest -q` green-on-empty before any strategy code exists. Replaced/extended
by real module tests from A1 onward.
"""

import lsb


def test_package_imports():
    assert lsb.__version__ == "0.0.0"
