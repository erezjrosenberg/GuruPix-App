#!/usr/bin/env python3
"""
One-time cleanup: remove erez user if present.

Admin is created by migration 003. This script only removes erez.
After the first run, this is a no-op. Safe to run on every startup.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.db.models import User  # noqa: E402
from app.db.session import _get_session_factory  # noqa: E402
from sqlalchemy import delete  # noqa: E402


async def main() -> None:
    factory = _get_session_factory()
    async with factory() as db:
        await db.execute(delete(User).where(User.email == "erez@gurupix.com"))
        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())
