#!/usr/bin/env python3
"""
Seed admin + erez users for local development.

- Admin: admin@gurupix.com / admin123 (add to ADMIN_EMAILS for ingest)
- Erez:  erez@gurupix.com / erez1234 (normal user)

Usage: cd backend && PYTHONPATH=. python scripts/seed_users.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from sqlalchemy import delete

from app.db.models import User
from app.db.session import _get_session_factory
from app.services.auth import create_user


async def main() -> None:
    factory = _get_session_factory()
    async with factory() as db:
        # 1. Delete all users
        await db.execute(delete(User))
        await db.commit()

        # 2. Create admin
        admin = await create_user(db, "admin@gurupix.com", "admin123")
        print(f"Created admin: admin@gurupix.com / admin123")

        # 3. Create erez (normal user)
        erez = await create_user(db, "erez@gurupix.com", "erez1234")
        print(f"Created erez: erez@gurupix.com / erez1234")

        print("\nAdd admin@gurupix.com to ADMIN_EMAILS in .env for ingest.")


if __name__ == "__main__":
    asyncio.run(main())
