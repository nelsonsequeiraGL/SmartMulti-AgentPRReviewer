"""Render merged issues to skimmable Markdown (≈30 sec read)."""

from collections import defaultdict

from reviewer.schema import Issue


def _one_line(issue: Issue) -> str:
    """Single skimmable line: severity, location, title."""
    return f"- **{issue.severity.value}** `{issue.file}:{issue.lines}` — {issue.title}"


def render_to_markdown(issues: list[Issue]) -> str:
    """
    Markdown report: title, top 3 issues, findings by file, suggested checklist.
    Designed to be skimmable in ~30 seconds.
    """
    lines = [
        "## AI PR Review",
        "",
        "### Top Issues (top 3 by severity)",
        "",
    ]

    # Top 3 by severity (list already sorted: high, med, low)
    top = issues[:3]
    if not top:
        lines.append("*No issues reported.*")
    else:
        for issue in top:
            lines.append(_one_line(issue))
            lines.append(f"  - *Suggestion:* {issue.suggestion}")
            lines.append("")
    lines.append("")

    # Findings by file
    lines.append("### Findings by File")
    lines.append("")
    by_file = defaultdict(list)
    for i in issues:
        by_file[i.file].append(i)
    for file in sorted(by_file.keys()):
        lines.append(f"**{file}**")
        for issue in by_file[file]:
            lines.append(_one_line(issue))
        lines.append("")
    lines.append("")

    # Static checklist
    lines.append("### Suggested Checklist")
    lines.append("")
    lines.append("- [ ] Fix high-severity security issues")
    lines.append("- [ ] Add validation / error handling")
    lines.append("- [ ] Add pagination / batching")
    lines.append("- [ ] Add tests")
    lines.append("")

    return "\n".join(lines).strip()
