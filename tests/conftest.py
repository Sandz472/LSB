import pytest

from lsb.data.db import apply_migrations, get_connection


@pytest.fixture(scope="session")
def db_conn():
    conn = get_connection()
    apply_migrations(conn)
    yield conn
    conn.close()
