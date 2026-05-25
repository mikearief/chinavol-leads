#!/usr/bin/env python3
"""Idempotently seed leads_monitors from migrations/002_seed_monitors.sql."""

import argparse
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.config import Config

SEED_SQL = os.path.join(os.path.dirname(__file__), '..', 'migrations', '002_seed_monitors.sql')
SCHEMA_SQL = os.path.join(os.path.dirname(__file__), '..', 'migrations', '001_leads_schema.sql')


def seed_monitors(db_path: str, dry_run: bool = False, check: bool = False) -> bool:
    if not os.path.exists(SEED_SQL):
        print(f"Seed file not found: {SEED_SQL}")
        return False

    with open(SEED_SQL, 'r', encoding='utf-8') as fh:
        sql = fh.read()

    if dry_run:
        print("Would execute seed SQL:")
        print(sql)
        return True

    target_db = db_path
    if check:
        if not os.path.exists(SCHEMA_SQL):
            print(f"Schema file not found: {SCHEMA_SQL}")
            return False
        temp = tempfile.NamedTemporaryFile(prefix='leads_seed_', suffix='.db')
        target_db = temp.name
    else:
        temp = None

    conn = sqlite3.connect(target_db, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    if check:
        with open(SCHEMA_SQL, 'r', encoding='utf-8') as fh:
            conn.executescript(fh.read())
    conn.executescript(sql)
    conn.commit()

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM leads_monitors")
    count = cur.fetchone()[0]
    conn.close()
    if temp is not None:
        temp.close()

    print(f"Seed complete: {count} monitors in leads_monitors")
    if check:
        print("Check mode passed.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Seed monitor data")
    parser.add_argument('--dry-run', action='store_true', help='Print SQL only')
    parser.add_argument('--check', action='store_true', help='Run and verify count')
    args = parser.parse_args()
    ok = seed_monitors(Config.DATABASE_PATH, dry_run=args.dry_run, check=args.check)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
