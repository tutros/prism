# Phase 4 Context: Source Quality + Confidence Signals

**Created:** 2026-02-09
**Phase Goal:** Users can assess reliability of AI claims through source quality indicators and confidence scores.

## Design Decisions

### 1. Source Quality Classification

**Decision:** AI Classification

Claude will analyze each source during the research phase and assign quality indicators based on content analysis. This provides more nuanced classification than domain heuristics alone.

**Implementation notes:**
- Add quality classification prompt to Claude's source analysis
- Quality tiers: peer-reviewed, government, industry, news, blog, unknown
- Store quality metadata with each source in the comparison result
- AI considers: publication type, author credentials, citation patterns, recency

### 2. Confidence Score Display

**Decision:** Text Badges

Display confidence as High/Medium/Low text badges, consistent with the existing Impact badges pattern in CriteriaEditor.

**Implementation notes:**
- Badges appear next to claims/criteria
- Styling matches existing badge pattern (green/amber/gray)
- Confidence calculated from: source quality diversity, source count, claim specificity
- Tooltip or explainer section describes what confidence levels mean

### 3. Multi-Source Per Claim

**Decision:** Inline Links

Show all sources inline separated by commas. Keep display simple and scannable.

**Implementation notes:**
- Each criterion shows all supporting sources as comma-separated links
- Format: "Source: [Domain1], [Domain2], [Domain3]"
- Links open in new tab
- If many sources, may truncate with "+N more" pattern

### 4. Source Flagging UX

**Decision:** Click Icon

Small flag icon next to each source - click to toggle flagged state.

**Implementation notes:**
- Flag icon appears on hover or always visible
- Clicking flags/unflags the source
- Flagged sources show visual indicator (strikethrough, red badge, or dimmed)
- Flagged state persists in comparison result JSON
- Backend endpoint to update source flagged status

## Success Criteria Mapping

| Success Criterion | Design Decision |
|-------------------|-----------------|
| Source quality indicators (peer-reviewed, gov, etc.) | AI Classification |
| Confidence scores based on quality and diversity | Text Badges (High/Med/Low) |
| "Last verified" timestamp | TBD - part of source metadata |
| Flag unreliable sources | Click Icon toggle |
| Multiple sources per claim | Inline Links |

## Technical Considerations

### Backend Changes
- Extend Claude prompt to output source quality classifications
- Add SourceMetadata model with quality, timestamp, flagged fields
- Add endpoint: PATCH /api/comparisons/{id}/sources/{source_id}/flag

### Frontend Changes
- Update source display in CriteriaEditor to show multiple inline links
- Add SourceLink component with quality badge and flag icon
- Add confidence badge next to criteria
- Extend ScoringExplainer with confidence explanation

---
*Context gathered: 2026-02-09*
*Ready for: /gsd:plan-phase 4*
