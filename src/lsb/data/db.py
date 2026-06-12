"""Database connection helper and migration runner.

Connection parameters come from LSB_DB_* environment variables, falling
back to local dev defaults (see .env.example).
"""

import os
from pathlib import Path

import psycopg2
import psycopg2.extensions

MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "migrations"


def get_connection() -> psycopg2.extensions.connection:
    return psycopg2.connect(
        host=os.environ.get("LSB_DB_HOST", "localhost"),
        port=os.environ.get("LSB_DB_PORT", "5432"),
        dbname=os.environ.get("LSB_DB_NAME", "lsb_dev"),
        user=os.environ.get("LSB_DB_USER", "lsb"),
        password=os.environ.get("LSB_DB_PASSWORD", "lsb_dev_password"),
    )


def _applied_migrations(conn) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT to_regclass('public.schema_migrations') IS NOT NULL")
        (exists,) = cur.fetchone()
        if not exists:
            return set()
        cur.execute("SELECT filename FROM schema_migrations")
        return {row[0] for row in cur.fetchall()}


def apply_migrations(conn, migrations_dir: Path = MIGRATIONS_DIR) -> list[str]:
    """Apply any migrations/*.sql files not yet recorded in schema_migrations.

    Returns the list of filenames applied (empty if already up to date).
    """
    already = _applied_migrations(conn)
    pending = sorted(p for p in migrations_dir.glob("*.sql") if p.name not in already)
    for path in pending:
        sql = path.read_text(encoding="utf-8")
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "INSERT INTO schema_migrations (filename) VALUES (%s)", (path.name,)
            )
        conn.commit()
    return [p.name for p in pending]
