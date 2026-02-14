"""Tests for the EmbeddingSimilarityEvaluator and cosine_similarity."""

from __future__ import annotations

import math

import pytest

from agentprobe.core.models import EvalVerdict, TestCase, Trace
from agentprobe.eval.embedding import EmbeddingSimilarityEvaluator, cosine_similarity


class TestCosineSimilarity:
    """Tests for the cosine_similarity function."""

    def test_identical_vectors(self) -> None:
        result = cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
        assert result == pytest.approx(1.0)

    def test_opposite_vectors(self) -> None:
        result = cosine_similarity([1.0, 0.0], [-1.0, 0.0])
        assert result == pytest.approx(-1.0)

    def test_orthogonal_vectors(self) -> None:
        result = cosine_similarity([1.0, 0.0], [0.0, 1.0])
        assert result == pytest.approx(0.0)

    def test_zero_vector(self) -> None:
        result = cosine_similarity([0.0, 0.0], [1.0, 2.0])
        assert result == 0.0

    def test_length_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="mismatch"):
            cosine_similarity([1.0], [1.0, 2.0])

    def test_empty_vectors_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            cosine_similarity([], [])

    def test_known_similarity(self) -> None:
        a = [1.0, 2.0, 3.0]
        b = [4.0, 5.0, 6.0]
        dot = 1 * 4 + 2 * 5 + 3 * 6  # 32
        norm_a = math.sqrt(14)
        norm_b = math.sqrt(77)
        expected = dot / (norm_a * norm_b)
        result = cosine_similarity(a, b)
        assert result == pytest.approx(expected, abs=1e-6)


class TestEmbeddingSimilarityEvaluator:
    """Tests for EmbeddingSimilarityEvaluator."""

    @pytest.mark.asyncio
    async def test_no_expected_output_passes(self) -> None:
        evaluator = EmbeddingSimilarityEvaluator(api_key="test")
        tc = TestCase(name="test", input_text="x")
        trace = Trace(agent_name="test", output_text="response")
        result = await evaluator.evaluate(tc, trace)
        assert result.verdict == EvalVerdict.PASS
        assert result.score == 1.0

    @pytest.mark.asyncio
    async def test_with_cached_embeddings(self) -> None:
        evaluator = EmbeddingSimilarityEvaluator(api_key="test", threshold=0.8)
        evaluator._cache["expected text"] = [1.0, 0.0, 0.0]
        evaluator._cache["actual text"] = [0.9, 0.1, 0.0]

        tc = TestCase(name="test", input_text="x", expected_output="expected text")
        trace = Trace(agent_name="test", output_text="actual text")
        result = await evaluator.evaluate(tc, trace)
        assert result.verdict == EvalVerdict.PASS
        assert result.score > 0.9

    @pytest.mark.asyncio
    async def test_low_similarity_fails(self) -> None:
        evaluator = EmbeddingSimilarityEvaluator(api_key="test", threshold=0.9)
        evaluator._cache["good"] = [1.0, 0.0, 0.0]
        evaluator._cache["bad"] = [0.0, 1.0, 0.0]

        tc = TestCase(name="test", input_text="x", expected_output="good")
        trace = Trace(agent_name="test", output_text="bad")
        result = await evaluator.evaluate(tc, trace)
        assert result.verdict == EvalVerdict.FAIL
        assert result.score == pytest.approx(0.0, abs=0.01)

    @pytest.mark.asyncio
    async def test_partial_similarity(self) -> None:
        evaluator = EmbeddingSimilarityEvaluator(api_key="test", threshold=0.9)
        evaluator._cache["expected"] = [1.0, 1.0, 0.0]
        evaluator._cache["actual"] = [1.0, 0.0, 0.0]

        tc = TestCase(name="test", input_text="x", expected_output="expected")
        trace = Trace(agent_name="test", output_text="actual")
        result = await evaluator.evaluate(tc, trace)
        sim = cosine_similarity([1.0, 1.0, 0.0], [1.0, 0.0, 0.0])
        assert result.score == pytest.approx(sim, abs=0.01)
