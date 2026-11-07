"""Apply SQL migrations in supabase/migrations/ using DIRECT_URL from .env."""

from __future__ import annotations

import os
import pathlib
import sys


def load_dotenv_file(env_path: pathlib.Path) -> None:
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def main() -> int:
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    load_dotenv_file(repo_root / ".env")
    load_dotenv_file(repo_root.parent / ".env")

    direct_url = os.environ.get("DIRECT_URL") or os.environ.get("DATABASE_URL")
    if not direct_url or "[YOUR-PASSWORD]" in direct_url:
        print(
            "[ERROR] Please replace [YOUR-PASSWORD] in DIRECT_URL inside .env before running migrations.",
            file=sys.stderr,
        )
        return 1

    try:
        import psycopg
    except ImportError:
        print("[ERROR] psycopg is required: pip install 'psycopg[binary]'", file=sys.stderr)
        return 1

    migrations_dir = pathlib.Path(__file__).resolve().parent / "migrations"
    sql_files = sorted(migrations_dir.glob("*.sql"))
    if not sql_files:
        print("[WARN] No migration files found in supabase/migrations/")
        return 0

    with psycopg.connect(direct_url, autocommit=False) as conn:
        for sql_file in sql_files:
            print(f"Applying {sql_file.name}...")
            sql_text = sql_file.read_text(encoding="utf-8")
            with conn.cursor() as cur:
                cur.execute(sql_text)
            conn.commit()
            print(f"[OK] Applied {sql_file.name}")

    print("All Supabase PostgreSQL >= 15 migrations applied successfully!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

