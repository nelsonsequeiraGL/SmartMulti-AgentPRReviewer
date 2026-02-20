"""Merge and deduplicate issues from multiple AgentReviews."""

import re
from collections import defaultdict
from difflib import SequenceMatcher
from reviewer.schema import AgentReview, Issue, IssueSeverity

# Severity rank: lower = higher priority
SEVERITY_RANK = {IssueSeverity.high: 0, IssueSeverity.med: 1, IssueSeverity.low: 2}

# Title similarity threshold for dedup (0 = exact match after normalize, 1 = anything)
TITLE_SIMILARITY_THRESHOLD = 0.8


def _parse_line_range(lines: str) -> tuple[int, int]:
    """Parse '12-18' or 'L12-L18' -> (start, end). Single line '12' -> (12, 12)."""
    nums = [int(m) for m in re.findall(r"\d+", lines)]
    if not nums:
        return (0, 0)
    start = nums[0]
    end = nums[1] if len(nums) > 1 else start
    return (start, end)


def _overlaps(a: tuple[int, int], b: tuple[int, int]) -> bool:
    """True if ranges [a0,a1] and [b0,b1] overlap."""
    return not (a[1] < b[0] or b[1] < a[0])


def _title_similar(norm_a: str, norm_b: str, raw_a: str, raw_b: str) -> bool:
    """True if titles are equal after normalize or have high string similarity."""
    if norm_a == norm_b:
        return True
    return SequenceMatcher(None, raw_a, raw_b).ratio() >= TITLE_SIMILARITY_THRESHOLD


def _normalize_title(s: str) -> str:
    return s.lower().strip()


def merge(reviews: dict[str, AgentReview]) -> list[Issue]:
    """
    1. Flatten all issues into one list.
    2. Map severity rank: high=0, med=1, low=2.
    3. Sort by (rank, file, line start).
    4. Group by file.
    5. Deduplicate: same file + overlapping line range + similar title -> keep higher severity.
    Returns a single sorted list of deduplicated issues.
    """
    # 1. Flatten
    all_issues: list[Issue] = []
    for review in reviews.values():
        all_issues.extend(review.issues)

    if not all_issues:
        return []

    # 2 & 3: attach rank and line start, then sort by (rank, file, line_start)
    def sort_key(issue: Issue) -> tuple[int, str, int]:
        start, _ = _parse_line_range(issue.lines)
        return (SEVERITY_RANK[issue.severity], issue.file, start)

    all_issues.sort(key=sort_key)

    # 4. Group by file
    by_file: dict[str, list[Issue]] = defaultdict(list)
    for issue in all_issues:
        by_file[issue.file].append(issue)

    # 5. Deduplicate per file: keep an issue iff no already-kept issue has
    #    overlapping range + similar title (when that happens, we already kept
    #    the higher severity one because list is sorted by rank).
    kept: list[Issue] = []
    for file, issues in by_file.items():
        for candidate in issues:
            c_start, c_end = _parse_line_range(candidate.lines)
            c_norm = _normalize_title(candidate.title)
            is_dup = False
            for k in kept:
                if k.file != file:
                    continue
                k_start, k_end = _parse_line_range(k.lines)
                if _overlaps((c_start, c_end), (k_start, k_end)) and _title_similar(
                    c_norm, _normalize_title(k.title), candidate.title, k.title
                ):
                    is_dup = True
                    break
            if not is_dup:
                kept.append(candidate)

    # Sort final list by (rank, file, line_start)
    kept.sort(key=sort_key)
    return kept
