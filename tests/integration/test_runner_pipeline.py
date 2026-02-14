"""Integration test: Runner + MockAdapter + RuleBasedEvaluator + SQLiteStorage."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentprobe.core.models import RunStatus, TestCase, TestStatus
from agentprobe.core.runner import TestRunner
from agentprobe.eval.rules import RuleBasedEvaluator, RuleSpec
from agentprobe.storage.sqlite import SQLiteStorage
from tests.fixtures.agents import MockAdapter
from tests.fixtures.traces import make_llm_call


@pytest.mark.integration
class TestRunnerPipeline:
    """End-to-end: run tests, evaluate, store results."""

    @pytest.mark.asyncio
    async def test_run_with_evaluator_and_store(self, tmp_path: Path) -> None:
        """Run tests through the full pipeline and persist results."""
        adapter = MockAdapter(
            name="pipeline-agent",
            output="The answer is 42.",
            llm_calls=[make_llm_call(model="test-model", input_tokens=50, output_tokens=20)],
        )
        evaluator = RuleBasedEvaluator(
            name="pipeline-eval",
            rules=[
                RuleSpec(rule_type="contains_any", params={"values": ["42"]}),
                RuleSpec(rule_type="max_length", params={"max": 500}),
            ],
        )
        runner = TestRunner(evaluators=[evaluator])
        cases = [
            TestCase(name="test_answer", input_text="What is the meaning?"),
            TestCase(name="test_greeting", input_text="Hello!"),
        ]

        run = await runner.run(cases, adapter)

        assert run.status == RunStatus.COMPLETED
        assert run.total_tests == 2
        assert run.passed == 2
        assert adapter.call_count == 2

        # Verify eval results were attached
        for result in run.test_results:
            assert len(result.eval_results) == 1
            assert result.eval_results[0].evaluator_name == "pipeline-eval"
            assert result.score == 1.0

        # Persist to SQLite and retrieve
        storage = SQLiteStorage(db_path=tmp_path / "pipeline.db")
        await storage.setup()
        for result in run.test_results:
            await storage.save_result(result)

        loaded = await storage.load_results()
        assert len(loaded) == 2
        await storage.close()

    @pytest.mark.asyncio
    async def test_failing_evaluator_marks_test_failed(self) -> None:
        """A rule that doesn't match causes the test to fail."""
        adapter = MockAdapter(name="fail-agent", output="No relevant answer here.")
        evaluator = RuleBasedEvaluator(
            name="strict-eval",
            rules=[
                RuleSpec(
                    rule_type="contains_any",
                    params={"values": ["REQUIRED_TOKEN"]},
                    weight=1.0,
                ),
            ],
        )
        runner = TestRunner(evaluators=[evaluator])
        cases = [TestCase(name="test_strict", input_text="Say something")]

        run = await runner.run(cases, adapter)

        assert run.failed == 1
        assert run.test_results[0].status == TestStatus.FAILED
        assert run.test_results[0].score == 0.0

    @pytest.mark.asyncio
    async def test_adapter_error_produces_error_status(self) -> None:
        """An adapter that raises produces ERROR status."""
        adapter = MockAdapter(name="error-agent", error=RuntimeError("boom"))
        runner = TestRunner()
        cases = [TestCase(name="test_error", input_text="trigger error")]

        run = await runner.run(cases, adapter)

        assert run.errors == 1
        assert run.test_results[0].status == TestStatus.ERROR
        assert "boom" in (run.test_results[0].error_message or "")

    @pytest.mark.asyncio
    async def test_multiple_evaluators(self) -> None:
        """Multiple evaluators all contribute to score."""
        adapter = MockAdapter(name="multi-eval-agent", output='{"valid": true}')
        eval1 = RuleBasedEvaluator(
            name="json-eval",
            rules=[RuleSpec(rule_type="json_valid")],
        )
        eval2 = RuleBasedEvaluator(
            name="length-eval",
            rules=[RuleSpec(rule_type="max_length", params={"max": 100})],
        )
        runner = TestRunner(evaluators=[eval1, eval2])
        cases = [TestCase(name="test_multi", input_text="Respond with JSON")]

        run = await runner.run(cases, adapter)

        assert run.passed == 1
        result = run.test_results[0]
        assert len(result.eval_results) == 2
        assert result.score == 1.0
