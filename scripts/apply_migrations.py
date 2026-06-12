"""Apply any migrations/*.sql files not yet recorded in schema_migrations.

Usage: python scripts/apply_migrations.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lsb.data.db import apply_migrations, get_connection  # noqa: E402


def main() -> None:
    conn = get_connection()
    try:
        applied = apply_migrations(conn)
        if applied:
            for name in applied:
                print(f"Applied {name}")
        else:
            print("No pending migrations.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
