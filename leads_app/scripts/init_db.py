#!/usr/bin/env python3
"""Run all SQL migrations in migrations/ against DATABASE_PATH."""

import argparse
import os
import sqlite3
import sys
import tempfile

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.config import Config

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'migrations')


def run_migrations(db_path: str, dry_run: bool = False, check: bool = False) -> bool:
    migration_files = sorted(
        [f for f in os.listdir(MIGRATIONS_DIR) if f.endswith('.sql')]
    )
    if not migration_files:
        print("No migration files found.")
        return False

    if dry_run:
        print(f"Would apply {len(migration_files)} migrations to {db_path}:")
        for f in migration_files:
            print(f"  - {f}")
        return True

    if check:
        with tempfile.NamedTemporaryFile(prefix='leads_schema_', suffix='.db') as tmp:
            print(f"Checking {len(migration_files)} migrations against temporary DB: {tmp.name}")
            ok = _apply_migrations(tmp.name, migration_files)
            if ok:
                print("All migrations applied cleanly (check mode).")
            return ok

    ok = _apply_migrations(db_path, migration_files)
    if ok:
        print(f"Migrations complete: {db_path}")
    return ok


def _apply_migrations(db_path: str, migration_files: list[str]) -> bool:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    for fname in migration_files:
        with open(os.path.join(MIGRATIONS_DIR, fname), 'r', encoding='utf-8') as fh:
            sql = fh.read()
        try:
            conn.executescript(sql)
            print(f"  [OK] {fname}")
        except sqlite3.Error as exc:
            print(f"  [FAIL] {fname}: {exc}")
            conn.rollback()
            conn.close()
            return False
    conn.commit()
    conn.close()
    return True


def create_admin(db_path: str, username: str, email: str) -> None:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO leads_users (username, email, role, approved, approved_by, approved_at)
        VALUES (?, ?, 'admin', 1, 'init_script', datetime('now'))
    """, (username, email))
    if cur.rowcount:
        print(f"Admin user created: {username} ({email})")
    else:
        print(f"Admin user already exists: {username}")
    conn.commit()
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Initialize leads_app database")
    parser.add_argument('--check', action='store_true', help='Verify migrations apply cleanly')
    parser.add_argument('--dry-run', action='store_true', help='Print migrations without running')
    parser.add_argument('--create-admin', action='store_true', default=True, help='Create admin user after migrations')
    parser.add_argument('--no-create-admin', action='store_false', dest='create_admin', help='Skip admin user creation')
    parser.add_argument('--admin-username', default='mike', help='Admin username')
    parser.add_argument('--admin-email', default='mikearief@gmail.com', help='Admin email')
    args = parser.parse_args()

    db_path = Config.DATABASE_PATH
    ok = run_migrations(db_path, dry_run=args.dry_run, check=args.check)
    if not ok:
        sys.exit(1)

    if args.create_admin and not (args.dry_run or args.check):
        create_admin(db_path, args.admin_username, args.admin_email)


if __name__ == '__main__':
    main()
