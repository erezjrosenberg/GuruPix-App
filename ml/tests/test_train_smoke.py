"""
Stage 0: smoke test for train.py --smoke.
Run from repo root: cd ml && pytest tests/ -v
"""
import subprocess
import sys
from pathlib import Path

# ml/tests/ -> ml/
ML_ROOT = Path(__file__).resolve().parent.parent


def test_train_smoke_exits_zero() -> None:
    """Running train.py --smoke should exit with code 0."""
    result = subprocess.run(
        [sys.executable, str(ML_ROOT / "train.py"), "--smoke"],
        cwd=ML_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
