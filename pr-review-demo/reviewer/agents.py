"""Run all review agents concurrently and return validated AgentReview objects."""

import asyncio
from typing import Any

from reviewer.llm import call_agent
from reviewer.schema import AgentReview


async def run_all(diff_text: str) -> dict[str, AgentReview]:
    """
    Run security, performance, and maintainability reviewers in parallel.
    Returns a dict of reviewer_name -> validated AgentReview.
    """
    async def run_security() -> AgentReview:
        print("Running SecurityReviewer...")
        return await asyncio.to_thread(call_agent, "security", diff_text)

    async def run_performance() -> AgentReview:
        print("Running PerformanceReviewer...")
        return await asyncio.to_thread(call_agent, "performance", diff_text)

    async def run_maintainability() -> AgentReview:
        print("Running MaintainabilityReviewer...")
        return await asyncio.to_thread(call_agent, "maintainability", diff_text)

    results: tuple[AgentReview, AgentReview, AgentReview] = await asyncio.gather(
        run_security(),
        run_performance(),
        run_maintainability(),
    )
    return {
        "security": results[0],
        "performance": results[1],
        "maintainability": results[2],
    }
