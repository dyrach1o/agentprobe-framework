"""Judge evaluator that uses a language model to assess agent outputs.

Sends the agent's output along with a rubric to a judge model and
parses the structured JSON response into an EvalResult.
"""

from __future__ import annotations

import json
import logging

import aiohttp

from agentprobe.core.exceptions import JudgeAPIError
from agentprobe.core.models import EvalResult, EvalVerdict, TestCase, Trace
from agentprobe.eval.base import BaseEvaluator

logger = logging.getLogger(__name__)

_DEFAULT_SYSTEM_PROMPT = """\
You are an evaluation judge. Assess the agent's output against the criteria below.
Respond with ONLY a JSON object (no markdown, no explanation) in this exact format:
{
  "verdict": "pass" | "fail" | "partial",
  "score": <float 0.0-1.0>,
  "reason": "<one sentence explanation>"
}
"""


class LLMJudge(BaseEvaluator):
    """Evaluator that uses a language model as a judge.

    Calls an external model API (Anthropic or OpenAI) with the agent's
    output and a rubric, then parses the JSON verdict response.

    Attributes:
        model: The judge model identifier.
        provider: API provider ('anthropic' or 'openai').
        temperature: Sampling temperature for the judge.
        max_tokens: Maximum response tokens.
        rubric: Evaluation rubric/criteria text.
    """

    def __init__(
        self,
        *,
        model: str = "claude-sonnet-4-5-20250929",
        provider: str = "anthropic",
        api_key: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        rubric: str = "",
        name: str = "llm-judge",
    ) -> None:
        """Initialize the judge evaluator.

        Args:
            model: Judge model identifier.
            provider: API provider name.
            api_key: API key. Read from environment if None.
            temperature: Sampling temperature.
            max_tokens: Max response tokens.
            rubric: Evaluation criteria text.
            name: Evaluator name.
        """
        super().__init__(name)
        self.model = model
        self.provider = provider
        self._api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.rubric = rubric

    async def _evaluate(self, test_case: TestCase, trace: Trace) -> EvalResult:
        """Send the output to the judge model and parse the verdict.

        Args:
            test_case: The test case.
            trace: The execution trace.

        Returns:
            Parsed evaluation result from the judge.
        """
        prompt = self._build_prompt(test_case, trace)
        response_text = await self._call_api(prompt)
        return self._parse_response(response_text)

    def _build_prompt(self, test_case: TestCase, trace: Trace) -> str:
        """Build the evaluation prompt for the judge.

        Args:
            test_case: The test case with expectations.
            trace: The execution trace with the output.

        Returns:
            Formatted prompt string.
        """
        parts = [f"## Agent Input\n{test_case.input_text}"]

        if test_case.expected_output:
            parts.append(f"## Expected Output\n{test_case.expected_output}")

        parts.append(f"## Actual Output\n{trace.output_text}")

        if self.rubric:
            parts.append(f"## Evaluation Criteria\n{self.rubric}")

        return "\n\n".join(parts)

    async def _call_api(self, prompt: str) -> str:
        """Call the judge model API.

        Args:
            prompt: The evaluation prompt.

        Returns:
            Raw response text from the judge.

        Raises:
            JudgeAPIError: If the API call fails.
        """
        if self.provider == "anthropic":
            return await self._call_anthropic(prompt)
        elif self.provider == "openai":
            return await self._call_openai(prompt)
        else:
            raise JudgeAPIError(self.model, 0, f"Unknown provider: {self.provider}")

    async def _call_anthropic(self, prompt: str) -> str:  # pragma: no cover
        """Call the Anthropic Messages API.

        Args:
            prompt: The evaluation prompt.

        Returns:
            Response text.
        """
        import os

        api_key = self._api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise JudgeAPIError(self.model, 0, "ANTHROPIC_API_KEY not set")

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system": _DEFAULT_SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}],
        }

        _http_ok = 200
        async with (
            aiohttp.ClientSession() as session,
            session.post(url, json=payload, headers=headers) as resp,
        ):
            if resp.status != _http_ok:
                body = await resp.text()
                raise JudgeAPIError(self.model, resp.status, body)
            data = await resp.json()
            return str(data["content"][0]["text"])

    async def _call_openai(self, prompt: str) -> str:  # pragma: no cover
        """Call the OpenAI Chat Completions API.

        Args:
            prompt: The evaluation prompt.

        Returns:
            Response text.
        """
        import os

        api_key = self._api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise JudgeAPIError(self.model, 0, "OPENAI_API_KEY not set")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": _DEFAULT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        }

        _http_ok = 200
        async with (
            aiohttp.ClientSession() as session,
            session.post(url, json=payload, headers=headers) as resp,
        ):
            if resp.status != _http_ok:
                body = await resp.text()
                raise JudgeAPIError(self.model, resp.status, body)
            data = await resp.json()
            return str(data["choices"][0]["message"]["content"])

    def _parse_response(self, response_text: str) -> EvalResult:
        """Parse the judge's JSON response into an EvalResult.

        Args:
            response_text: Raw response text.

        Returns:
            Parsed EvalResult.
        """
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            cleaned = response_text.strip()
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    data = json.loads(cleaned[start:end])
                except json.JSONDecodeError:
                    return EvalResult(
                        evaluator_name=self.name,
                        verdict=EvalVerdict.ERROR,
                        score=0.0,
                        reason=f"Failed to parse judge response: {response_text[:200]}",
                    )
            else:
                return EvalResult(
                    evaluator_name=self.name,
                    verdict=EvalVerdict.ERROR,
                    score=0.0,
                    reason=f"No JSON found in judge response: {response_text[:200]}",
                )

        verdict_str = str(data.get("verdict", "error")).lower()
        verdict_map = {
            "pass": EvalVerdict.PASS,
            "fail": EvalVerdict.FAIL,
            "partial": EvalVerdict.PARTIAL,
        }
        verdict = verdict_map.get(verdict_str, EvalVerdict.ERROR)

        score = float(data.get("score", 0.0))
        score = max(0.0, min(1.0, score))

        reason = str(data.get("reason", ""))

        return EvalResult(
            evaluator_name=self.name,
            verdict=verdict,
            score=score,
            reason=reason,
        )
