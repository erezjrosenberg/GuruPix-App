"""
Unit tests for app.core.version.get_app_version().

Covers the two key branches: env override and fallback when package is missing.
The installed-package path is exercised by the version endpoint test.
"""

from __future__ import annotations

import os
from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

from app.core.version import get_app_version


def test_get_app_version_uses_env_when_set() -> None:
    """GURUPIX_BACKEND_VERSION env var takes priority."""
    with patch.dict(os.environ, {"GURUPIX_BACKEND_VERSION": "1.2.3-env"}, clear=False):
        assert get_app_version() == "1.2.3-env"


def test_get_app_version_fallback_when_package_not_found() -> None:
    """When env is unset and package is not installed, returns fallback."""
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("GURUPIX_BACKEND_VERSION", None)
        with patch("app.core.version.pkg_version", side_effect=PackageNotFoundError("nope")):
            assert get_app_version() == "0.1.0"
