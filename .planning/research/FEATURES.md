# Features Research: AI-Powered Decision Comparison Tools

**Research Date:** 2026-02-01
**Context:** Building a web app that compares two options by surfacing hidden costs and non-obvious impacts (embedded energy, subsidies, externalities).

---

## Table Stakes

These features are essential. Users expect them from any decision/comparison tool. Without them, users abandon the tool.

### Core Comparison Functionality
**What:** Side-by-side comparison layout with clear visual structure
**Why Table Stakes:** Users expect to see options compared in an easily scannable format. Standard across all comparison tools ([NN/G](https://www.nngroup.com/articles/comparison-tables/), [Smashing Magazine](https://www.smashingmagazine.com/2017/08/designing-perfect-feature-comparison-table/))
**Complexity:** Low - Standard table/card layout patterns
**Notes:** Use sticky headers, white space for readability, horizontal styling to separate rows

### Source Citations
**What:** Every claim/criterion must link to a verifiable source
**Why Table Stakes:** Trust is foundational for decision tools. Without citations, users can't verify AI claims ([Scite](https://scite.ai/), [GPTZero](https://gptzero.me/sources))
**Complexity:** Medium - Requires RAG system integration, citation extraction, link preservation
**Notes:** Show sources inline (not just at end), allow click-through to original content. AI citation accuracy rates vary (72-94% depending on domain)

### Clear Winner Indication
**What:** Visual indicator showing which option "wins" based on current weights
**Why Table Stakes:** Users need immediate clarity on the recommendation. Decision fatigue is real ([Asana](https://asana.com/resources/decision-matrix-examples))
**Complexity:** Low - Simple scoring calculation + visual badge/highlight
**Notes:** Must update in real-time as weights change

### Mobile Responsiveness
**What:** Works on phones/tablets with touch-friendly controls
**Why Table Stakes:** 50%+ of web traffic is mobile. Non-responsive tools get abandoned ([Baymard](https://baymard.com/blog/user-friendly-comparison-tools))
**Complexity:** Medium - Requires horizontal scroll or stacked view, touch-optimized sliders
**Notes:** Consider toggle between "full view" and "differences only" for mobile

### Save/Export Results
**What:** Users can download or save their comparison for later
**Why Table Stakes:** Decision-making is iterative. Users want to revisit analysis or share with others ([Xmind](https://xmind.com/blog/collaborative-decision-making-definition-and-tools))
**Complexity:** Low (file download) to Medium (cloud save with retrieval)
**Notes:** POC can start with JSON/PDF download before building cloud storage

### Loading States & Progress Indicators
**What:** Show that AI is working when researching options
**Why Table Stakes:** AI research takes 5-30+ seconds. Users need feedback to avoid thinking the app crashed
**Complexity:** Low - Spinner + progress messages
**Notes:** Consider showing "Researching Option A...", "Finding hidden costs...", etc.

---

## Differentiators

These features would set this tool apart from generic comparison sites and AI assistants. They create competitive advantage.

### Non-Obvious Criteria Discovery
**What:** AI actively searches for hidden/systemic impacts users wouldn't think of (embedded energy, subsidies, externalities)
**Why Differentiating:** Most comparison tools show what users already know. This surfaces invisible connections (Project requirement, predecessor project `orchids-option-analysis-ui`)
**Complexity:** High - Requires sophisticated prompting, domain knowledge, web search orchestration
**Notes:** This is THE core differentiator. Must be reliable or entire value prop fails

### Intent-Based Weighting
**What:** AI automatically weights criteria based on user's stated intent/priorities
**Why Differentiating:** Generic decision matrices make users assign all weights manually. This understands context ([Decision Matrix Pro](https://decisionmatrix.tools), [MyMap.AI](https://www.mymap.ai/decision-matrix-maker))
**Complexity:** Medium - Requires good prompt engineering + semantic understanding
**Notes:** Users can override, but smart defaults save cognitive load

### "What Would Flip This?" Analysis
**What:** Shows realistic actions that would change the losing option into the winner
**Why Differentiating:** Unique feature. Helps users understand decision sensitivity and find actionable paths forward
**Complexity:** High - Requires reverse-engineering scoring, understanding realistic constraints
**Notes:** Must avoid suggesting unrealistic changes ("if it was 90% cheaper..."). Focus on user-controllable variables

### Systemic Impact Focus
**What:** Prioritize criteria about systems (supply chains, externalities, subsidies) over individual attributes
**Why Differentiating:** Forces consideration of broader impacts. Educational component (Project motivation, predecessor project `orchids-option-analysis-ui`)
**Complexity:** Medium - Requires curated prompt templates, domain knowledge
**Notes:** Could maintain a library of "systemic impact categories" to guide search

### Interactive Weight Adjustment with Real-Time Recalculation
**What:** Sliders for each criterion that instantly update the winner when adjusted
**Why Differentiating:** Most decision tools require "recalculate" buttons. Immediate feedback enables exploration ([D-Sight](https://www.d-sight.com/sensitivity-analysis), [Prophix](https://www.prophix.com/blog/how-to-consider-the-what-ifs-in-times-of-uncertainty/))
**Complexity:** Low - Frontend calculation only
**Notes:** UX research shows sliders work best when precise values don't matter, only relative importance

### Source Quality Indicators
**What:** Show credibility signals for sources (peer-reviewed, government data, industry reports vs. blog posts)
**Why Differentiating:** Not all sources are equal. Helps users assess reliability ([Grammarly Citation Finder](https://www.grammarly.com/ai-agents/citation-finder), [Consensus](https://consensus.app))
**Complexity:** Medium - Requires source classification logic or API
**Notes:** Could use simple heuristics (.gov, .edu, journal domains) or AI classification

### "Go Deeper" Progressive Disclosure
**What:** Start with 3-5 criteria, allow users to request more analysis
**Why Differentiating:** Balances comprehensiveness with cognitive load. Most tools are all-or-nothing ([Perplexity](https://www.perplexity.ai), [Elicit](https://elicit.com))
**Complexity:** Medium - Requires stateful analysis, avoiding duplication
**Notes:** Each "go deeper" could add 2-3 more criteria, or drill into one existing criterion

### Confidence Scores for AI Claims
**What:** Show AI's certainty level for each criterion/data point
**Why Differentiating:** Helps users know which findings are solid vs. speculative. Builds trust ([DigitalOcean](https://www.digitalocean.com/resources/articles/ai-hallucination), [AWS Automated Reasoning](https://aws.amazon.com/blogs/aws/minimize-ai-hallucinations-and-deliver-up-to-99-verification-accuracy-with-automated-reasoning-checks-now-available/))
**Complexity:** High - Requires confidence scoring system, calibration
**Notes:** Could use source quality + claim specificity as confidence proxies if model-level scores unavailable

---

## Anti-Features

These are features to deliberately NOT build, despite users potentially asking for them or competitors having them.

### More Than 2 Options at Once
**Why NOT:** Cognitive overload. Comparison complexity grows exponentially (2 options = 1 comparison, 3 = 3 comparisons, 4 = 6 comparisons). Keep it simple (Project scope, predecessor project `orchids-option-analysis-ui`)
**Instead:** Allow sequential comparisons, but one head-to-head at a time
**Exception:** Could add in v2+ if users consistently request it

### Exhaustive Criteria Lists (10+ criteria by default)
**Why NOT:** Analysis paralysis. Users can't process too many dimensions simultaneously. Research shows 3-7 items is optimal for decision-making
**Instead:** Start with 3-5 most impactful criteria, use "Go Deeper" for more
**Exception:** Power users who explicitly request comprehensive analysis

### Collaborative/Multi-User Editing
**Why NOT:** Scope creep. Adds authentication, real-time sync, conflict resolution. Wrong focus for MVP (Project constraints, predecessor project `orchids-option-analysis-ui`)
**Instead:** Export/share read-only results. Users can discuss offline
**Exception:** Could add in future if this becomes a team decision tool

### Custom Criteria Input
**Why NOT:** Defeats the purpose. Core value is AI discovering non-obvious criteria. User-defined criteria = just another spreadsheet
**Instead:** Trust the AI to find hidden impacts based on intent
**Exception:** Could allow "also consider..." as supplementary input in v2

### Gamification/Social Features (upvoting, comments, sharing to social)
**Why NOT:** Distracts from core value. Adds moderation burden, privacy concerns. This is a thinking tool, not a social platform
**Instead:** Keep it focused on individual decision-making quality
**Exception:** Could add "export to image" for manual social sharing without in-app social features

### Price Tracking / Real-Time Updates
**Why NOT:** Maintenance nightmare. Requires ongoing web scraping, API integrations, staleness detection. Not core to hidden cost analysis
**Instead:** Analysis is point-in-time. Users can re-run if needed
**Exception:** None planned

### AI Chat Interface for Follow-Up Questions
**Why NOT:** Scope creep. Turns focused comparison tool into general chatbot. Dilutes the structured analysis value
**Instead:** Structured flows (adjust weights, go deeper, regenerate) cover exploration needs
**Exception:** Could add "explain this criterion" tooltips without full chat

---

## Feature Dependencies

Understanding which features rely on others for implementation or user value.

### Core Foundation Layer
These must exist first:
- **Source Citations** ← Everything depends on this for trust
- **Side-by-side Comparison Layout** ← Visual foundation
- **AI Research + Web Search Integration** ← Data source

### Dependent on Foundation
- **Non-Obvious Criteria Discovery** ← requires AI Research + Sources
- **Intent-Based Weighting** ← requires Criteria Discovery
- **Clear Winner Indication** ← requires Weighting
- **Mobile Responsiveness** ← requires Comparison Layout

### Enhancement Layer (can be added later)
- **Interactive Weight Adjustment** ← requires Winner Indication (to show updates)
- **"Go Deeper"** ← requires Criteria Discovery (to add more)
- **"What Would Flip This?"** ← requires Weighting + Winner (to reverse-engineer)
- **Source Quality Indicators** ← requires Source Citations (to classify)
- **Confidence Scores** ← requires AI Research (to assess certainty)
- **Save/Export** ← requires all above (to persist results)

### No Dependencies (can be added anytime)
- **Loading States** ← UI polish, independent
- **Progress Indicators** ← UI polish, independent

---

## Complexity Assessment

Rating each feature's implementation difficulty (Low/Medium/High) based on technical requirements, AI reliability needs, and UX challenges.

### Low Complexity (1-2 days)
- Side-by-side Comparison Layout
- Clear Winner Indication
- Loading States & Progress Indicators
- Interactive Weight Adjustment (frontend only)
- Save/Export Results (file download version)

### Medium Complexity (3-5 days)
- Source Citations (RAG integration)
- Intent-Based Weighting (prompt engineering)
- Mobile Responsiveness (responsive design)
- "Go Deeper" Progressive Disclosure (stateful analysis)
- Source Quality Indicators (classification logic)
- Systemic Impact Focus (prompt templates)

### High Complexity (5-10 days)
- Non-Obvious Criteria Discovery (core AI research orchestration)
- "What Would Flip This?" Analysis (reverse engineering)
- Confidence Scores for AI Claims (scoring system, calibration)

### Unknown/Research Required
- Avoiding AI hallucinations at scale (requires testing different prevention strategies)
- Optimal prompt structure for systemic impacts (needs iteration and validation)

---

## Key Insights from Research

### Comparison Tool Patterns
- **Scannability is king:** Use white space, alternating row colors, sticky headers ([Contentsquare](https://contentsquare.com/blog/comparing-products-design-practices-to-help-your-users-avoid-fragmented-comparison-7/))
- **"Show Differences" button highly valued:** Users want to hide identical attributes ([Baymard](https://baymard.com/blog/user-friendly-comparison-tools))
- **Mobile users scroll horizontally OR prefer vertical stacking:** Test both approaches

### AI Research Assistant Patterns
- **Perplexity model:** Fast, cited, conversational - good for quick research ([Index.dev](https://www.index.dev/blog/best-ai-tools-for-deep-research))
- **Elicit model:** Structured tables, academic focus, 125M papers - good for systematic review
- **Consensus model:** Shows scientific agreement/disagreement - good for controversial topics
- **Implication:** Different modes for different use cases. This tool leans toward Perplexity's speed + Consensus's synthesis

### Decision Matrix Tools
- **AI-assisted weighting is emerging:** Tools like Decision Matrix Pro, MyMap.AI now offer AI weight suggestions ([Decision Matrix Tools](https://decisionmatrix.tools))
- **Sensitivity analysis is power user feature:** Most users don't touch it, but those who do love it
- **Implication:** Make intent-based weighting automatic, sliders optional

### Source & Citation Patterns
- **Inline citations > end-of-doc citations:** Users need to verify specific claims, not hunt for sources ([Scite](https://scite.ai/))
- **Click-through to source is essential:** Don't just show URLs, make them actionable
- **Hallucination detection is hard:** GPTZero reports 72% accuracy on fact-checking, not 100% ([Medium](https://medium.com/@isabelgarciaphd/best-source-checking-apps-for-accurate-fact-verification-in-2025-03a8ca28704b))
- **Implication:** Prioritize source quality over source quantity. Better 3 solid sources than 10 questionable ones

### Cost Analysis Patterns
- **LCCA tools focus on Total Cost of Ownership:** Initial + operational + maintenance + end-of-life ([WBDG](https://www.wbdg.org/resources/life-cycle-cost-analysis-lcca))
- **Hidden costs are often overlooked:** Training, integration, disposal, externalities ([Business Case Analysis](https://www.business-case-analysis.com/total-cost-of-ownership.html))
- **Implication:** "Prism" aligns perfectly with LCCA methodology. This is a validated approach

### What-If Analysis Patterns
- **Real-time recalculation is expected:** Users adjust variables and see instant results ([Cube](https://www.cubesoftware.com/scenario-what-if-analysis))
- **Scenario comparison is common:** "Base case" vs "optimistic" vs "pessimistic" ([Epicflow](https://www.epicflow.com/features/what-if/))
- **Implication:** Weight sliders should update instantly, not require "recalculate" button

---

## Recommendations for MVP

### Must Have (Table Stakes)
1. Side-by-side comparison layout
2. Source citations (inline, clickable)
3. Clear winner indication
4. Loading states
5. Basic mobile support
6. Save results (JSON download)

### Should Have (Core Differentiators)
7. Non-obvious criteria discovery (THE value prop)
8. Intent-based weighting
9. Interactive weight sliders with real-time update
10. "What would flip this?" analysis

### Could Have (Nice-to-Have Differentiators)
11. "Go deeper" for more criteria
12. Source quality indicators
13. Confidence scores

### Won't Have (Anti-Features)
- More than 2 options
- 10+ default criteria
- Collaborative editing
- Custom criteria input
- Social features
- Real-time price tracking
- AI chat interface

---

## Sources

Research conducted on 2026-02-01 using web search. Key sources:

**AI Decision Tools:**
- [16 Best AI Decision-Making Software Reviewed in 2026](https://peoplemanagingpeople.com/tools/best-ai-decision-making-software/)
- [Decision Intelligence Platforms - Gartner](https://www.gartner.com/reviews/market/decision-intelligence-platforms)
- [Decision Matrix Pro](https://decisionmatrix.tools)
- [MyMap.AI Decision Matrix Maker](https://www.mymap.ai/decision-matrix-maker)

**Comparison Table UX:**
- [Comparison Tables - Nielsen Norman Group](https://www.nngroup.com/articles/comparison-tables/)
- [Designing Perfect Feature Comparison Table - Smashing Magazine](https://www.smashingmagazine.com/2017/08/designing-perfect-feature-comparison-table/)
- [4 Ways to Optimize Comparison Features - Baymard](https://baymard.com/blog/user-friendly-comparison-tools)
- [Comparing Products UX Best Practices - Contentsquare](https://contentsquare.com/blog/comparing-products-design-practices-to-help-your-users-avoid-fragmented-comparison-7/)

**AI Research Assistants:**
- [6 Best AI Tools for Deep Research](https://www.index.dev/blog/best-ai-tools-for-deep-research)
- [Top 10 AI Tools for Research - Julius AI](https://julius.ai/articles/top-10-ai-tools-for-research)
- [Scite AI](https://scite.ai/)

**Citations & Fact-Checking:**
- [8 Trusted AI Tools That Provide Sources Correctly](https://anara.com/blog/ai-referencing-sources)
- [GPTZero Citation Checker](https://gptzero.me/sources)
- [Grammarly Citation Finder](https://www.grammarly.com/ai-agents/citation-finder)
- [Best Source Checking Apps 2025 - Medium](https://medium.com/@isabelgarciaphd/best-source-checking-apps-for-accurate-fact-verification-in-2025-03a8ca28704b)

**Cost Analysis:**
- [Life-Cycle Cost Analysis - WBDG](https://www.wbdg.org/resources/life-cycle-cost-analysis-lcca)
- [Total Cost of Ownership - Business Case Analysis](https://www.business-case-analysis.com/total-cost-of-ownership.html)

**What-If Analysis:**
- [What-If Analysis - Epicflow](https://www.epicflow.com/features/what-if/)
- [Scenario Planning Software - Cube](https://www.cubesoftware.com/scenario-what-if-analysis)
- [Sensitivity Analysis - D-Sight](https://www.d-sight.com/sensitivity-analysis)

**Sensitivity Analysis & Sliders:**
- [Slider Design Rules - Nielsen Norman Group](https://www.nngroup.com/articles/gui-slider-controls/)
- [Weighting Criteria and Sensitivity Analysis](https://pressbooks.pub/decisions/chapter/11-3/)

**Collaboration Features:**
- [Loomio - Collaborative Decision Making](https://www.loomio.com/)
- [Collaborative Decision Making Tools](https://xmind.com/blog/collaborative-decision-making-definition-and-tools)

**AI Hallucination Prevention:**
- [Understanding AI Hallucination - DigitalOcean](https://www.digitalocean.com/resources/articles/ai-hallucination)
- [AWS Automated Reasoning Checks](https://aws.amazon.com/blogs/aws/minimize-ai-hallucinations-and-deliver-up-to-99-verification-accuracy-with-automated-reasoning-checks-now-available/)
- [Why Language Models Hallucinate - OpenAI](https://openai.com/index/why-language-models-hallucinate/)

---

*Last updated: 2026-02-01*
