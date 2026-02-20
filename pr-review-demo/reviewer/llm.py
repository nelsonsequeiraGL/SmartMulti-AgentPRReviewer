"""LLM call wrapper with retries and structured output parsing."""

import json
import logging
import time
from typing import Optional

from openai import OpenAI
from pydantic import ValidationError

from reviewer.prompts import build_review_system_prompt
from reviewer.schema import AgentReview, ReviewerType

logger = logging.getLogger(__name__)

# Default client (uses OPENAI_API_KEY env)
_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def call_llm(
    prompt: str,
    *,
    system_prompt: Optional[str] = None,
    max_attempts: int = 3,
) -> str:
    """
    Call the LLM with optional system prompt. Retries on transient failures.
    """
    client = _get_client()
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.2,
            )
            text = response.choices[0].message.content or ""
            if not text.strip():
                raise ValueError("Empty model response")
            return text.strip()
        except Exception as e:
            last_error = e
            logger.warning(
                "LLM call attempt %s/%s failed: %s",
                attempt,
                max_attempts,
                e,
                exc_info=False,
            )
            if attempt < max_attempts:
                time.sleep(1.0 * attempt)
            else:
                logger.error("LLM call failed after %s attempts", max_attempts)
                raise
    raise last_error  # type: ignore[misc]


def _strip_json_block(raw: str) -> str:
    """Remove markdown code fences if present."""
    s = raw.strip()
    if s.startswith("```"):
        lines = s.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        s = "\n".join(lines)
    return s.strip()


def _parse_and_validate(raw: str) -> AgentReview:
    """Parse JSON and validate as AgentReview. Raises ValueError or ValidationError."""
    data = json.loads(_strip_json_block(raw))
    return AgentReview.model_validate(data)


def call_agent(reviewer_name: str, diff_text: str) -> AgentReview:
    """
    Run one reviewer agent on the diff. Returns validated AgentReview.
    reviewer_name must be one of: security, performance, maintainability.
    On parse/validation failure, retries once with a repair prompt (max 2 attempts).
    """
    ReviewerType(reviewer_name)  # validate name
    system_prompt = build_review_system_prompt()
    user_prompt = f"Reviewer: {reviewer_name}\n\nDiff:\n{diff_text}"

    # Attempt 1
    raw = call_llm(user_prompt, system_prompt=system_prompt)
    try:
        return _parse_and_validate(raw)
    except (json.JSONDecodeError, ValidationError, ValueError) as e:
        logger.warning(
            "Agent %s: parse/validation failed (attempt 1): %s",
            reviewer_name,
            e,
            exc_info=False,
        )

    # Attempt 2: repair
    repair_prompt = (
        f"Previous output:\n{raw}\n\n"
        f"Parse/validation error: {e!s}\n\n"
        "Return corrected JSON only."
    )
    raw_repair = call_llm(repair_prompt, system_prompt=system_prompt)
    try:
        return _parse_and_validate(raw_repair)
    except (json.JSONDecodeError, ValidationError, ValueError) as e2:
        logger.error(
            "Agent %s: repair attempt failed: %s",
            reviewer_name,
            e2,
            exc_info=True,
        )
        raise
