"""Test discovery: finds and loads test modules with @scenario decorators.

Scans directories for Python files matching test patterns, imports them,
and extracts registered test cases.
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
from pathlib import Path

from agentprobe.core.models import TestCase
from agentprobe.core.scenario import get_scenarios

logger = logging.getLogger(__name__)


def discover_test_files(
    test_dir: str | Path,
    pattern: str = "test_*.py",
) -> list[Path]:
    """Find test files matching a pattern in the given directory.

    Args:
        test_dir: Root directory to search.
        pattern: Glob pattern for test files.

    Returns:
        Sorted list of matching file paths.
    """
    test_path = Path(test_dir)
    if not test_path.is_dir():
        logger.warning("Test directory does not exist: %s", test_path)
        return []

    files = sorted(test_path.rglob(pattern))
    logger.info("Discovered %d test files in %s", len(files), test_path)
    return files


def load_test_module(file_path: Path) -> str:
    """Import a test module from a file path.

    Uses importlib to load the module with a unique name derived
    from the file path. The module is registered in ``sys.modules``.

    Args:
        file_path: Path to the Python test file.

    Returns:
        The module name used for registration.

    Raises:
        ImportError: If the module cannot be loaded.
    """
    module_name = f"agentprobe_tests.{file_path.stem}_{id(file_path)}"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        msg = f"Cannot create module spec for {file_path}"
        raise ImportError(msg)

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        del sys.modules[module_name]
        raise ImportError(f"Failed to load {file_path}: {exc}") from exc

    logger.debug("Loaded test module: %s from %s", module_name, file_path)
    return module_name


def extract_test_cases(
    test_dir: str | Path,
    pattern: str = "test_*.py",
) -> list[TestCase]:
    """Discover and extract all test cases from a directory.

    Finds test files, imports them (triggering @scenario registration),
    then collects all registered test cases.

    Args:
        test_dir: Root directory to search.
        pattern: Glob pattern for test files.

    Returns:
        List of all discovered TestCase objects.
    """
    files = discover_test_files(test_dir, pattern)
    module_names: list[str] = []

    for file_path in files:
        try:
            name = load_test_module(file_path)
            module_names.append(name)
        except ImportError:
            logger.exception("Skipping unloadable file: %s", file_path)

    all_cases: list[TestCase] = []
    for module_name in module_names:
        cases = get_scenarios(module_name)
        all_cases.extend(cases)

    logger.info("Extracted %d test cases from %d modules", len(all_cases), len(module_names))
    return all_cases
