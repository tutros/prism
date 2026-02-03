# Requirements: Hidden Cost Comparator

**Defined:** 2026-02-01
**Core Value:** Surface the invisible threads that connect everyday choices to systemic impacts

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Input

- [ ] **INP-01**: User can enter two options to compare (text fields)
- [ ] **INP-02**: User can describe their intent/priorities in a text box
- [ ] **INP-03**: User can click Compare to trigger AI analysis
- [ ] **INP-04**: User sees example prompts to help get started

### Research

- [ ] **RES-01**: AI researches both options via Tavily web search
- [ ] **RES-02**: AI generates 3-5 non-obvious criteria (hidden costs, not obvious factors)
- [ ] **RES-03**: Every criterion includes source citations (clickable links)
- [ ] **RES-04**: User can "Go Deeper" to generate additional criteria
- [ ] **RES-05**: Sources display quality indicators (peer-reviewed, government, blog, etc.)

### Weights

- [ ] **WGT-01**: AI generates initial weights based on user intent
- [ ] **WGT-02**: System displays weighted scores for each option
- [ ] **WGT-03**: User can adjust weights via sliders
- [ ] **WGT-04**: Scores auto-recalculate when weights change
- [ ] **WGT-05**: User can regenerate weights (re-prompts AI with intent)

### Results

- [ ] **RST-01**: System shows clear winner with reasoning summary
- [ ] **RST-02**: System shows "what would flip the outcome" for losing option
- [ ] **RST-03**: Flip suggestions are realistic and actionable only
- [ ] **RST-04**: Flip suggestions include source citations

### UX

- [ ] **UX-01**: Loading states shown during AI processing
- [ ] **UX-02**: Mobile responsive design
- [ ] **UX-03**: Streaming responses show AI progress in real-time
- [ ] **UX-04**: Results saved to JSON file (POC persistence)
- [ ] **UX-05**: User can recall previous results by filename

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Sharing

- **SHR-01**: Shareable links to specific comparison results
- **SHR-02**: Database storage for persistent results
- **SHR-03**: Embed comparison results on other sites

### Advanced

- **ADV-01**: Compare more than 2 options
- **ADV-02**: User accounts to save comparisons
- **ADV-03**: Comparison history dashboard

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| User authentication | Anyone can use, no accounts for POC |
| Database storage | File-based for POC, migrate later |
| More than 2 options | Complexity explosion, keep v1 simple |
| Real-time price tracking | Maintenance burden, out of core value |
| Collaborative editing | Scope creep for MVP |
| Custom criteria input | Defeats AI discovery purpose |
| Mobile native app | Web-first, responsive design sufficient |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INP-01 | Phase 1 | Pending |
| INP-02 | Phase 1 | Pending |
| INP-03 | Phase 1 | Pending |
| INP-04 | Phase 1 | Pending |
| RES-01 | Phase 2 | Pending |
| RES-02 | Phase 2 | Pending |
| RES-03 | Phase 2 | Pending |
| RES-04 | Phase 3 | Pending |
| RES-05 | Phase 4 | Pending |
| WGT-01 | Phase 2 | Pending |
| WGT-02 | Phase 1 | Pending |
| WGT-03 | Phase 1 | Pending |
| WGT-04 | Phase 1 | Pending |
| WGT-05 | Phase 3 | Pending |
| RST-01 | Phase 1 | Pending |
| RST-02 | Phase 3 | Pending |
| RST-03 | Phase 3 | Pending |
| RST-04 | Phase 3 | Pending |
| UX-01 | Phase 1 | Pending |
| UX-02 | Phase 1 | Pending |
| UX-03 | Phase 2 | Pending |
| UX-04 | Phase 1 | Pending |
| UX-05 | Phase 1 | Pending |

**Coverage:**
- v1 requirements: 23 total
- Mapped to phases: 23 (100% coverage)
- Unmapped: 0

**Phase distribution:**
- Phase 1 (Foundation + Core Trust): 12 requirements
- Phase 2 (AI Integration + Async Orchestration): 5 requirements
- Phase 3 (Interactive Analysis + Flip Detection): 5 requirements
- Phase 4 (Source Quality + Confidence Signals): 1 requirement
- Phase 5 (Cost Optimization + Scaling Prep): 0 requirements (infrastructure improvements)

---
*Requirements defined: 2026-02-01*
*Last updated: 2026-02-02 after roadmap creation*
