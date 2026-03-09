from __future__ import annotations

import os
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version


def get_app_version() -> str:
    """
    Resolve the running backend version.

    Priority:
    1) GURUPIX_BACKEND_VERSION env var (useful in containers/CI)
    2) Installed package version for "gurupix-backend"
    3) Fallback static default (matches pyproject version)
    """
    env_version = os.getenv("GURUPIX_BACKEND_VERSION")
    if env_version:
        return env_version

    try:
        return pkg_version("gurupix-backend")
    except PackageNotFoundError:
        # Fallback for local runs without an installed package
        return "0.1.0"
