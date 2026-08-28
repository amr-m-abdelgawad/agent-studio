from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.m0_exit

REPO_ROOT = Path(__file__).resolve().parents[2]
EXIT_DOC = REPO_ROOT / "tests" / "m0" / "EXIT.md"
CHECK_SCRIPT = REPO_ROOT / "tests" / "m0" / "check-m0-exit.sh"


def test_exit_doc_has_nine_bullets():
    content = EXIT_DOC.read_text(encoding="utf-8")
    bullets = [line for line in content.splitlines() if line.strip().startswith("- ")]
    assert len(bullets) == 9, f"expected 9 EXIT bullets, found {len(bullets)}"


def test_check_m0_exit_script_exists_and_is_executable():
    assert CHECK_SCRIPT.is_file()
    assert CHECK_SCRIPT.stat().st_mode & 0o111


def test_check_m0_exit_runs_successfully():
    result = subprocess.run(
        ["bash", str(CHECK_SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
