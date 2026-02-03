# Roadmap: Hidden Cost Comparator

## Overview

This roadmap delivers an AI-powered decision comparison tool that surfaces hidden costs and systemic impacts invisible in traditional comparisons. The five phases progress from trust infrastructure (sources, human oversight) through AI integration (criteria discovery, weighting) to differentiation (flip analysis, confidence signals) and scaling preparation (cost optimization). Every phase delivers verifiable user capabilities that build toward the core value: surfacing invisible threads connecting choices to systemic impacts.

**Phases:** 5
**Depth:** Standard (5-8 phases, 3-5 plans each)
**Coverage:** 23/23 v1 requirements mapped

## Phases

### Phase 1: Foundation + Core Trust

**Goal:** Users can compare two options with source-cited information and see a clear winner based on adjustable weights.

**Dependencies:** None (foundation)

**Requirements:** INP-01, INP-02, INP-03, INP-04, WGT-02, WGT-03, WGT-04, RST-01, UX-01, UX-02, UX-04, UX-05

**Plans:** 5 plans in 3 waves

Plans:
- [ ] 01-01-PLAN.md - Backend setup (FastAPI, Pydantic models, atomic JSON storage)
- [ ] 01-02-PLAN.md - Frontend setup (Vite + React + TanStack Query + Tailwind)
- [ ] 01-03-PLAN.md - Comparison flow (form, API integration, polling, display)
- [ ] 01-04-PLAN.md - Weight system (sliders, client-side recalculation)
- [ ] 01-05-PLAN.md - Persistence + polish (history, examples, responsive verification)

**Success Criteria:**
1. User can enter two options and intent, submit comparison, and see results within reasonable time
2. User can view comparison results side-by-side with clear visual winner indication
3. User can adjust weight sliders and see scores recalculate instantly without page reload
4. User can save comparison results and recall them by filename
5. User can access the application on mobile device with full functionality (responsive design)
6. Every displayed claim includes clickable source citation links that work

**Notes:** Establishes trust infrastructure before AI features. Uses mock AI results initially to verify full stack communication. File-based JSON storage with atomic writes. Addresses critical pitfalls: source reliability, human oversight, mobile UX, cost monitoring setup.

---

### Phase 2: AI Integration + Async Orchestration

**Goal:** AI researches both options via web search and generates non-obvious criteria with intent-based weights.

**Dependencies:** Phase 1 (requires working storage, display, and validation)

**Requirements:** RES-01, RES-02, RES-03, WGT-01, UX-03

**Success Criteria:**
1. User sees AI discover 3-5 criteria that are non-obvious (not price/durability/convenience)
2. User sees criteria focused on hidden costs (embedded energy, subsidies, externalities, supply chain)
3. User sees AI-generated weights that reflect their stated intent/priorities
4. User sees real-time progress updates during AI processing ("Searching web...", "Analyzing sources...")
5. Every criterion includes at least one source citation from web search results
6. User can submit comparison and return later to find results ready (async processing works)

**Notes:** Integrates Tavily search (parallel calls) and Claude API (structured outputs). Implements BackgroundTasks with 202 Accepted + polling pattern. Streaming progress via SSE. Addresses critical pitfalls: AI hallucination (all claims grounded in sources), cost explosion (prompt caching), slow responses (streaming), error handling.

---

### Phase 3: Interactive Analysis + Flip Detection

**Goal:** Users can explore alternative scenarios and understand what would change the losing option into the winner.

**Dependencies:** Phase 2 (requires working AI system to recalculate against)

**Requirements:** RES-04, WGT-05, RST-02, RST-03, RST-04

**Success Criteria:**
1. User can click "Go Deeper" and see AI generate additional criteria beyond initial 3-5
2. User can click "Regenerate Weights" and see AI recalculate based on same intent with fresh analysis
3. User sees "What would flip this?" analysis showing realistic actions that would reverse the winner
4. Flip suggestions are actionable only (no impossible changes like "change the laws")
5. Flip suggestions include source citations justifying the suggested changes
6. User sees which criteria are most sensitive (high impact on outcome if weights change)

**Notes:** Client-side scoring service for instant recalculation. Flip analysis algorithm calculates weight threshold changes. Optimistic UI updates with backend sync. Addresses pitfalls: weight bias transparency, loss of user agency, information overload via progressive disclosure.

---

### Phase 4: Source Quality + Confidence Signals

**Goal:** Users can assess reliability of AI claims through source quality indicators and confidence scores.

**Dependencies:** Phase 2 (requires AI integration and source data)

**Requirements:** RES-05

**Success Criteria:**
1. User sees source quality indicators for each citation (peer-reviewed, government, industry, blog)
2. User sees confidence scores for AI claims based on source quality and diversity
3. User sees "Last verified" timestamp on sources to assess recency
4. User can flag unreliable sources and see flagged status persist
5. User sees multiple sources per claim when available (not just single citation)

**Notes:** Domain-based heuristics for quality classification (.gov, .edu, journals). Caches source content at analysis time to prevent dead links. Multi-source verification when available. Addresses pitfalls: source reliability, poor data quality.

---

### Phase 5: Cost Optimization + Scaling Prep

**Goal:** Application runs efficiently with optimized API costs and monitoring for sustainable scaling.

**Dependencies:** Phase 2 (requires working AI system to optimize)

**Requirements:** None (infrastructure improvements, not user-facing features)

**Success Criteria:**
1. Developer sees token usage metrics broken down by feature and request type
2. Developer sees cost per comparison tracked and displayed in monitoring dashboard
3. Developer can set daily spending caps that prevent runaway API costs
4. User sees cache age indicators and can choose "Refresh with latest data" for stale results
5. System automatically caches Tavily results and comparison outputs to reduce duplicate API calls
6. System uses prompt caching for repeated content (90% cost reduction on system prompts)

**Notes:** Implements prompt caching, Tavily result caching (24hr TTL), comparison result caching (1-7 day TTL). Token usage monitoring. Rate limiting. Model selection (Haiku for lightweight, Sonnet for complex). Addresses pitfalls: cost explosion, poor caching, inefficient prompts, scaling cost explosions.

---

## Progress

| Phase | Status | Progress | Requirements |
|-------|--------|----------|--------------|
| 1 - Foundation + Core Trust | ○ Pending | 0% | 12 requirements |
| 2 - AI Integration + Async Orchestration | ○ Pending | 0% | 5 requirements |
| 3 - Interactive Analysis + Flip Detection | ○ Pending | 0% | 5 requirements |
| 4 - Source Quality + Confidence Signals | ○ Pending | 0% | 1 requirement |
| 5 - Cost Optimization + Scaling Prep | ○ Pending | 0% | 0 requirements (infra) |

**Legend:** ○ Pending | ◐ In Progress | ● Complete

## Phase Ordering Rationale

**Dependency-driven order:**
- Phase 1 establishes trust infrastructure (sources, human oversight) that is prerequisite for AI features
- Phase 2 builds on working storage, validation, and display layers from Phase 1
- Phase 3 requires working AI system from Phase 2 to enable interactive recalculation
- Phase 4 enhances AI integration from Phase 2 with quality signals
- Phase 5 optimizes proven system from Phase 2 before scaling

**Risk-mitigation order:**
- Critical pitfalls (hallucination, sources, costs, UX) addressed in Phases 1-2 before scaling
- Common mistakes (oversight, explainability, overload, agency) addressed in Phases 1-3
- Technical/cost pitfalls progressively addressed across all phases

**Value delivery order:**
- Phase 1 delivers visible progress quickly (working UI, full stack verified)
- Phase 2 delivers core value proposition (non-obvious criteria discovery)
- Phase 3 delivers key differentiator (flip analysis) unique to this tool
- Phase 4 enhances trust in existing features
- Phase 5 enables sustainable scaling

---
*Last updated: 2026-02-02 after roadmap creation*
