# Pitfalls Research

## Critical Pitfalls

### 1. AI Hallucination in Decision Support
**The Problem**: AI hallucinations—where models generate plausible but incorrect information—poses significant risks for critical decision makers. Studies show hallucination rates of 69-88% when AI responds to specific queries without proper grounding. In 2025, judges worldwide issued hundreds of decisions addressing AI hallucinations in legal filings.

**Warning Signs**:
- AI generates criteria or facts without citing sources
- Contradictions between different API responses
- Inability to trace claims back to source material
- Confidence scores don't match actual accuracy (68% higher confidence-calibration failures vs. human experts)

**Prevention Strategy**:
- **MANDATORY**: All criteria, weights, and facts MUST have source citations from Tavily
- Implement multi-source verification for critical claims
- Use retrieval-augmented generation (RAG) patterns
- Show confidence indicators alongside all AI-generated content
- Never allow the system to make assertions without grounding in search results

**Phase to Address**: Phase 1 (MVP) - This is a fundamental requirement that cannot be deferred

**References**:
- [AI Hallucination: Compare top LLMs](https://research.aimultiple.com/ai-hallucination/)
- [Understanding and Mitigating AI Hallucination](https://www.digitalocean.com/resources/articles/ai-hallucination)
- [Diagnosing Hallucination Risk in AI Decision-Support](https://arxiv.org/html/2511.00588v1)

---

### 2. Source Reliability and Dead Links
**The Problem**: Tavily and other search APIs can return 404s or dead pages, pulling from cached or indexed sources that haven't been revalidated. Most AI systems are trained on massive datasets without disclosing sources, requiring users to verify AI citations themselves.

**Warning Signs**:
- 404 errors when users click source links
- Sources dated years before current information
- Contradictory information between sources
- Inability to verify claims through provided sources
- Fabricated citations (AI creating fake references)

**Prevention Strategy**:
- Implement link validation layer before displaying to users
- Add "Last verified" timestamps to sources
- Provide fallback when sources are unavailable
- Cache source content at time of analysis
- Allow users to flag dead/unreliable sources
- Set Tavily max_results to 10 for better quality

**Phase to Address**: Phase 1 (MVP) - Core to the "all information must have sources" requirement

**References**:
- [Is Tavily a reliable web search tool](https://github.com/orgs/community/discussions/167015)
- [Best Practices for Search - Tavily](https://docs.tavily.com/documentation/best-practices/best-practices-search)
- [Source attribution and detection strategies](https://www.sciencedirect.com/science/article/pii/S0308596125001508)

---

### 3. Criteria Weight Bias and Subjectivity
**The Problem**: AI-generated weights can accumulate biases through the preference elicitation process, potentially favoring certain criteria repeatedly. Traditional methods suffer from anchoring bias, loss aversion bias, and scale compatibility issues. This leads to selection of inferior alternatives.

**Warning Signs**:
- Weights that seem intuitively wrong to users
- Same criteria always weighted highest across different comparisons
- Inability to explain why specific weights were assigned
- Weights that don't align with user's stated priorities
- Deterministic weights perceived as subjective by users

**Prevention Strategy**:
- Make weight generation transparent with explanations
- Allow easy user adjustment of weights
- Show sensitivity analysis (what would flip the outcome)
- Provide multiple weighting methodologies as options
- Document the rationale for each weight assignment with sources
- Test with diverse user scenarios to detect systematic biases

**Phase to Address**: Phase 1 (MVP) for basic transparency, Phase 2 for advanced sensitivity analysis

**References**:
- [Comparison of weighting methods in MCDA](https://becarispublishing.com/doi/10.2217/cer-2018-0102)
- [On preference elicitation processes which mitigate bias](https://www.sciencedirect.com/science/article/abs/pii/S0377221719307428)
- [Comprehensive Review of Novel Weighting Methods](https://www.mdpi.com/2078-2489/14/5/285)

---

### 4. Cost Explosion from Unoptimized API Usage
**The Problem**: AI applications can generate unexpected costs through inefficient prompt design, lack of caching, unnecessary API calls, and unmonitored usage. Batch processing alone offers 50% savings, while prompt caching provides 90% savings on repeated content.

**Warning Signs**:
- Monthly API bills growing faster than user growth
- Same prompts/system messages sent repeatedly
- Long context windows with mostly static content
- No batching of similar requests
- Token usage spikes during testing/development
- Lack of per-request cost visibility

**Prevention Strategy**:
- Implement prompt caching for system prompts (90% cost reduction)
- Use batch processing where 24-hour latency acceptable (50% discount)
- Start with Haiku for lightweight tasks, only use Sonnet/Opus when needed
- Set daily spending caps in dev/staging ($50/day ceiling)
- Monitor token usage by feature/request type
- Trim prompts to minimum needed length
- Cache Tavily results for repeated queries
- Implement rate limiting and request deduplication

**Phase to Address**: Phase 1 (MVP) for basic monitoring, Phase 2 for advanced optimization

**References**:
- [FinOps For Claude: Managing Costs at Scale](https://www.cloudzero.com/blog/finops-for-claude/)
- [Manage costs effectively - Claude Code](https://code.claude.com/docs/en/costs)
- [Optimize Hidden Costs of Claude APIs](https://blog.cloudbuckle.com/how-to-optimize-the-hidden-costs-of-anthropic-claude-apis-part-1-ce52d08ae3e4)

---

### 5. Pilot-to-Production Failure
**The Problem**: 54% of AI projects fail to move from pilot to production. Failures rarely stem from model underperformance; instead, they result from organizational misalignment, undefined success metrics, and unfit underlying processes.

**Warning Signs**:
- No clear business value metric defined
- Different stakeholders measuring success differently
- Proof of concept works but can't scale
- No named owner responsible for outcomes
- Technology focus without process redesign

**Prevention Strategy**:
- Define clear success metrics before building
- Identify specific user pain points being solved
- Start with smallest viable scope
- Get user feedback early and often
- Ensure infrastructure can handle production load
- Plan for human oversight and intervention paths

**Phase to Address**: Pre-Phase 1 (Planning) - Define success criteria upfront

**References**:
- [AI in Decision Making: Benefits & Examples](https://intellias.com/ai-decision-making/)
- [Avoiding AI Pitfalls in 2026](https://www.isaca.org/resources/news-and-trends/isaca-now-blog/2025/avoiding-ai-pitfalls-in-2026-lessons-learned-from-top-2025-incidents)

---

## Common Mistakes

### 6. Over-Reliance on AI Without Human Oversight
**The Problem**: Despite AI capabilities, humans should not depend excessively on AI. Muted human oversight can lead to critical failures. A balance must be struck between AI assistance and human judgment.

**Warning Signs**:
- No ability to override AI decisions
- No human review before final decisions
- Users treating AI outputs as absolute truth
- No explanation of AI reasoning process
- Inability to contest or question AI conclusions

**Prevention Strategy**:
- Always present AI analysis as decision support, not decisions
- Provide clear "Edit" and "Override" options
- Show reasoning and sources for all recommendations
- Add disclaimers about AI limitations
- Enable users to add their own criteria/weights
- Maintain audit trail of user modifications

**Phase to Address**: Phase 1 (MVP) - Fundamental to responsible AI design

**References**:
- [AI for Decision Making - PagerDuty](https://www.pagerduty.com/resources/ai/learn/ai-decision-making/)
- [Three Challenges for AI-Assisted Decision-Making](https://pmc.ncbi.nlm.nih.gov/articles/PMC11373149/)

---

### 7. Black Box Problem and Lack of Explainability
**The Problem**: AI systems operate as "black boxes" where internal logic isn't easily understood. This leads to mistrust, especially in critical decisions. Users need to understand why a decision was made.

**Warning Signs**:
- Users ask "why?" and can't get answers
- No visible reasoning process
- Inability to trace decisions back to inputs
- Technical jargon instead of plain explanations
- Users abandon tool due to lack of trust

**Prevention Strategy**:
- Show step-by-step reasoning process
- Provide plain-language explanations for weights
- Link every claim to specific sources
- Use progressive disclosure for technical details
- Explain what criteria were considered and why
- Show alternative outcomes and what would change them

**Phase to Address**: Phase 1 (MVP) for basic explanations, Phase 2 for advanced reasoning traces

**References**:
- [AI Decision Making: Challenges & Costs](https://euristiq.com/ai-decision-making/)
- [Building User Trust in UX Design](https://medium.com/@thefinchdesignagency/building-user-trust-in-ux-design-proven-strategies-for-better-engagement-c975aa381516)

---

### 8. Poor Data Quality Leading to Misleading Decisions
**The Problem**: AI outputs are only as good as their inputs. Incomplete, outdated, or biased search results can lead to misleading or harmful decisions.

**Warning Signs**:
- Outdated information in search results
- Missing critical context
- Biased or one-sided sources
- Incomplete coverage of important factors
- Sources from unreliable domains

**Prevention Strategy**:
- Validate source recency and relevance
- Use multiple search queries for comprehensive coverage
- Allow users to request additional sources
- Show information gaps clearly
- Implement source diversity checks
- Date-stamp all retrieved information
- Allow users to add their own sources/knowledge

**Phase to Address**: Phase 1 (MVP) for source quality basics, Phase 2 for advanced validation

**References**:
- [When AI goes wrong: 13 examples of failures](https://www.evidentlyai.com/blog/ai-failures-examples)
- [What 2025 Taught Us About Data, AI, and Decision-Making](https://www.turningdataintowisdom.com/what-2025-taught-us-about-data-ai-and-decision-making/)

---

## UX Pitfalls

### 9. Slow Response Times Creating Frustration
**The Problem**: AI API calls can take 10-30+ seconds. Without proper UX, users perceive the tool as broken or unresponsive. Studies show users see 70% reduction in perceived wait time with streaming.

**Warning Signs**:
- Users refresh page thinking it's frozen
- No indication of progress
- Abrupt transitions from loading to results
- Timeout errors surprising users
- Users abandoning during long waits

**Prevention Strategy**:
- Implement streaming responses (SSE or ReadableStreams)
- Show granular progress: "Searching web...", "Analyzing sources...", "Generating criteria..."
- Display partial results as they arrive
- Set realistic timeout expectations (mention 30-60 second waits)
- Provide ability to cancel long-running requests
- Show token-by-token streaming for AI text
- Test with slow networks

**Phase to Address**: Phase 1 (MVP) - Critical for acceptable UX

**References**:
- [Stop Making Users Wait: Ultimate Guide to Streaming](https://dev.to/programmingcentral/stop-making-users-wait-the-ultimate-guide-to-streaming-ai-responses-22m3)
- [Real-time AI: Streaming with Vercel AI SDK](https://blog.logrocket.com/nextjs-vercel-ai-sdk-streaming/)
- [AI SDK RSC: Handling Loading State](https://ai-sdk.dev/docs/ai-sdk-rsc/loading-state)

---

### 10. Information Overload and Cognitive Burden
**The Problem**: Comparison tools can overwhelm users with too much information, making decisions harder instead of easier. Users need clarity, not cleverness.

**Warning Signs**:
- Users taking longer to decide after using tool
- Confusion about what information is important
- Users ignoring most displayed information
- Requests to "simplify" or "just tell me"
- High bounce rates on results page

**Prevention Strategy**:
- Progressive disclosure: show summary first, details on demand
- Highlight top 3-5 most important criteria
- Use visual hierarchy to emphasize key findings
- Provide "Quick Answer" view vs "Detailed Analysis"
- Allow filtering/hiding of less relevant criteria
- Limit initial criteria to 5-7 (human working memory limit)
- Use comparison tables, not just text

**Phase to Address**: Phase 1 (MVP) for basic hierarchy, Phase 2 for advanced customization

**References**:
- [Comparing products: UX design best practices](https://contentsquare.com/blog/comparing-products-design-practices-to-help-your-users-avoid-fragmented-comparison-7/)
- [13 Proven Error Fixes for User Trust](https://standardbeagle.com/improving-user-trust-through-ux-design/)

---

### 11. Loss of User Control and Agency
**The Problem**: When AI makes too many decisions automatically, users feel powerless. Speed without control feels risky. Prediction-driven UI that auto-fills and auto-decides can backfire.

**Warning Signs**:
- Users can't modify AI decisions
- No undo/redo functionality
- Auto-submission without confirmation
- Can't adjust individual criteria or weights
- No way to add domain knowledge AI missed

**Prevention Strategy**:
- Every AI decision should be editable
- Provide clear "Regenerate with different approach" option
- Allow manual addition of criteria
- Enable weight sliders for easy adjustment
- Show what-if scenarios
- Never auto-commit to decisions
- Confirm before actions with consequences

**Phase to Address**: Phase 1 (MVP) - Core to user trust and usability

**References**:
- [What failed UI/UX design case studies teach](https://roboticsandautomationnews.com/2026/01/29/what-can-you-learn-from-failed-ui-ux-design-case-studies/98350/)
- [Good vs Bad UX Design: Examples](https://tsttechnology.io/blog/good-and-bad-ux-design-examples)

---

### 12. Poor Mobile Experience
**The Problem**: Comparison interfaces often fail on mobile with poor touch targets, small text, horizontal scrolling, and information density that doesn't adapt.

**Warning Signs**:
- Users zooming to read content
- Horizontal scrolling required
- Buttons too small to tap
- Tables don't fit viewport
- High mobile bounce rate

**Prevention Strategy**:
- Mobile-first design approach
- Collapsible sections for dense information
- Vertical card layouts instead of tables on mobile
- Touch-friendly controls (min 44px tap targets)
- Test on actual mobile devices
- Consider mobile context (shorter sessions)

**Phase to Address**: Phase 1 (MVP) for responsive basics, Phase 2 for mobile optimization

**References**:
- [7 UX Mistakes Everyone Makes](https://www.crazyegg.com/blog/ux-mistakes-every-unknowingly-commits/)
- [How to Avoid Common UX Design Mistakes](https://blog.pixelfreestudio.com/how-to-avoid-common-ux-design-mistakes/)

---

## Technical Pitfalls

### 13. Inadequate Error Handling and Resilience
**The Problem**: Network issues can interrupt streams, API rate limits can be hit, search APIs can fail, and LLMs can timeout. Without proper handling, users see cryptic errors or complete failures.

**Warning Signs**:
- White screen of death on errors
- Generic "Something went wrong" messages
- Lost work when errors occur
- No retry mechanism
- Errors that require page refresh

**Prevention Strategy**:
- Implement exponential backoff retry logic
- Graceful degradation (partial results if one source fails)
- Save user inputs before API calls
- Provide specific, actionable error messages
- Fallback to cached results when available
- Circuit breaker pattern for failing services
- Handle rate limiting transparently

**Phase to Address**: Phase 1 (MVP) for basic handling, Phase 2 for advanced resilience

**References**:
- [AI SDK: Handling Loading State](https://ai-sdk.dev/docs/ai-sdk-rsc/loading-state)
- [Building responsive APIs with response streaming](https://aws.amazon.com/blogs/compute/building-responsive-apis-with-amazon-api-gateway-response-streaming/)

---

### 14. Insufficient Testing with Edge Cases
**The Problem**: AI tools often work well for common cases but fail with unusual inputs, controversial topics, or incomplete information.

**Warning Signs**:
- Works in demo, fails in production
- Breaks with very short/long option names
- Can't handle ties or near-ties
- Fails when few sources available
- Errors with special characters

**Prevention Strategy**:
- Test with minimal inputs (1-word options)
- Test with maximal inputs (paragraph-length)
- Test controversial comparisons
- Test with low-quality search results
- Test with no clear winner
- Test with exact ties
- Test timeout scenarios
- Load testing with concurrent users

**Phase to Address**: Phase 1 (MVP) for basic edge cases, Ongoing for discovered issues

---

### 15. Poor Caching Strategy
**The Problem**: Regenerating identical comparisons wastes money and time. But over-caching can serve stale results.

**Warning Signs**:
- Same comparison takes same time every run
- Results don't update with new information
- API costs scale linearly with usage
- No cache invalidation strategy

**Prevention Strategy**:
- Cache Tavily search results (time-based: 24 hours)
- Cache full analyses with TTL (1-7 days)
- Show cache age to users
- Allow "Refresh with latest data" option
- Hash comparison inputs for cache keys
- Implement cache warming for popular comparisons
- Respect Tavily rate limits through caching

**Phase to Address**: Phase 2 (Optimization) - Not critical for MVP but important for scale

**References**:
- [Manage costs effectively](https://code.claude.com/docs/en/costs)
- [Optimizing Your Request Parameters - Tavily](https://help.tavily.com/articles/7879881576-optimizing-your-query-parameters)

---

## Cost Pitfalls

### 16. Uncontrolled Development/Testing Costs
**The Problem**: Development and testing can rack up API costs through repeated runs, forgotten test instances, and lack of spending limits.

**Warning Signs**:
- Dev environment costs approaching production
- Test API keys with unlimited budgets
- No visibility into who/what generated costs
- Surprise bills at month end
- CI/CD running full comparisons

**Prevention Strategy**:
- Set $50/day caps on dev/staging environments
- Use shorter prompts and cheaper models (Haiku) for testing
- Mock API responses in unit tests
- Implement cost attribution by environment/developer
- Regular API key audits (retire unused)
- Test with cached responses when possible
- Monitor token usage in CI/CD

**Phase to Address**: Phase 1 (MVP) - Set up from day one

**References**:
- [FinOps For Claude: Cost Management](https://www.cloudzero.com/blog/finops-for-claude/)
- [Managing Costs and Token Usage](https://stevekinney.com/courses/ai-development/cost-management)

---

### 17. Inefficient Prompt Engineering
**The Problem**: Verbose prompts, unnecessary context, and poor structure waste tokens and slow responses. Vague requests trigger broad scanning.

**Warning Signs**:
- Prompts over 1000 tokens
- Repeating same context in every request
- AI generating unnecessary verbose output
- Long generation times
- High cost per comparison

**Prevention Strategy**:
- Use prompt caching for static system prompts
- Be specific: "Generate 5 criteria" not "think about criteria"
- Limit output: "Max 100 words" not unbounded
- Remove unnecessary preambles
- Use structured outputs (JSON) when possible
- A/B test prompt variations for cost/quality
- Version control prompts for iteration

**Phase to Address**: Phase 1 (MVP) for baseline, Phase 2 for optimization

**References**:
- [Claude API Pricing Guide 2026](https://www.aifreeapi.com/en/posts/claude-api-pricing-per-million-tokens)
- [The Truth About Claude API Pricing](https://apidog.com/blog/claude-api-cost/)

---

### 18. Scaling Cost Explosions
**The Problem**: Costs that seem fine at 10 users/day become unsustainable at 1000 users/day. Linear cost scaling can kill a product.

**Warning Signs**:
- Cost per user stays constant as you grow
- No volume discounts negotiated
- Every comparison costs same regardless of complexity
- Margins shrinking as usage grows
- Can't afford customer acquisition at scale

**Prevention Strategy**:
- Implement tiered pricing (free tier with limits)
- Cache popular comparisons aggressively
- Use batch processing for non-urgent analyses
- Negotiate volume discounts with Anthropic/Tavily
- Consider serving cached results for common queries
- Implement rate limiting per user
- Monitor cost per user metric
- Plan pricing model around unit economics

**Phase to Address**: Phase 2 (Growth) - Before significant user scaling

**References**:
- [Anthropic API Pricing: Complete Guide](https://www.finout.io/blog/anthropic-api-pricing)
- [FinOps For Claude at Scale](https://www.cloudzero.com/blog/finops-for-claude/)

---

## Prevention Strategies by Phase

### Pre-Phase 1 (Planning)
**Focus**: Prevent strategic failures
- Define clear success metrics (#5)
- Identify specific user pain points (#5)
- Plan cost management approach (#4, #16)
- Design for explainability from start (#7)

### Phase 1 (MVP)
**Focus**: Prevent critical functional failures
- **MUST HAVE**:
  - All claims sourced from Tavily (#1)
  - Link validation for sources (#2)
  - User-editable weights (#3, #11)
  - Basic cost monitoring (#4, #16)
  - Streaming responses (#9)
  - Human oversight/editing (#6)
  - Basic error handling (#13)
  - Mobile-responsive design (#12)

### Phase 2 (Enhancement)
**Focus**: Prevent scaling and UX issues
- Advanced sensitivity analysis (#3)
- Caching strategy (#15)
- Prompt optimization (#17)
- Advanced loading states (#9)
- Information hierarchy refinement (#10)
- Edge case testing (#14)
- Cost optimization (#17, #18)

### Phase 3 (Scale)
**Focus**: Prevent growth failures
- Volume pricing negotiations (#18)
- Advanced caching for popular queries (#15)
- Performance optimization (#9)
- A/B testing for UX improvements (#10, #11)
- Multi-model cost optimization (#4)

---

## Quick Reference: Detection Checklist

Use this checklist during development and testing:

**Every API Call:**
- [ ] Is this result cached? Should it be?
- [ ] Are we using the cheapest appropriate model?
- [ ] Is the prompt minimal and specific?
- [ ] Do we have retry logic?
- [ ] Are we streaming the response?

**Every Displayed Result:**
- [ ] Does every claim have a source?
- [ ] Are source links validated/reachable?
- [ ] Can the user edit/override this?
- [ ] Is the reasoning explained?
- [ ] Is critical information visible without scrolling?

**Every Feature:**
- [ ] What happens if the API fails?
- [ ] What happens if this takes 60 seconds?
- [ ] What happens on mobile?
- [ ] What happens with unusual inputs?
- [ ] Is there a cost limit on this feature?

**Before Launch:**
- [ ] Have we tested edge cases?
- [ ] Do we have cost monitoring?
- [ ] Can users undo mistakes?
- [ ] Is there human oversight?
- [ ] Are we measuring the right success metrics?

---

## Sources

### AI Decision Making & Pitfalls
- [AI in Decision Making: Benefits & Examples - Intellias](https://intellias.com/ai-decision-making/)
- [AI for Decision Making - PagerDuty](https://www.pagerduty.com/resources/ai/learn/ai-decision-making/)
- [AI Decision Making: Challenges & Costs - Euristiq](https://euristiq.com/ai-decision-making/)
- [Avoiding AI Pitfalls in 2026 - ISACA](https://www.isaca.org/resources/news-and-trends/isaca-now-blog/2025/avoiding-ai-pitfalls-in-2026-lessons-learned-from-top-2025-incidents)
- [Three Challenges for AI-Assisted Decision-Making - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11373149/)
- [When AI goes wrong: 13 examples - Evidently AI](https://www.evidentlyai.com/blog/ai-failures-examples)
- [What 2025 Taught Us About Data, AI, and Decision-Making](https://www.turningdataintowisdom.com/what-2025-taught-us-about-data-ai-and-decision-making/)

### AI Hallucination & Reliability
- [Why language models hallucinate - OpenAI](https://openai.com/index/why-language-models-hallucinate/)
- [AI Hallucination: Compare top LLMs - AIM](https://research.aimultiple.com/ai-hallucination/)
- [Understanding and Mitigating AI Hallucination - DigitalOcean](https://www.digitalocean.com/resources/articles/ai-hallucination)
- [Diagnosing Hallucination Risk in AI Surgical Decision-Support - arXiv](https://arxiv.org/html/2511.00588v1)
- [Addressing AI Hallucinations and Bias - MIT Sloan](https://mitsloanedtech.mit.edu/ai/basics/addressing-ai-hallucinations-and-bias/)

### Cost Management & Optimization
- [Usage and Cost API - Claude Docs](https://platform.claude.com/docs/en/build-with-claude/usage-cost-api)
- [Manage costs effectively - Claude Code](https://code.claude.com/docs/en/costs)
- [The Truth About Claude API Pricing - Apidog](https://apidog.com/blog/claude-api-cost/)
- [FinOps For Claude - CloudZero](https://www.cloudzero.com/blog/finops-for-claude/)
- [Managing Costs and Token Usage - Steve Kinney](https://stevekinney.com/courses/ai-development/cost-management)
- [Anthropic API Pricing Guide - Finout](https://www.finout.io/blog/anthropic-api-pricing)
- [Optimize Hidden Costs of Claude APIs - CloudBuckle](https://blog.cloudbuckle.com/how-to-optimize-the-hidden-costs-of-anthropic-claude-apis-part-1-ce52d08ae3e4)

### UX Design & User Trust
- [Comparing products: UX design best practices - Contentsquare](https://contentsquare.com/blog/comparing-products-design-practices-to-help-your-users-avoid-fragmented-comparison-7/)
- [Building User Trust in UX Design - Medium](https://medium.com/@thefinchdesignagency/building-user-trust-in-ux-design-proven-strategies-for-better-engagement-c975aa381516)
- [What failed UI/UX design case studies teach - Robotics News](https://roboticsandautomationnews.com/2026/01/29/what-can-you-learn-from-failed-ui-ux-design-case-studies/98350/)
- [Good vs Bad UX Design Examples - TST Technology](https://tsttechnology.io/blog/good-and-bad-ux-design-examples)
- [13 Proven Error Fixes for User Trust - Standard Beagle](https://standardbeagle.com/improving-user-trust-through-ux-design/)
- [7 UX Mistakes Everyone Makes - CrazyEgg](https://www.crazyegg.com/blog/ux-mistakes-every-unknowingly-commits/)

### Multi-Criteria Decision Analysis & Weighting
- [Comparison of weighting methods in MCDA - BECARIS](https://becarispublishing.com/doi/10.2217/cer-2018-0102)
- [What is Multi-Criteria Decision Analysis - All About AI](https://www.allaboutai.com/ai-glossary/multi-criteria-decision-analysis/)
- [On preference elicitation processes which mitigate bias - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0377221719307428)
- [Comprehensive Review of Novel Weighting Methods - MDPI](https://www.mdpi.com/2078-2489/14/5/285)

### Source Attribution & Transparency
- [Transparency & Attribution: Citing AI Tools - University of Calgary](https://libguides.ucalgary.ca/c.php?g=733971&p=5302331)
- [How to Cite AI-Generated Content - Sourcely](https://www.sourcely.net/post/how-to-cite-ai-generated-content-guidelines-for-chatgpt-claude-and-other-ai-tools)
- [How different AI engines generate and cite answers - Search Engine Land](https://searchengineland.com/how-different-ai-engines-generate-and-cite-answers-463234)
- [Source attribution strategies for AI-era journalism - ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0308596125001508)

### Tavily Search API
- [Best Practices for Search - Tavily Docs](https://docs.tavily.com/documentation/best-practices/best-practices-search)
- [Is Tavily a reliable web search tool - GitHub](https://github.com/orgs/community/discussions/167015)
- [Optimizing Your Query Parameters - Tavily](https://help.tavily.com/articles/7879881576-optimizing-your-query-parameters)
- [AI Search APIs Compared: Tavily vs Exa vs Perplexity](https://www.humai.blog/ai-search-apis-compared-tavily-vs-exa-vs-perplexity/)

### Streaming & Performance
- [Stop Making Users Wait: Streaming AI Responses - DEV](https://dev.to/programmingcentral/stop-making-users-wait-the-ultimate-guide-to-streaming-ai-responses-22m3)
- [From Waiting to Streaming: Handle LLM Responses - DEV](https://dev.to/abhinav__ap/from-waiting-to-streaming-how-to-handle-llm-responses-like-a-pro-especially-with-json-2lgh)
- [AI SDK RSC: Handling Loading State - Vercel](https://ai-sdk.dev/docs/ai-sdk-rsc/loading-state)
- [Real-time AI: Streaming with Vercel AI SDK - LogRocket](https://blog.logrocket.com/nextjs-vercel-ai-sdk-streaming/)
- [Building responsive APIs with response streaming - AWS](https://aws.amazon.com/blogs/compute/building-responsive-apis-with-amazon-api-gateway-response-streaming/)
