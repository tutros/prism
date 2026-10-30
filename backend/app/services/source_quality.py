"""Source quality and criterion confidence.

Claude labels each cited source during criteria generation; classify_sources()
turns those labels into the stored url -> quality map. It is the one place that
decides a source's quality, so it can later be swapped for another classifier
(#22) without touching compute_confidence().
"""

from typing import Literal

from pydantic import BaseModel

SourceQuality = Literal["peer-reviewed", "government", "industry", "news", "blog", "unknown"]
Confidence = Literal["high", "medium", "low"]

_VALID_QUALITIES: set[str] = {"peer-reviewed", "government", "industry", "news", "blog", "unknown"}

# Quality tiers ordered from highest to lowest trust
_QUALITY_RANK: dict[str, int] = {
    "peer-reviewed": 4,
    "government": 3,
    "industry": 2,
    "news": 1,
    "blog": 0,
    "unknown": 0,
}

CLASSIFICATION_PROMPT = (
    "For each source URL you cite, classify its quality tier in source_classifications:\n"
    '- "peer-reviewed": academic journals, scientific studies\n'
    '- "government": .gov domains, regulators, government agencies\n'
    '- "industry": trade associations, industry or company reports\n'
    '- "news": news outlets, journalism\n'
    '- "blog": personal blogs, opinion pieces, commentary\n'
    '- "unknown": cannot tell\n'
)


class SourceClassification(BaseModel):
    """Claude's quality label for one source URL."""
    url: str
    quality: str


def classify_sources(
    classifications: list[SourceClassification],
    research_urls: set[str],
) -> dict[str, SourceQuality]:
    """Map every researched URL to a quality tier.

    URLs Claude did not label, or labelled with an unknown tier, are "unknown".
    Labels for URLs outside the research are dropped.
    """
    quality: dict[str, SourceQuality] = {url: "unknown" for url in research_urls}
    for sc in classifications:
        if sc.url in quality and sc.quality in _VALID_QUALITIES:
            quality[sc.url] = sc.quality  # type: ignore[assignment]
    return quality


def compute_confidence(sources: list[str], source_quality: dict[str, str]) -> Confidence:
    """Grade a criterion from its sources.

    - high:   >= 2 sources AND at least one peer-reviewed or government source
    - medium: >= 1 source AND at least one industry or news source
    - low:    otherwise

    Only sources present in source_quality (i.e. from the research) count.
    """
    known = {url for url in sources if url in source_quality}
    if not known:
        return "low"

    max_rank = max(_QUALITY_RANK.get(source_quality[url], 0) for url in known)
    if len(known) >= 2 and max_rank >= 3:  # peer-reviewed or government
        return "high"
    if max_rank >= 1:  # industry or news
        return "medium"
    return "low"
