"""Prompt fragments and schema template for the PR review agent."""

# Instruction prompts (combine as needed for the LLM)
ONLY_ANALYZE_DIFF = "Only analyze what's in the diff. Don't assume anything else."
RETURN_VALID_JSON = "Return ONLY valid JSON matching this schema."
FILE_AND_LINES_REQUIRED = "Every issue must include file + line range from the diff."
EMPTY_ISSUES_OK = "If you can't find issues, return empty issues: [] with a short summary."

# Compact schema shape for the prompt (keep short)
SCHEMA_TEMPLATE = """{
  "reviewer": "security" | "performance" | "maintainability",
  "summary": "<string>",
  "issues": [
    {
      "severity": "high" | "med" | "low",
      "file": "<path from diff>",
      "lines": "<e.g. 12-18 or L12-L18>",
      "title": "<string>",
      "details": "<string>",
      "suggestion": "<string>"
    }
  ]
}"""


def build_review_system_prompt() -> str:
    """Full system prompt for the review agent, including schema and rules."""
    return "\n\n".join([
        ONLY_ANALYZE_DIFF,
        RETURN_VALID_JSON,
        FILE_AND_LINES_REQUIRED,
        EMPTY_ISSUES_OK,
        "Schema:",
        SCHEMA_TEMPLATE,
    ])
