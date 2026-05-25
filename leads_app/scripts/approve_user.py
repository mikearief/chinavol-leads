#!/usr/bin/env python3
"""Approve a pending leads_users record by username."""

import argparse
import os
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.config import Config


def approve_user(username: str, approver: str = 'admin') -> bool:
    conn = sqlite3.connect(Config.DATABASE_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()
    cur.execute("""
        UPDATE leads_users
        SET approved = 1, approved_by = ?, approved_at = datetime('now')
        WHERE username = ?
    """, (approver, username))
    conn.commit()
    if cur.rowcount:
        print(f"Approved user: {username} (by {approver})")
        ok = True
    else:
        print(f"User not found: {username}")
        ok = False
    conn.close()
    return ok


def main():
    parser = argparse.ArgumentParser(description="Approve a pending leads user")
    parser.add_argument('username', help='Username to approve')
    parser.add_argument('--approver', default='admin', help='Who is approving')
    args = parser.parse_args()
    ok = approve_user(args.username, args.approver)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
