# Phase 2: AI Integration + Async Orchestration - Research

**Researched:** 2026-02-07
**Domain:** AI API Integration, Async Processing, Structured Outputs
**Confidence:** HIGH

## Summary

Phase 2 integrates Claude API for criteria generation and Tavily Search API for web research, implementing async orchestration with real-time progress streaming. The research confirms that the planned 202 Accepted + polling pattern from Phase 1 is production-ready, and identifies Server-Sent Events (SSE) as the optimal approach for streaming progress updates to the frontend.

**Key findings:**
- Claude's structured outputs (JSON mode) guarantee schema-compliant responses, eliminating retry logic
- Prompt caching provides 90% cost reduction on repeated context (system prompts, tools)
- Tavily's AsyncTavilyClient enables parallel searches for both options simultaneously
- FastAPI's native SSE support via StreamingResponse is simpler than WebSockets for unidirectional updates
- Python's asyncio.gather() is the standard pattern for parallel AI calls in FastAPI

**Primary recommendation:** Use Claude's structured outputs with Pydantic models for criteria generation, implement prompt caching for system prompts and tools, run Tavily searches in parallel with asyncio.gather(), and stream progress via SSE to frontend EventSource.

## Standard Stack

The established libraries/tools for this domain:

### Core AI APIs
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| anthropic | >=0.40.0 | Claude API client (structured outputs, streaming, caching) | Official SDK with excellent async support, type hints, structured outputs |
| tavily-python | >=0.7.21 | Web search API for source citations | Purpose-built for LLM/AI agents, returns structured data with sources |

### Supporting Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | >=0.27.0 | Async HTTP client | Already in stack (Phase 1 research), handles both Tavily and Claude API calls |
| pydantic | >=2.10.0 | Validation and structured outputs | Already in stack, transforms to/from Claude's JSON schemas |
| sse-starlette | >=2.2.1 | SSE streaming support for FastAPI | Simplifies SSE implementation, handles connection management |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SSE | WebSockets | WebSockets are bidirectional but more complex; SSE is simpler for unidirectional server-to-client streaming |
| FastAPI BackgroundTasks | Celery/RQ | Celery adds Redis dependency; BackgroundTasks sufficient for POC with atomic JSON storage |
| Claude structured outputs | Instructor library | Instructor adds abstraction layer; native SDK is simpler and officially supported |

**Installation:**
```bash
pip install anthropic>=0.40.0 tavily-python>=0.7.21 sse-starlette>=2.2.1
```

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── routers/
│   └── comparison.py        # Existing 202 Accepted pattern
├── services/
│   ├── claude_service.py    # Criteria generation + weighting
│   ├── tavily_service.py    # Web search orchestration
│   └── orchestrator.py      # Parallel research + criteria synthesis
├── models.py                # Pydantic models (existing)
└── storage.py               # Atomic JSON writes (existing)
```

### Pattern 1: Structured Outputs with Pydantic

**What:** Use Claude's native structured outputs to guarantee schema-compliant JSON responses
**When to use:** Any Claude API call that needs predictable JSON structure (criteria, weights, reasoning)
**Example:**
```python
# Source: https://platform.claude.com/docs/en/build-with-claude/structured-outputs
from anthropic import AsyncAnthropic
from pydantic import BaseModel

class Criterion(BaseModel):
    id: str
    name: str
    description: str
    score_a: float
    score_b: float
    weight: float
    sources: list[str]

class CriteriaOutput(BaseModel):
    criteria: list[Criterion]
    reasoning: str

client = AsyncAnthropic()

response = await client.messages.parse(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    messages=[{"role": "user", "content": prompt}],
    output_format=CriteriaOutput,  # SDK handles schema transformation
)

# response.parsed_output is type-safe CriteriaOutput instance
criteria = response.parsed_output.criteria
```

**Key benefits:**
- No retry logic for malformed JSON
- Type-safe parsed output
- SDK automatically transforms Pydantic models to Claude's JSON schema format

### Pattern 2: Prompt Caching for Cost Reduction

**What:** Cache static system prompts and tool definitions to reduce input token costs by 90%
**When to use:** Any content that repeats across requests (system prompts, tool definitions, examples)
**Example:**
```python
# Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
response = await client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    system=[
        {
            "type": "text",
            "text": "You are an AI that discovers non-obvious criteria...",
        },
        {
            "type": "text",
            "text": "# Examples of non-obvious criteria:\n1. Embedded energy...",
            "cache_control": {"type": "ephemeral"}  # Cache this block
        }
    ],
    messages=[{"role": "user", "content": f"Compare {option_a} vs {option_b}"}]
)

# First request: cache_creation_input_tokens = system prompt tokens
# Subsequent requests: cache_read_input_tokens = system prompt tokens (90% cheaper)
```

**Cost impact:**
- Cache write: 1.25x base price (one-time)
- Cache read: 0.1x base price (90% savings)
- 5-minute TTL, refreshed on each use

### Pattern 3: Parallel Async Orchestration

**What:** Run independent AI operations concurrently using asyncio.gather()
**When to use:** When researching multiple options or calling multiple APIs that don't depend on each other
**Example:**
```python
# Source: https://docs.tavily.com/documentation/best-practices/best-practices-search
import asyncio
from tavily import AsyncTavilyClient

async def research_option(option: str, tavily: AsyncTavilyClient) -> dict:
    """Research a single option via web search."""
    search_results = await tavily.search(
        query=f"{option} hidden costs environmental impact subsidies",
        search_depth="basic",
        max_results=10
    )
    return search_results

async def research_both_options(option_a: str, option_b: str):
    """Research both options in parallel."""
    tavily = AsyncTavilyClient()

    results_a, results_b = await asyncio.gather(
        research_option(option_a, tavily),
        research_option(option_b, tavily),
        return_exceptions=True  # Continue if one fails
    )

    return results_a, results_b
```

### Pattern 4: SSE Streaming Progress

**What:** Stream real-time progress updates from backend to frontend via Server-Sent Events
**When to use:** Long-running operations where user needs feedback (AI processing, web searches)
**Example:**
```python
# Source: https://mahdijafaridev.medium.com/implementing-server-sent-events-sse-with-fastapi-real-time-updates-made-simple-6492f8bfc154
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
import asyncio

router = APIRouter()

async def progress_generator(comparison_id: str):
    """Generate progress events for streaming."""
    yield {"event": "progress", "data": '{"status": "Searching web for option A..."}'}
    await asyncio.sleep(0.1)

    yield {"event": "progress", "data": '{"status": "Searching web for option B..."}'}
    await asyncio.sleep(0.1)

    yield {"event": "progress", "data": '{"status": "Analyzing sources..."}'}
    await asyncio.sleep(0.1)

    yield {"event": "progress", "data": '{"status": "Generating criteria..."}'}
    await asyncio.sleep(0.1)

    yield {"event": "complete", "data": f'{{"comparison_id": "{comparison_id}"}}'}

@router.get("/api/progress/{comparison_id}")
async def stream_progress(comparison_id: str):
    return EventSourceResponse(progress_generator(comparison_id))
```

**Frontend consumption (React):**
```typescript
// Source: https://oneuptime.com/blog/post/2026-01-15-server-sent-events-sse-react/view
useEffect(() => {
  const eventSource = new EventSource(`/api/progress/${comparisonId}`);

  eventSource.addEventListener('progress', (event) => {
    const data = JSON.parse(event.data);
    setStatus(data.status);
  });

  eventSource.addEventListener('complete', (event) => {
    const data = JSON.parse(event.data);
    setComplete(true);
    eventSource.close();
  });

  return () => eventSource.close();
}, [comparisonId]);
```

### Pattern 5: Error Handling with Exponential Backoff

**What:** Retry failed API calls with exponential delays and jitter
**When to use:** Any API call (Claude, Tavily) that might fail due to rate limits or transient errors
**Example:**
```python
# Source: https://www.aifreeapi.com/en/posts/fix-claude-api-429-rate-limit-error
import asyncio
import random
from anthropic import AsyncAnthropic, APIError

async def call_claude_with_retry(
    client: AsyncAnthropic,
    max_retries: int = 3,
    **kwargs
) -> dict:
    """Call Claude API with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            response = await client.messages.create(**kwargs)
            return response
        except APIError as e:
            if e.status_code == 429:  # Rate limit
                # Use retry-after header if available
                retry_after = e.response.headers.get('retry-after', 1)
                wait_time = float(retry_after)
            elif e.status_code == 529:  # Server overloaded
                # Exponential backoff with jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
            else:
                raise  # Don't retry other errors

            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)
            else:
                raise  # Final attempt failed
```

### Anti-Patterns to Avoid

- **Synchronous API calls in FastAPI**: Use AsyncAnthropic and AsyncTavilyClient, not sync clients
- **No prompt caching**: System prompts repeat on every request; cache them for 90% cost reduction
- **Sequential searches**: Research both options in parallel with asyncio.gather(), not sequentially
- **Polling without timeout**: Add max poll duration to prevent infinite loops
- **Unvalidated JSON parsing**: Use Claude's structured outputs instead of manual JSON.parse with try/catch

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON schema validation | Custom validators | Claude structured outputs + Pydantic | Guarantees schema compliance via constrained decoding, no retry logic needed |
| Retry logic for rate limits | Manual retry loops | Exponential backoff with retry-after header | Claude API returns retry-after header; manual logic misses server guidance |
| SSE connection management | Raw EventSource handling | sse-starlette library | Handles reconnection, error recovery, event formatting automatically |
| Prompt template management | Custom string builders | F-strings with Pydantic models | Pydantic models enforce structure, f-strings are native and readable |
| Token counting | Manual calculation | Anthropic SDK token counting API | Accurate tokenization without loading model locally |
| Cache invalidation logic | Custom TTL tracking | Claude's ephemeral cache (5min TTL) | Automatic cache refresh on each use, no manual tracking |

**Key insight:** Claude's structured outputs eliminate an entire class of problems (malformed JSON, missing fields, retry logic) that were previously unavoidable with LLM APIs. This is a major shift from 2024 where manual validation was necessary.

## Common Pitfalls

### Pitfall 1: Forgetting to Cache System Prompts

**What goes wrong:** System prompts repeat on every comparison, costing full input token price each time
**Why it happens:** Caching requires explicit cache_control markers; defaults to no caching
**How to avoid:**
- Mark final system message block with `cache_control: {"type": "ephemeral"}`
- Cache saves 90% on repeated system prompts after first request
- Monitor cache_read_input_tokens in response.usage to verify caching works
**Warning signs:** High input token costs despite similar comparisons, cache_read_input_tokens always 0

### Pitfall 2: Sequential API Calls Instead of Parallel

**What goes wrong:** Researching option A, then option B doubles the total latency (20s instead of 10s)
**Why it happens:** Natural to write sequential code; requires explicit asyncio.gather()
**How to avoid:**
- Use `asyncio.gather(task_a, task_b)` for independent operations
- Both Tavily searches can run simultaneously
- Claude criteria generation depends on search results, so must wait
**Warning signs:** Total processing time = sum of individual call times instead of max(call times)

### Pitfall 3: Not Handling API Failures Gracefully

**What goes wrong:** Single API failure (rate limit, timeout) crashes entire comparison
**Why it happens:** APIs are unreliable; default behavior is to raise exceptions
**How to avoid:**
- Wrap API calls in try/except with exponential backoff retry
- Use `return_exceptions=True` in asyncio.gather() to handle partial failures
- Return partial results with error indicators rather than failing completely
**Warning signs:** 500 errors for comparisons, no graceful degradation

### Pitfall 4: Insufficiently Specific Prompts

**What goes wrong:** Claude generates obvious criteria (price, durability) instead of hidden costs
**Why it happens:** Generic prompts get generic results; need explicit guidance
**How to avoid:**
- Explicitly request "non-obvious" and "hidden costs" in system prompt
- Provide examples of desired criteria (embedded energy, subsidies, externalities)
- Use negative examples: "NOT price, durability, or convenience"
**Warning signs:** User feedback that criteria are "too obvious", low engagement with results

### Pitfall 5: Tavily Query Too Broad or Too Narrow

**What goes wrong:** Search returns irrelevant results or no results
**Why it happens:** Query design is critical; generic queries get generic results
**How to avoid:**
- Keep queries under 400 characters
- Include specific aspects: "{option} hidden costs environmental impact subsidies"
- Use search_depth="basic" for POC (balanced speed/quality)
- Set max_results=10 for focused, relevant sources
**Warning signs:** Search results unrelated to comparison, missing critical information

### Pitfall 6: Frontend Loses SSE Connection

**What goes wrong:** Progress updates stop mid-stream, user sees stale status
**Why it happens:** Network issues, server restarts, client tab backgrounding
**How to avoid:**
- Implement EventSource error handler that reconnects
- Fall back to polling if SSE fails after N retries
- Store last known status in case of connection loss
**Warning signs:** Users report "stuck" loading states, progress never completes

## Code Examples

Verified patterns from official sources:

### Complete Orchestration Flow

```python
# Source: Synthesized from official docs
from anthropic import AsyncAnthropic
from tavily import AsyncTavilyClient
from pydantic import BaseModel
import asyncio

class Criterion(BaseModel):
    id: str
    name: str
    description: str
    score_a: float
    score_b: float
    weight: float
    sources: list[str]

class ComparisonResult(BaseModel):
    criteria: list[Criterion]
    winner: str
    reasoning: str

async def generate_comparison(
    option_a: str,
    option_b: str,
    intent: str,
    comparison_id: str
) -> ComparisonResult:
    """Full orchestration: search + analyze + generate criteria."""

    # Initialize clients
    claude = AsyncAnthropic()
    tavily = AsyncTavilyClient()

    # Step 1: Search both options in parallel
    search_a, search_b = await asyncio.gather(
        tavily.search(
            query=f"{option_a} hidden costs environmental impact subsidies",
            search_depth="basic",
            max_results=10
        ),
        tavily.search(
            query=f"{option_b} hidden costs environmental impact subsidies",
            search_depth="basic",
            max_results=10
        ),
        return_exceptions=True
    )

    # Step 2: Extract sources and content
    sources_a = [r['url'] for r in search_a.get('results', [])]
    content_a = "\n\n".join([
        f"{r['title']}: {r['content']}"
        for r in search_a.get('results', [])
    ])

    sources_b = [r['url'] for r in search_b.get('results', [])]
    content_b = "\n\n".join([
        f"{r['title']}: {r['content']}"
        for r in search_b.get('results', [])
    ])

    # Step 3: Generate criteria with structured output
    prompt = f"""Based on the research below, generate 3-5 non-obvious criteria for comparing {option_a} vs {option_b}.

User intent: {intent}

Focus on hidden costs like:
- Embedded energy and carbon footprint
- Government subsidies and externalities
- Supply chain transparency
- Long-term systemic impacts

DO NOT include obvious factors like price, durability, or convenience.

Research for {option_a}:
{content_a}

Research for {option_b}:
{content_b}

For each criterion:
1. Score both options 0-100
2. Generate weight (0-100) based on user intent: "{intent}"
3. Include at least one source URL from research
"""

    response = await claude.messages.parse(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": "You are an expert at discovering non-obvious decision criteria.",
            },
            {
                "type": "text",
                "text": "Always ground claims in provided sources. Never hallucinate.",
                "cache_control": {"type": "ephemeral"}
            }
        ],
        messages=[{"role": "user", "content": prompt}],
        output_format=ComparisonResult
    )

    return response.parsed_output
```

### SSE Progress Streaming

```python
# Source: https://mahdijafaridev.medium.com/implementing-server-sent-events-sse-with-fastapi-real-time-updates-made-simple-6492f8bfc154
from sse_starlette.sse import EventSourceResponse
import json

async def generate_with_progress(
    option_a: str,
    option_b: str,
    intent: str,
    comparison_id: str
):
    """Generate comparison with progress streaming."""

    async def event_generator():
        try:
            yield {
                "event": "progress",
                "data": json.dumps({"status": f"Searching web for {option_a}..."})
            }

            # Perform actual work...
            result = await generate_comparison(option_a, option_b, intent, comparison_id)

            yield {
                "event": "progress",
                "data": json.dumps({"status": "Generating criteria..."})
            }

            yield {
                "event": "complete",
                "data": json.dumps({
                    "comparison_id": comparison_id,
                    "status": "completed"
                })
            }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }

    return EventSourceResponse(event_generator())
```

### Frontend SSE Consumer (React)

```typescript
// Source: https://oneuptime.com/blog/post/2026-01-15-server-sent-events-sse-react/view
import { useEffect, useState } from 'react';

function useComparisonProgress(comparisonId: string) {
  const [status, setStatus] = useState<string>('Initializing...');
  const [error, setError] = useState<string | null>(null);
  const [complete, setComplete] = useState(false);

  useEffect(() => {
    if (!comparisonId) return;

    const eventSource = new EventSource(`/api/progress/${comparisonId}`);

    eventSource.addEventListener('progress', (event) => {
      const data = JSON.parse(event.data);
      setStatus(data.status);
    });

    eventSource.addEventListener('complete', (event) => {
      setComplete(true);
      eventSource.close();
    });

    eventSource.addEventListener('error', (event) => {
      const data = JSON.parse(event.data);
      setError(data.error);
      eventSource.close();
    });

    eventSource.onerror = () => {
      // Connection failed - fall back to polling
      setStatus('Connection lost, switching to polling...');
      eventSource.close();
      // Trigger polling fallback (not shown)
    };

    return () => {
      eventSource.close();
    };
  }, [comparisonId]);

  return { status, error, complete };
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual JSON validation with retries | Structured outputs (constrained decoding) | Nov 2025 | Eliminates entire class of parsing errors |
| Full input tokens on every request | Prompt caching (5min/1hr TTL) | Aug 2024 | 90% cost reduction on repeated context |
| Single search query per comparison | Parallel async searches | Established | 50% latency reduction |
| WebSocket for streaming | Server-Sent Events (SSE) | Established | Simpler implementation, native browser support |
| Manual schema transformation | Pydantic model -> Claude schema | Oct 2024 | SDK handles transformation automatically |

**Deprecated/outdated:**
- **LangChain for simple API calls**: Adds unnecessary abstraction; direct SDK usage is cleaner (Phase 1 research confirmed)
- **Instructor library**: Claude SDK now has native structured outputs; Instructor adds redundant layer
- **Manual retry logic**: Use retry-after header + exponential backoff; don't hard-code delays

## Open Questions

Things that couldn't be fully resolved:

1. **Optimal number of Tavily results**
   - What we know: Tavily docs recommend max_results=10 for quality
   - What's unclear: Whether 10 results provide enough source diversity for non-obvious criteria
   - Recommendation: Start with 10, instrument to measure source citation usage, adjust based on data

2. **SSE vs polling trade-offs**
   - What we know: SSE is simpler for unidirectional streaming, polling works everywhere
   - What's unclear: How reliably SSE works across corporate proxies, mobile networks
   - Recommendation: Implement SSE with polling fallback; measure SSE success rate in production

3. **Prompt caching effectiveness for variable contexts**
   - What we know: System prompts and tools cache well (static content)
   - What's unclear: Whether caching is worthwhile when context varies (different searches per comparison)
   - Recommendation: Cache system prompts and tool definitions only; don't cache search results

4. **Claude model selection (Sonnet vs Haiku)**
   - What we know: Sonnet 4.5 has better reasoning; Haiku 4.5 is 5x cheaper and faster
   - What's unclear: Whether Haiku can generate quality non-obvious criteria
   - Recommendation: Start with Sonnet for quality; A/B test Haiku once criteria patterns are established

## Sources

### Primary (HIGH confidence)

- [Structured outputs - Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) - JSON mode, strict tool use, Pydantic integration
- [Prompt caching - Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) - Cost savings, implementation, best practices
- [Best Practices for Search - Tavily Docs](https://docs.tavily.com/documentation/best-practices/best-practices-search) - Query design, parallel execution, parameter optimization
- [Anthropic SDK Python GitHub](https://github.com/anthropics/anthropic-sdk-python) - Official SDK examples, async streaming patterns
- [FastAPI Background Tasks - Official Docs](https://fastapi.tiangolo.com/tutorial/background-tasks/) - Built-in async task execution

### Secondary (MEDIUM confidence)

- [Claude API Structured Output: Complete Guide](https://thomas-wiegold.com/blog/claude-api-structured-output/) - Practical implementation patterns
- [Prompt Caching: 10x cheaper LLM tokens](https://ngrok.com/blog/prompt-caching/) - Cost analysis and optimization strategies
- [Implementing Server-Sent Events (SSE) with FastAPI](https://mahdijafaridev.medium.com/implementing-server-sent-events-sse-with-fastapi-real-time-updates-made-simple-6492f8bfc154) - SSE implementation patterns
- [How to Implement Server-Sent Events in React](https://oneuptime.com/blog/post/2026-01-15-server-sent-events-sse-react/view) - Frontend SSE consumption
- [FastAPI and Background Tasks](https://unfoldai.com/fastapi-background-tasks/) - Async processing best practices
- [Claude API Rate Limits: Production Scaling Guide](https://www.hashbuilds.com/articles/claude-api-rate-limits-production-scaling-guide-for-saas) - Error handling and retry strategies
- [API Error Handling & Retry Strategies](https://easyparser.com/blog/api-error-handling-retry-strategies-python-guide) - Exponential backoff patterns

### Tertiary (LOW confidence)

- [The 2026 Guide to Prompt Engineering](https://www.ibm.com/think/prompt-engineering) - General prompt engineering trends
- [Future of Prompt Engineering 2026](https://www.refontelearning.com/blog/future-of-prompt-engineering-trends-tools-and-job-opportunities-for-2026-and-beyond) - Industry trends and meta-prompting
- [AI in 2026: Five Defining Themes](https://news.sap.com/2026/01/ai-in-2026-five-defining-themes/) - Intent-based AI trends

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official SDKs with active maintenance, verified 2026 compatibility
- Architecture: HIGH - Patterns verified in official documentation and production use
- Pitfalls: HIGH - Sourced from official docs and known production issues
- Prompt engineering: MEDIUM - General trends applied to specific use case; requires validation
- SSE reliability: MEDIUM - Standard pattern but network variability unknown without production data

**Research date:** 2026-02-07
**Valid until:** 2026-03-07 (30 days - stable APIs with active maintenance)
