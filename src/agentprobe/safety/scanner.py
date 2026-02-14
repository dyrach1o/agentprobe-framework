"""Safety scanner engine: runs safety test suites against agents.

Provides the SafetyScanner orchestrator and base SafetySuite ABC
for implementing specific safety test suites (prompt injection,
data leakage, etc.).
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agentprobe.core.protocols import AdapterProtocol

logger = logging.getLogger(__name__)


class SafetySuiteResult(BaseModel):
    """Result from a single safety suite execution.

    Attributes:
        suite_name: Name of the safety suite.
        total_tests: Number of tests in the suite.
        passed: Number of tests that passed (no safety violation).
        failed: Number of tests that detected a safety issue.
        results: Detailed per-test results.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    suite_name: str
    total_tests: int = Field(default=0, ge=0)
    passed: int = Field(default=0, ge=0)
    failed: int = Field(default=0, ge=0)
    results: tuple[dict[str, Any], ...] = ()


class SafetyScanResult(BaseModel):
    """Aggregate result from all safety suites.

    Attributes:
        total_suites: Number of suites executed.
        total_tests: Total tests across all suites.
        total_passed: Tests that passed across all suites.
        total_failed: Tests that failed across all suites.
        suite_results: Per-suite results.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    total_suites: int = Field(default=0, ge=0)
    total_tests: int = Field(default=0, ge=0)
    total_passed: int = Field(default=0, ge=0)
    total_failed: int = Field(default=0, ge=0)
    suite_results: tuple[SafetySuiteResult, ...] = ()


class SafetySuite(ABC):
    """Abstract base class for safety test suites.

    Each suite implements a specific category of safety testing
    (e.g. prompt injection, data leakage, bias detection).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the suite name."""
        ...

    @abstractmethod
    async def run(self, adapter: AdapterProtocol) -> SafetySuiteResult:
        """Execute all tests in this suite against an adapter.

        Args:
            adapter: The agent adapter to test.

        Returns:
            Results from the suite execution.
        """
        ...


# Suite registry
_suite_registry: dict[str, type[SafetySuite]] = {}


def register_suite(suite_class: type[SafetySuite]) -> type[SafetySuite]:
    """Register a safety suite class in the global registry.

    Args:
        suite_class: The suite class to register.

    Returns:
        The same class (for use as a decorator).
    """
    instance = suite_class()
    _suite_registry[instance.name] = suite_class
    return suite_class


def get_registered_suites() -> dict[str, type[SafetySuite]]:
    """Return all registered safety suite classes."""
    return dict(_suite_registry)


class SafetyScanner:
    """Orchestrates safety testing by running configured suites.

    Attributes:
        suites: List of safety suite instances to run.
    """

    def __init__(self, suites: list[SafetySuite] | None = None) -> None:
        """Initialize the safety scanner.

        Args:
            suites: Safety suites to run. If None, uses an empty list.
        """
        self._suites = suites or []

    @classmethod
    def from_config(cls, suite_names: list[str]) -> SafetyScanner:
        """Create a scanner from a list of suite names.

        Looks up suite classes in the global registry.

        Args:
            suite_names: Names of suites to instantiate.

        Returns:
            A configured SafetyScanner.
        """
        suites: list[SafetySuite] = []
        for name in suite_names:
            suite_class = _suite_registry.get(name)
            if suite_class is None:
                logger.warning("Unknown safety suite: %s", name)
                continue
            suites.append(suite_class())
        return cls(suites=suites)

    async def scan(self, adapter: AdapterProtocol) -> SafetyScanResult:
        """Run all configured safety suites against an adapter.

        Args:
            adapter: The agent adapter to test.

        Returns:
            Aggregate scan results.
        """
        suite_results: list[SafetySuiteResult] = []

        for suite in self._suites:
            try:
                result = await suite.run(adapter)
                suite_results.append(result)
            except Exception:
                logger.exception("Safety suite '%s' failed", suite.name)
                suite_results.append(
                    SafetySuiteResult(
                        suite_name=suite.name,
                        total_tests=0,
                        passed=0,
                        failed=0,
                    )
                )

        total_tests = sum(r.total_tests for r in suite_results)
        total_passed = sum(r.passed for r in suite_results)
        total_failed = sum(r.failed for r in suite_results)

        return SafetyScanResult(
            total_suites=len(suite_results),
            total_tests=total_tests,
            total_passed=total_passed,
            total_failed=total_failed,
            suite_results=tuple(suite_results),
        )
