"""
Root conftest.py — ensures `Smart_Home` is importable as a package.

Tests import modules with package-qualified paths:
    from Smart_Home.tool_broker.schemas import ToolCall
    from Smart_Home.memory.structured_state import StructuredStateStore

This conftest adds the *parent* of Smart_Home/ to sys.path so that
`import Smart_Home` resolves correctly regardless of how pytest is invoked.
"""

import sys
from pathlib import Path

# Add the parent of this repo (e.g., /home/alexanderleon255) to sys.path
# so that `from Smart_Home.xxx import yyy` works.
_repo_root = Path(__file__).resolve().parent
_parent = str(_repo_root.parent)
if _parent not in sys.path:
    sys.path.insert(0, _parent)

# pytest-asyncio: auto mode so async fixtures/tests just work
pytest_plugins = ["pytest_asyncio"]

def pytest_configure(config):
    config.option.asyncio_mode = "auto"
