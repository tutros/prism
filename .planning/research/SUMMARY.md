# Project Research Summary

**Project:** Prism (AI-powered Decision Comparison Tool)
**Domain:** AI-powered web application for decision support
**Researched:** 2026-02-01
**Confidence:** HIGH

## Executive Summary

This project is an AI-powered decision comparison web application that helps users make informed choices by surfacing hidden costs, systemic impacts, and non-obvious criteria. Experts in this domain build such tools using async-first architectures with modern React frontends, FastAPI backends, and direct API integrations rather than heavyweight LLM frameworks. The recommended approach is React 18 + Vite 6 + TanStack Query for the frontend, FastAPI 0.128+ with Python 3.11/3.12 for the backend, and direct integration with Claude API and Tavily Search API for AI capabilities.

The key to success is treating AI as a research assistant rather than a decision maker—every claim must be sourced, users must control weights, and transparency is non-negotiable. The primary technical challenge is handling 20-40 second AI processing times gracefully through background tasks, polling/SSE, and streaming responses. The main business risk is AI hallucination, which can be mitigated through mandatory source citations from web search, multi-source verification, and keeping humans in the loop for all final decisions.

The research shows clear architectural patterns: separate concerns (frontend owns presentation, backend owns orchestration), use async patterns throughout, start with file-based JSON storage for simplicity, and implement client-side recalculation for instant weight adjustment feedback. Critical pitfalls to avoid include hallucination without sources (must address in Phase 1), uncontrolled API costs (monitoring from day one), and poor mobile UX (responsive design from start).

## Key Findings

### Recommended Stack

Modern AI web applications benefit from lightweight, async-first stacks that minimize complexity while maximizing performance. The research shows clear winners for each layer, with emphasis on simplicity for POC while maintaining production-ready patterns.

**Core technologies:**
- **React 18.3+ with Vite 6.x**: Industry standard for greenfield projects in 2025, providing fast HMR and excellent build times. Vite's dev server and build performance far exceed webpack-based alternatives.
- **Tailwind CSS v4**: Version 4 includes dedicated Vite plugin, eliminating PostCSS/Autoprefixer complexity. Simpler setup and better performance than v3.
- **TanStack Query v5**: Purpose-built for server state management. Handles caching, background updates, loading/error states automatically—perfect for AI API calls. Solves 80% of state management needs without Redux complexity.
- **React Hook Form 7.x**: 8KB bundle (vs Formik's 15KB), zero dependencies, better performance via uncontrolled components. Formik is no longer actively maintained.
- **FastAPI 0.128+ with Python 3.11/3.12**: Native async support, automatic OpenAPI docs, excellent for AI integration. Python 3.11/3.12 provide significant performance improvements over 3.9/3.10.
- **Uvicorn 0.32+ (dev) + Gunicorn with Uvicorn workers (prod)**: Built with uvloop and httptools for maximum async performance. Gunicorn provides multi-core utilization and fault isolation.
- **Pydantic v2**: Core validation for FastAPI. V2 uses Rust (pydantic-core) for 5-50x performance improvement over v1. Automatic OpenAPI schema generation.
- **HTTPX 0.27+**: Both sync and async support (flexibility), HTTP/2 support. Better for mixed workloads than aiohttp (async-only). Only use aiohttp if you need extreme concurrency (1000+ req/s).
- **Anthropic Python SDK 0.40+**: Official SDK with excellent async support, streaming, and type hints. Use AsyncAnthropic client for FastAPI integration.
- **Tavily Python SDK 0.7.21+**: Purpose-built for LLM/AI agents, returns structured, pre-processed data with sources. 1,000 credits/month free tier sufficient for POC.
- **pathlib + Atomic Writes**: Atomic writes prevent corruption during power loss or crashes. Use os.replace() which is atomic on all platforms for JSON persistence.
- **Ruff 0.8+**: 10-100x faster than existing Python linters/formatters, written in Rust. Single tool replaces Flake8, Black, and isort.

**What NOT to use:**
- Next.js/Remix (over-engineered for POC, adds SSR complexity)
- Redux/Redux Toolkit (TanStack Query handles server state better)
- LangChain/LlamaIndex (adds abstraction overhead without value for direct API needs)
- Django/Flask (FastAPI purpose-built for async APIs)
- SQLAlchemy/any ORM (using JSON files for POC, don't add DB complexity prematurely)

### Expected Features

Decision comparison tools require foundational trust-building features before differentiation matters. Users abandon tools that lack citations or clear recommendations, regardless of how sophisticated the AI analysis is.

**Must have (table stakes):**
- **Side-by-side comparison layout** — users expect scannable format with clear visual structure
- **Source citations** — every claim must link to verifiable sources; trust is foundational
- **Clear winner indication** — visual indicator showing recommended option based on weights
- **Loading states & progress indicators** — AI research takes 5-30+ seconds, users need feedback
- **Mobile responsiveness** — 50%+ of web traffic is mobile, non-responsive tools get abandoned
- **Save/Export results** — decision-making is iterative, users want to revisit or share

**Should have (competitive differentiators):**
- **Non-obvious criteria discovery** — AI actively searches for hidden impacts users wouldn't think of (embedded energy, subsidies, externalities). This is THE core differentiator.
- **Intent-based weighting** — AI automatically weights criteria based on user's stated priorities, users can override
- **Interactive weight sliders with real-time update** — instant feedback enables exploration, no "recalculate" button needed
- **"What would flip this?" analysis** — shows realistic actions that would change the losing option into the winner
- **Source quality indicators** — credibility signals (peer-reviewed, government data vs blog posts)
- **"Go deeper" progressive disclosure** — start with 3-5 criteria, allow users to request more analysis
- **Confidence scores for AI claims** — show AI's certainty level for each finding

**Defer (v2+):**
- **More than 2 options at once** — comparison complexity grows exponentially, cognitive overload
- **Exhaustive criteria lists (10+ default)** — analysis paralysis, start with 3-7 items optimal range
- **Collaborative/multi-user editing** — scope creep, adds auth and real-time sync complexity
- **Custom criteria input** — defeats the purpose of AI discovering non-obvious criteria
- **AI chat interface for follow-up** — turns focused tool into general chatbot, dilutes value
- **Price tracking/real-time updates** — maintenance nightmare, not core to hidden cost analysis

### Architecture Approach

Modern AI web applications follow a clear separation-of-concerns pattern with async-first design throughout. The frontend owns presentation and user interaction, the backend owns orchestration and business logic, and AI services are treated as external dependencies with proper error handling and retry logic.

**Major components:**
1. **React Frontend** — User input collection, display comparison results with sources, interactive weight adjustment, trigger recalculation/regeneration, loading states and error handling. Uses TanStack Query for async state management and polling pattern for long-running operations.
2. **FastAPI Backend** — Request validation and routing, AI orchestration (Claude + Tavily coordination), business logic (scoring, flip analysis), file persistence, error handling and retry logic. Follows standard project structure with separate api/services/models/storage layers.
3. **AI Services Layer** — Claude API for reasoning/criteria generation/weighting with structured JSON outputs, Tavily API for web search with parallel searches for both options. Uses asyncio.gather() for concurrent calls to minimize latency.
4. **File-Based Storage (Repository Pattern)** — JSON files with atomic writes for crash safety, simple for POC with easy migration path to database later. Store full comparison data including research, criteria, weights, sources, and timestamps.

**Key architectural decisions:**
- **Async-first design** — AI calls take 20-40 seconds; use background tasks and polling to avoid blocking
- **Client-side recalculation** — weight changes trigger instant local updates, then sync to backend for better UX
- **Structured AI outputs** — use JSON mode for predictable Claude responses, easier parsing and error handling
- **Repository pattern** — abstract storage layer for easy swapping from files to database
- **202 Accepted pattern** — long-running operations return immediately with operation ID, client polls for results

**Suggested build order (from ARCHITECTURE.md):**
1. **Phase 1: Foundation** (Days 1-2) — Basic request/response flow, file storage, mock results to verify full stack communication
2. **Phase 2: AI Integration** (Days 3-4) — Real AI calls generating actual criteria, sequential flow first before optimizing
3. **Phase 3: Async & Performance** (Days 5-6) — BackgroundTasks, status tracking, parallel Tavily calls, React Query polling
4. **Phase 4: Interactivity** (Days 7-8) — Weight adjustment UI with sliders, local recalculation, flip analysis
5. **Phase 5: Polish & Sources** (Days 9-10) — Source citations display, regeneration, UX improvements, testing

### Critical Pitfalls

The research identified 18 pitfalls across critical, common, UX, technical, and cost categories. The top 5 that must be addressed in Phase 1 (MVP) or earlier are:

1. **AI Hallucination in Decision Support** — Studies show 69-88% hallucination rates when AI responds to queries without proper grounding. For a decision support tool, this is catastrophic. MUST address by requiring all criteria, weights, and facts to have source citations from Tavily, implement multi-source verification, and show confidence indicators. Never allow assertions without grounding in search results.

2. **Source Reliability and Dead Links** — Tavily and other search APIs can return 404s or dead pages from cached/indexed sources. Users clicking broken links lose trust immediately. MUST address by implementing link validation before displaying, adding "Last verified" timestamps, caching source content at time of analysis, and allowing users to flag unreliable sources.

3. **Criteria Weight Bias and Subjectivity** — AI-generated weights can accumulate biases, potentially favoring certain criteria repeatedly. Traditional methods suffer from anchoring bias and loss aversion. MUST address by making weight generation transparent with explanations, allowing easy user adjustment, showing sensitivity analysis ("what would flip this?"), and documenting rationale for each weight assignment.

4. **Cost Explosion from Unoptimized API Usage** — AI applications generate unexpected costs through inefficient prompts, lack of caching, and unnecessary API calls. Batch processing offers 50% savings, prompt caching provides 90% savings. MUST address by implementing prompt caching for system prompts, starting with Haiku for lightweight tasks, setting daily spending caps in dev/staging ($50/day), monitoring token usage by feature, and caching Tavily results.

5. **Slow Response Times Creating Frustration** — AI API calls take 10-30+ seconds. Without proper UX, users perceive the tool as broken. Studies show streaming reduces perceived wait time by 70%. MUST address by implementing streaming responses (SSE or ReadableStreams), showing granular progress ("Searching web...", "Analyzing sources..."), displaying partial results as they arrive, and setting realistic timeout expectations.

**Other critical pitfalls to address by phase:**
- **Phase 1 (MVP):** Over-reliance on AI without human oversight (always editable, never auto-commit), black box problem (show step-by-step reasoning), poor mobile experience (mobile-first responsive design), inadequate error handling (exponential backoff retry logic)
- **Phase 2 (Enhancement):** Information overload (progressive disclosure, limit to 5-7 initial criteria), loss of user control (every AI decision editable), poor data quality (validate source recency/relevance)
- **Phase 3 (Scale):** Scaling cost explosions (tiered pricing, cache popular comparisons, negotiate volume discounts), inefficient prompt engineering (A/B test prompt variations)

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Foundation + Core Trust Features
**Rationale:** Must establish trust before any AI features matter. All pitfalls research points to source citations and human oversight as non-negotiable for decision support tools. Architecture research shows file-based storage and basic request/response flow must work before adding complexity.

**Delivers:**
- Working React + FastAPI stack with CORS configured
- Basic comparison form (2 options + intent)
- File-based JSON storage with atomic writes
- Mock comparison results displayed side-by-side
- Source citations displayed inline with links
- Link validation for sources
- User-editable weights with local recalculation
- Clear winner indication
- Basic cost monitoring setup ($50/day dev cap)
- Mobile-responsive layout

**Addresses:** Table stakes features (side-by-side layout, source citations, winner indication, mobile responsiveness) + critical pitfalls (#1 hallucination, #2 dead links, #6 human oversight, #12 mobile UX)

**Avoids:** Building on shaky foundation, losing user trust early, accumulating technical debt

**Research Flag:** STANDARD PATTERNS - Well-documented React + FastAPI setup, skip `/gsd:research-phase`

---

### Phase 2: AI Integration + Async Orchestration
**Rationale:** With trust infrastructure in place, add real AI capabilities. Research shows sequential flow first (easier to debug) before optimizing for async. Tavily + Claude integration is straightforward with official SDKs.

**Delivers:**
- Tavily search integration for both options (parallel asyncio.gather)
- Claude API integration with structured JSON outputs
- Prompt engineering for criteria discovery and weighting
- AI orchestration service coordinating research -> criteria -> weights
- FastAPI BackgroundTasks for long-running operations
- 202 Accepted + polling pattern on frontend
- Streaming progress updates via SSE
- Retry logic with exponential backoff
- Error handling for API failures

**Addresses:** Core differentiator (non-obvious criteria discovery), intent-based weighting, loading states & progress indicators

**Uses:** AsyncAnthropic client, Tavily SDK, HTTPX, asyncio patterns

**Implements:** AI Services Layer, Orchestration Service from architecture

**Avoids:** Critical pitfall #1 (all AI claims grounded in Tavily sources), #4 (prompt caching implemented), #5 (streaming for perceived performance), #13 (error handling with graceful degradation)

**Research Flag:** MAY NEED RESEARCH - Prompt engineering for systemic impact discovery is iterative. Consider `/gsd:research-phase` if initial prompts don't surface hidden costs effectively.

---

### Phase 3: Interactive Analysis + Flip Detection
**Rationale:** Users need to explore decisions, not just accept AI recommendations. Research shows weight adjustment is where users gain confidence in the tool. Flip analysis is a key differentiator that no competitor offers.

**Delivers:**
- Interactive weight sliders with instant client-side recalculation
- PATCH endpoint for persisting weight changes
- Flip analysis algorithm (what weight changes would reverse winner)
- Display sensitive criteria (high impact on outcome)
- "What would flip this?" visualization
- Optimistic UI updates with backend sync
- Regenerate criteria button (reuse research, new AI analysis)

**Addresses:** Differentiators (interactive weight adjustment, flip analysis, "go deeper")

**Implements:** Client-side scoring service, sensitivity analysis logic

**Avoids:** Critical pitfall #3 (weight bias addressed via transparency and user control), #11 (loss of user agency), #10 (information overload via progressive disclosure)

**Research Flag:** STANDARD PATTERNS - UI state management and scoring algorithms are well-understood, skip research

---

### Phase 4: Source Quality + Confidence Signals
**Rationale:** Not all sources are equal. Users need to assess reliability of claims. Research shows confidence indicators build trust when calibrated properly.

**Delivers:**
- Source quality classification (peer-reviewed, government, industry, blog)
- Domain-based heuristics (.gov, .edu, journals)
- Confidence scores for AI claims based on source quality
- "Last verified" timestamps on sources
- Source diversity metrics
- Ability to flag unreliable sources
- Cache source content at analysis time
- Display multiple sources per claim when available

**Addresses:** Differentiators (source quality indicators, confidence scores)

**Avoids:** Critical pitfall #2 (source reliability), #8 (poor data quality)

**Research Flag:** MAY NEED RESEARCH - Source quality classification may require experimentation with heuristics vs AI classification

---

### Phase 5: Cost Optimization + Scaling Prep
**Rationale:** With core features working, optimize for production costs before user growth. Research shows 50-90% cost reduction possible through caching and batching.

**Delivers:**
- Prompt caching for system prompts (90% savings on repeated content)
- Tavily result caching with 24hr TTL
- Full comparison result caching with 1-7 day TTL
- Cache age display with "Refresh with latest data" option
- Token usage monitoring by feature/request
- Rate limiting per user
- Cost per comparison metrics
- Prompt optimization (trim to minimum needed length)
- Model selection (Haiku for lightweight, Sonnet for complex)

**Addresses:** Cost optimization, scaling preparation

**Avoids:** Critical pitfall #4 (cost explosion), #15 (poor caching), #17 (inefficient prompts), #18 (scaling cost explosions)

**Research Flag:** STANDARD PATTERNS - Caching and cost monitoring are well-documented FastAPI patterns

---

### Phase Ordering Rationale

**Dependency-driven order:**
- Phase 1 must come first: Trust infrastructure (sources, human oversight) is prerequisite for AI features. Architecture foundation must work before adding complexity.
- Phase 2 depends on Phase 1: AI integration requires working storage, validation, and display layers.
- Phase 3 depends on Phase 2: Interactive features require working AI system to recalculate against.
- Phase 4 can partially overlap Phase 3: Source quality can be added as AI integration matures.
- Phase 5 comes last: Optimize only after core features proven.

**Risk-mitigation order:**
- Critical pitfalls (#1 hallucination, #2 sources, #4 costs, #5 UX) addressed in Phases 1-2 before scaling.
- Common mistakes (#6 oversight, #7 explainability, #10 overload, #11 agency) addressed in Phases 1-3.
- UX pitfalls (#9 slow responses, #12 mobile) addressed in Phase 1 foundation.
- Technical/cost pitfalls (#13 errors, #15 caching, #17 prompts) addressed progressively.

**Value delivery order:**
- Phase 1 delivers visible progress quickly (2-3 days to working UI)
- Phase 2 delivers core value proposition (non-obvious criteria discovery)
- Phase 3 delivers key differentiator (flip analysis) that no competitor has
- Phase 4 enhances trust in existing features
- Phase 5 enables sustainable scaling

### Research Flags

**Phases likely needing deeper research during planning:**
- **Phase 2 (AI Integration):** Prompt engineering for systemic impact discovery is iterative and domain-specific. May need `/gsd:research-phase` to refine prompt templates for surfacing hidden costs, subsidies, and externalities effectively.
- **Phase 4 (Source Quality):** Source quality classification may require experimentation. Consider `/gsd:research-phase` if simple heuristics prove insufficient and AI classification needed.

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (Foundation):** React + Vite + FastAPI setup is well-documented with clear patterns. File-based storage with atomic writes is proven approach.
- **Phase 3 (Interactivity):** Weight sliders, client-side recalculation, and scoring algorithms are standard UI patterns with established libraries.
- **Phase 5 (Cost Optimization):** Caching strategies, prompt optimization, and cost monitoring are well-documented in FastAPI and Anthropic docs.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All recommendations backed by official docs, recent articles (2025-2026), and community consensus. React + Vite + FastAPI is battle-tested for AI applications. Version numbers verified from package registries. |
| Features | HIGH | Extensive research into comparison tool UX, AI research assistant patterns, and decision matrix tools. Clear distinction between table stakes and differentiators based on multiple user research sources. Anti-features backed by cognitive load research. |
| Architecture | HIGH | Multiple architecture pattern articles from 2025-2026 agree on async-first design, separation of concerns, and background task patterns. File-based storage validated for POC. Build order tested in similar projects. |
| Pitfalls | HIGH | 18 pitfalls identified from diverse sources (academic papers, industry blogs, vendor docs). Each pitfall includes warning signs, prevention strategies, and phase recommendations. Hallucination research particularly robust with multiple studies. |

**Overall confidence:** HIGH

All four research areas produced consistent recommendations across multiple high-quality sources. Technologies chosen are current (2025-2026), actively maintained, and appropriate for POC-to-production path. Feature priorities align with both expert guidance and user research. Architecture patterns are proven for AI web applications. Pitfalls cover full spectrum from critical (hallucination) to cost/UX concerns.

### Gaps to Address

**Prompt engineering effectiveness:** While prompt patterns exist for criteria discovery, the specific prompt structure for surfacing systemic impacts (subsidies, externalities, embedded energy) will require iteration and validation during Phase 2 implementation. Plan to A/B test prompt variations and validate against known examples.

**Source quality heuristics calibration:** Simple domain-based heuristics (.gov, .edu, journals) are a starting point, but may need refinement based on real Tavily results. Monitor false positives/negatives and adjust classification logic during Phase 4.

**Cost projections at scale:** While optimization strategies are clear (caching, batching, prompt compression), actual costs per comparison depend on prompt size, criteria count, and source depth. Monitor cost per comparison metric from Phase 2 onward to validate assumptions and adjust if needed.

**Mobile UX for complex comparisons:** Research validates mobile-responsive design, but optimal mobile experience for weight sliders and multi-criteria comparisons may require usability testing. Plan for mobile-specific optimizations in Phase 1 foundation.

**Tavily result quality variability:** Research confirms Tavily is reliable, but result quality varies by query specificity and topic. Plan for monitoring source relevance and implementing query refinement logic if initial searches return poor results.

## Sources

### Primary (HIGH confidence)

**Official Documentation:**
- [FastAPI Official Docs](https://fastapi.tiangolo.com/) — async patterns, background tasks, deployment
- [TanStack Query Docs](https://tanstack.com/query/latest) — server state management, polling patterns
- [Anthropic API Reference](https://docs.anthropic.com/) — async client, streaming, prompt caching
- [Tavily API Docs](https://docs.tavily.com/) — search best practices, optimization
- [React Hook Form](https://react-hook-form.com/) — form handling patterns
- [Tailwind CSS v4](https://tailwindcss.com/docs) — Vite integration, v4 migration

**Industry Best Practices (2025-2026 articles):**
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices) — project structure, async patterns
- [Modern FastAPI Architecture Patterns for Scalable Production Systems](https://medium.com/algomart/modern-fastapi-architecture-patterns-for-scalable-production-systems-41a87b165a8b) — proven patterns
- [Building Scalable AI Apps with React & FastAPI](https://dev.to/mayowaadeoni/building-scalable-ai-apps-with-react-fastapi-2gg0) — integration patterns
- [FastAPI production deployment best practices](https://render.com/articles/fastapi-production-deployment-best-practices) — Gunicorn + Uvicorn config

### Secondary (MEDIUM confidence)

**UX Research & Comparison Tools:**
- [Comparison Tables - Nielsen Norman Group](https://www.nngroup.com/articles/comparison-tables/) — UX patterns
- [4 Ways to Optimize Comparison Features - Baymard](https://baymard.com/blog/user-friendly-comparison-tools) — user research findings
- [Comparing Products UX Best Practices - Contentsquare](https://contentsquare.com/blog/comparing-products-design-practices-to-help-your-users-avoid-fragmented-comparison-7/) — mobile UX

**AI Decision Making & Hallucination:**
- [AI Hallucination: Compare top LLMs](https://research.aimultiple.com/ai-hallucination/) — 69-88% rates without grounding
- [Understanding and Mitigating AI Hallucination - DigitalOcean](https://www.digitalocean.com/resources/articles/ai-hallucination) — prevention strategies
- [Diagnosing Hallucination Risk in AI Decision-Support - arXiv](https://arxiv.org/html/2511.00588v1) — academic research

**Cost Management:**
- [FinOps For Claude: Managing Costs at Scale - CloudZero](https://www.cloudzero.com/blog/finops-for-claude/) — 50-90% savings strategies
- [Manage costs effectively - Claude Code](https://code.claude.com/docs/en/costs) — prompt caching, batching
- [Optimize Hidden Costs of Claude APIs - CloudBuckle](https://blog.cloudbuckle.com/how-to-optimize-the-hidden-costs-of-anthropic-claude-apis-part-1-ce52d08ae3e4)

### Tertiary (LOW confidence, needs validation)

**Streaming & Performance:**
- [Stop Making Users Wait: Ultimate Guide to Streaming](https://dev.to/programmingcentral/stop-making-users-wait-the-ultimate-guide-to-streaming-ai-responses-22m3) — 70% perceived wait time reduction (needs validation in real tests)
- [Real-time AI: Streaming with Vercel AI SDK](https://blog.logrocket.com/nextjs-vercel-ai-sdk-streaming/) — patterns adaptable to FastAPI

---
*Research completed: 2026-02-01*
*Ready for roadmap: yes*
