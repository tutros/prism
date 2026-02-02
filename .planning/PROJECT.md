# Hidden Cost Comparator

## What This Is

A web app that helps users compare two options by surfacing the hidden costs and non-obvious impacts they wouldn't normally consider. Unlike typical comparison tools that focus on price, durability, or convenience, this tool uses AI to research systemic impacts — embedded energy, supply chain effects, government subsidies, externalities — and presents 3-5 non-obvious criteria with sources. Users can adjust how criteria are weighted based on their intent, and see what realistic actions could flip the outcome.

## Core Value

Surface the invisible threads that connect everyday choices to systemic impacts — the things people don't think about when making decisions.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] User can enter two options to compare
- [ ] User can describe their intent/priorities in a text box
- [ ] AI researches both options using web search with sources
- [ ] AI generates 3-5 non-obvious criteria relevant to the options
- [ ] Criteria focus on hidden costs (embedded energy, subsidies, externalities) not obvious factors
- [ ] AI weights criteria based on user intent
- [ ] User can adjust weights via sliders
- [ ] Weights auto-recalculate winner when adjusted
- [ ] User can regenerate weights (re-prompts AI with intent)
- [ ] System shows winning option with reasoning
- [ ] System shows what would flip the outcome for losing option
- [ ] Flip-the-outcome suggestions are realistic and actionable
- [ ] All information includes sources
- [ ] User can "go deeper" to get more criteria
- [ ] Results saved to file for later recall (POC)

### Out of Scope

- Database storage — POC uses file-based persistence
- User accounts / authentication — anyone can use
- Shareable links — future enhancement after database
- More than 2 options — keep it simple for v1
- Mobile app — web-first

## Context

**Motivation:** The creator often wonders about the hidden costs of choices. Example: glass vs plastic bottles — the "obvious" answer (glass = recyclable = better) falls apart when you dig into embedded energy, transportation weight, mining impacts, recycling infrastructure reality, subsidies.

**Goal:** Create a way to measure these hidden impacts and share with others via a public web app.

**Example flow:**
- Options: "glass bottle" vs "plastic bottle"
- Intent: "I want to minimize environmental impact in my local community"
- Criteria might include: local recycling infrastructure, transportation emissions (weight matters), manufacturing energy, raw material extraction impacts, microplastics vs landfill glass
- Sources for each claim
- Winner: depends on weights and local factors
- Flip the outcome: "If your local recycling actually processes plastic, and you reused it 3+ times, plastic's lifecycle impact drops below glass"

## Constraints

- **Tech Stack:** React + Vite + Tailwind (frontend), Python + FastAPI (backend)
- **AI Provider:** Claude API for reasoning and synthesis
- **Search Provider:** Tavily API for sourced web search
- **POC Persistence:** File-based (JSON files) — no database yet
- **Scope:** 3-5 criteria initially, "go deeper" for more

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| React + Vite over Next.js | Simpler setup for POC, separate frontend/backend | — Pending |
| Python + FastAPI for backend | Great for AI integration, async-native | — Pending |
| Claude + Tavily for AI + search | Claude for reasoning, Tavily for sourced research | — Pending |
| File-based persistence for POC | Avoid database complexity, migrate later | — Pending |
| 3-5 criteria default | Exhaustive analysis overwhelming, option to go deeper | — Pending |
| Sliders + auto-recalc for weights | Immediate feedback, intuitive UX | — Pending |

---
*Last updated: 2026-02-01 after initialization*
