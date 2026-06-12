from pathlib import Path

from lsb.data.config import (
    canonical_yaml,
    config_hash,
    get_or_create_config_version,
    load_config,
)

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


def test_identical_configs_hash_identically():
    a = load_config(CONFIG_DIR / "EURUSD.yaml")
    b = load_config(CONFIG_DIR / "EURUSD.yaml")
    assert config_hash(a) == config_hash(b)


def test_different_configs_hash_differently():
    eurusd = load_config(CONFIG_DIR / "EURUSD.yaml")
    boom500 = load_config(CONFIG_DIR / "BOOM500.yaml")
    assert config_hash(eurusd) != config_hash(boom500)


def test_config_hash_is_sha256_hex():
    config = load_config(CONFIG_DIR / "EURUSD.yaml")
    h = config_hash(config)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_insert_or_get_is_idempotent(db_conn):
    config = load_config(CONFIG_DIR / "EURUSD.yaml")

    h1 = get_or_create_config_version(db_conn, config)
    h2 = get_or_create_config_version(db_conn, config)

    assert h1 == h2 == config_hash(config)

    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT instrument, canonical_yaml FROM config_version WHERE config_hash = %s",
            (h1,),
        )
        rows = cur.fetchall()

    assert len(rows) == 1
    instrument, stored_yaml = rows[0]
    assert instrument == config.instrument
    assert stored_yaml == canonical_yaml(config)
