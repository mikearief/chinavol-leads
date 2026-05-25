#!/usr/bin/env python3
"""Create a user in AppWrite Auth and insert a local leads_users row."""

import argparse
import os
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.config import Config


def create_appwrite_user(email: str, password: str, username: str) -> str | None:
    import requests

    url = f"{Config.APPWRITE_URL}/v1/account"
    headers = {
        "X-Appwrite-Project": Config.APPWRITE_PROJECT_ID,
        "Content-Type": "application/json",
    }
    payload = {"userId": "unique()", "email": email, "password": password, "name": username}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("$id")
    except requests.exceptions.RequestException as exc:
        print(f"AppWrite error: {exc}")
        if hasattr(exc, 'response') and exc.response is not None:
            print(f"Response: {exc.response.text}")
        return None


def insert_local_user(username: str, email: str, appwrite_uid: str, role: str) -> bool:
    conn = sqlite3.connect(Config.DATABASE_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO leads_users (appwrite_uid, username, email, role, approved)
            VALUES (?, ?, ?, ?, 0)
        """, (appwrite_uid, username, email, role))
        conn.commit()
        print(f"Local user inserted: {username} (role={role}, approved=0)")
        return True
    except sqlite3.IntegrityError as exc:
        print(f"Local insert failed: {exc}")
        return False
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Create AppWrite + local user")
    parser.add_argument('username', help='Desired username')
    parser.add_argument('email', help='User email')
    parser.add_argument('password', help='User password')
    parser.add_argument('--role', default='member', choices=['member', 'admin'], help='User role')
    parser.add_argument('--skip-appwrite', action='store_true', help='Skip AppWrite creation, just insert local row')
    parser.add_argument('--appwrite-uid', default='', help='Existing AppWrite UID when skipping')
    args = parser.parse_args()

    if args.skip_appwrite:
        if not args.appwrite_uid:
            print("--appwrite-uid required when --skip-appwrite is set")
            sys.exit(1)
        uid = args.appwrite_uid
    else:
        uid = create_appwrite_user(args.email, args.password, args.username)
        if not uid:
            sys.exit(1)

    ok = insert_local_user(args.username, args.email, uid, args.role)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
