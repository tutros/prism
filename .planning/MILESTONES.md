# Project Milestones: Prism

## v1.0 MVP (Shipped: 2026-06-15)

**Delivered:** AI-powered N-option decision analysis tool with three depth tiers (Quick/Medium/Deep), auto tier suggestion, hidden property discovery, decisions→analyses two-level API, and a consumer app UI.

**Phases completed:** 6 (scaffold + phases 2–6)

**Key accomplishments:**

- N-option comparison (2–6+) replacing the original 2-option constraint
- Three depth tiers: Quick (LLM-only ~5s), Medium (Tavily web search ~45s), Deep (hidden properties ~3min)
- Auto tier suggestion via claude-haiku on decision creation
- Decisions → Analyses two-level hierarchy; supports re-running at different tiers with dedup
- Hidden property discovery (Deep tier) surfaces second-order systemic impacts
- Consumer App UI with scoring engine, analyses list, and history sidebar
- SSE real-time progress streaming; atomic JSON persistence; daily spending cap
- Code review of the Prism codebase: findings across 8 files fixed (9d394d5). The earlier 35-issue review (5 Critical, 10 High, 12 Medium, 8 Low, see `tasks/todo.md`) was done on the orchids predecessor in 2026-02, before the Prism scaffold

**What's next:** Planning next milestone — potential areas include database storage, shareable links, user accounts.

---
*Note: Earlier planning docs (.planning/phases/, .planning/milestones/) reference the predecessor "Hidden Cost Comparator" project (2-option, single-comparison API). Those are preserved as historical context.*

---
