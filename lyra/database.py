"""SQLite database setup and connection management for the Lyra marketing system."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator


DEFAULT_DB_PATH = Path.home() / ".lyra" / "marketing.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    phone       TEXT NOT NULL,
    email       TEXT NOT NULL,
    address     TEXT NOT NULL,
    city        TEXT NOT NULL,
    zip_code    TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'lead',
    notes       TEXT DEFAULT '',
    tags        TEXT DEFAULT '',
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
    last_contacted TEXT
);

CREATE TABLE IF NOT EXISTS campaigns (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    name             TEXT NOT NULL,
    subject          TEXT NOT NULL,
    body             TEXT NOT NULL,
    campaign_type    TEXT NOT NULL DEFAULT 'email',
    status           TEXT NOT NULL DEFAULT 'draft',
    target_zip_codes TEXT DEFAULT '',
    target_statuses  TEXT DEFAULT '',
    target_tags      TEXT DEFAULT '',
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    scheduled_at     TEXT,
    sent_at          TEXT
);

CREATE TABLE IF NOT EXISTS campaign_recipients (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id  INTEGER NOT NULL REFERENCES campaigns(id),
    customer_id  INTEGER NOT NULL REFERENCES customers(id),
    sent_at      TEXT,
    opened       INTEGER NOT NULL DEFAULT 0,
    clicked      INTEGER NOT NULL DEFAULT 0,
    responded    INTEGER NOT NULL DEFAULT 0,
    unsubscribed INTEGER NOT NULL DEFAULT 0,
    UNIQUE(campaign_id, customer_id)
);

CREATE INDEX IF NOT EXISTS idx_customers_status   ON customers(status);
CREATE INDEX IF NOT EXISTS idx_customers_zip      ON customers(zip_code);
CREATE INDEX IF NOT EXISTS idx_campaigns_status   ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_recipients_campaign ON campaign_recipients(campaign_id);
CREATE INDEX IF NOT EXISTS idx_recipients_customer ON campaign_recipients(customer_id);
"""


def get_db_path(db_path: str | Path | None = None) -> Path:
    """Return a resolved Path for the database file."""
    if db_path is None:
        return DEFAULT_DB_PATH
    return Path(db_path)


def init_db(db_path: str | Path | None = None) -> None:
    """Create the database and tables if they don't exist."""
    path = get_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


@contextmanager
def get_connection(db_path: str | Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Provide a database connection as a context manager."""
    path = get_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
