"""Embedding similarity evaluator using cosine similarity.

Compares agent output embeddings against expected output embeddings
to produce a similarity score.
"""

from __future__ import annotations

import logging
import math

import aiohttp

from agentprobe.core.exceptions import EvaluatorError
from agentprobe.core.models import EvalResult, EvalVerdict, TestCase, Trace
from agentprobe.eval.base import BaseEvaluator

logger = logging.getLogger(__name__)


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        vec_a: First vector.
        vec_b: Second vector.

    Returns:
        Cosine similarity score in [-1.0, 1.0].

    Raises:
        ValueError: If vectors have different lengths or are empty.
    """
    if len(vec_a) != len(vec_b):
        msg = f"Vector length mismatch: {len(vec_a)} vs {len(vec_b)}"
        raise ValueError(msg)

    if len(vec_a) == 0:
        msg = "Cannot compute similarity of empty vectors"
        raise ValueError(msg)

    dot = sum(a * b for a, b in zip(vec_a, vec_b, strict=True))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot / (norm_a * norm_b)


class EmbeddingSimilarityEvaluator(BaseEvaluator):
    """Evaluator that compares embeddings via cosine similarity.

    Obtains embeddings for expected and actual outputs from an
    embedding API, then computes cosine similarity. A threshold
    determines pass/fail.

    Attributes:
        model: Embedding model identifier.
        provider: API provider ('openai').
        threshold: Minimum similarity score to pass.
    """

    def __init__(
        self,
        *,
        model: str = "text-embedding-3-small",
        provider: str = "openai",
        api_key: str | None = None,
        threshold: float = 0.8,
        name: str = "embedding-similarity",
    ) -> None:
        """Initialize the embedding similarity evaluator.

        Args:
            model: Embedding model name.
            provider: API provider.
            api_key: API key. Read from environment if None.
            threshold: Minimum similarity to pass.
            name: Evaluator name.
        """
        super().__init__(name)
        self.model = model
        self.provider = provider
        self._api_key = api_key
        self.threshold = threshold
        self._cache: dict[str, list[float]] = {}

    async def _evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        """Compare embeddings of expected and actual output.

        Args:
            test_case: Test case with expected output.
            trace: Execution trace with actual output.

        Returns:
            Evaluation result based on cosine similarity.
        """
        if not test_case.expected_output:
            return EvalResult(
                evaluator_name=self.name,
                verdict=EvalVerdict.PASS,
                score=1.0,
                reason="No expected output — skip embedding comparison",
            )

        expected_emb = await self._get_embedding(test_case.expected_output)
        actual_emb = await self._get_embedding(trace.output_text)

        similarity = cosine_similarity(expected_emb, actual_emb)
        score = max(0.0, min(1.0, similarity))

        if score >= self.threshold:
            verdict = EvalVerdict.PASS
        elif score >= self.threshold * 0.75:
            verdict = EvalVerdict.PARTIAL
        else:
            verdict = EvalVerdict.FAIL

        return EvalResult(
            evaluator_name=self.name,
            verdict=verdict,
            score=score,
            reason=f"Cosine similarity: {similarity:.4f} (threshold: {self.threshold})",
            metadata={"similarity": similarity, "threshold": self.threshold},
        )

    async def _get_embedding(self, text: str) -> list[float]:
        """Get the embedding for a text string, using cache.

        Args:
            text: The text to embed.

        Returns:
            Embedding vector.
        """
        if text in self._cache:
            return self._cache[text]

        embedding = await self._call_embedding_api(text)
        self._cache[text] = embedding
        return embedding

    async def _call_embedding_api(self, text: str) -> list[float]:  # pragma: no cover
        """Call the embedding API.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector.

        Raises:
            EvaluatorError: If the API call fails.
        """
        import os

        api_key = self._api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise EvaluatorError("OPENAI_API_KEY not set for embedding API")

        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self.model, "input": text}

        _http_ok = 200
        async with (
            aiohttp.ClientSession() as session,
            session.post(url, json=payload, headers=headers) as resp,
        ):
            if resp.status != _http_ok:
                body = await resp.text()
                raise EvaluatorError(f"Embedding API error: {resp.status} — {body}")
            data = await resp.json()
            embedding: list[float] = data["data"][0]["embedding"]
            return embedding
