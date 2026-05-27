"""Test configuration ensuring local sources are importable."""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if SRC_PATH.exists():
    sys.path.insert(0, str(SRC_PATH))


def pytest_collection_modifyitems(config, items):
    offline_files = {
        "test_utils.py",
        "test_nodeslist_cache.py",
    }

    for item in items:
        module_path = item.fspath
        if module_path:
            filename = Path(module_path).name

            is_offline = filename in offline_files

            if not is_offline:
                item.add_marker(pytest.mark.network)
