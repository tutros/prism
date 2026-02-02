# Architecture Research

## System Overview

This document outlines the architecture for an AI-powered comparison web application that helps users make decisions by surfacing hidden costs and non-obvious criteria. The system follows a modern **React + FastAPI** pattern with clear separation of concerns, async-first design, and file-based persistence for POC simplicity.

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         React Frontend                          │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐  │
│  │ Comparison   │  │ Weight       │  │ Results Display     │  │
│  │ Form         │  │ Adjustment   │  │ (with sources)      │  │
│  └──────────────┘  └──────────────┘  └─────────────────────┘  │
│         │                  │                      ▲             │
│         │                  │                      │             │
│         └──────────────────┴──────────────────────┘             │
│                            │                                    │
│                    Async API Client                             │
└────────────────────────────┼───────────────────────────────────┘
                             │
                    HTTP/JSON (SSE for streaming)
                             │
┌────────────────────────────┼───────────────────────────────────┐
│                   FastAPI Backend                               │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐  │
│  │ API Routes   │  │ Service      │  │ Orchestration       │  │
│  │ Layer        │  │ Layer        │  │ Layer               │  │
│  └──────────────┘  └──────────────┘  └─────────────────────┘  │
│         │                  │                      │             │
│         └──────────────────┴──────────────────────┘             │
│                            │                                    │
└────────────────────────────┼───────────────────────────────────┘
                             │
                   ┌─────────┴─────────┐
                   ▼                   ▼
          ┌─────────────────┐  ┌──────────────┐
          │  AI Services    │  │ File Storage │
          │  - Claude API   │  │  (JSON)      │
          │  - Tavily API   │  └──────────────┘
          └─────────────────┘
```

## Components

### 1. React Frontend

**Responsibilities:**
- User input collection (options, intent)
- Display comparison results with sources
- Interactive weight adjustment
- Trigger recalculation and regeneration
- Loading states and error handling

**Key Technologies:**
- React 18+ with hooks
- State management: React Query or Zustand for async state
- HTTP client: Axios or fetch with async/await
- UI: Tailwind CSS or similar for rapid prototyping

**State Structure:**
```javascript
{
  comparison: {
    optionA: string,
    optionB: string,
    intent: string
  },
  results: {
    criteria: Array<Criterion>,
    weights: Map<string, number>,
    scores: { optionA: number, optionB: number },
    winner: string,
    flipAnalysis: Object,
    sources: Array<Source>,
    status: 'idle' | 'loading' | 'success' | 'error'
  }
}
```

### 2. FastAPI Backend

**Responsibilities:**
- Request validation and routing
- AI orchestration (Claude + Tavily coordination)
- Business logic (scoring, flip analysis)
- File persistence
- Error handling and retry logic

**Project Structure** (following [FastAPI best practices](https://github.com/zhanymkanov/fastapi-best-practices)):
```
backend/
├── app/
│   ├── main.py                 # FastAPI app setup
│   ├── api/
│   │   ├── routes/
│   │   │   ├── comparisons.py  # Comparison endpoints
│   │   │   └── health.py       # Health check
│   │   └── dependencies.py     # Shared dependencies
│   ├── services/
│   │   ├── ai_service.py       # AI orchestration
│   │   ├── claude_service.py   # Claude API wrapper
│   │   ├── tavily_service.py   # Tavily API wrapper
│   │   └── scoring_service.py  # Calculation logic
│   ├── models/
│   │   ├── domain.py           # Business models
│   │   └── schemas.py          # Pydantic schemas (DTOs)
│   └── storage/
│       └── file_repository.py  # JSON persistence
├── data/                       # File storage directory
└── tests/
```

### 3. AI Services Layer

**Claude API (Anthropic)**
- **Purpose:** Reasoning, criteria generation, weighting
- **Pattern:** Structured prompts with JSON response format
- **Calls:**
  1. Generate criteria from research results
  2. Assign weights based on user intent
  3. Explain flip scenarios

**Tavily API (Web Search)**
- **Purpose:** Research both options, gather factual data
- **Pattern:** Parallel searches for both options
- **Returns:** Search results with sources/citations

### 4. File-Based Storage

**Pattern:** [Repository Pattern with JSON files](https://codesignal.com/learn/courses/refactoring-for-production-readiness/lessons/file-persistence-with-json)

**Structure:**
```
data/
├── comparisons/
│   ├── {uuid}.json          # Individual comparison results
│   └── index.json           # List of all comparisons
```

**File Format:**
```json
{
  "id": "uuid",
  "timestamp": "ISO-8601",
  "input": {
    "optionA": "...",
    "optionB": "...",
    "intent": "..."
  },
  "research": {
    "optionA": { "sources": [...] },
    "optionB": { "sources": [...] }
  },
  "criteria": [...],
  "weights": {...},
  "results": {...}
}
```

## Data Flow

### Primary Flow: New Comparison

```
1. User Input → Frontend
   ↓
2. POST /api/comparisons { optionA, optionB, intent }
   ↓
3. Backend: Orchestration Service
   ↓
4. Parallel Research Phase (async)
   ├─→ Tavily: Search optionA → Results A
   └─→ Tavily: Search optionB → Results B
   ↓
5. AI Analysis Phase
   ├─→ Claude: Generate criteria from (Results A + Results B)
   └─→ Claude: Weight criteria based on intent
   ↓
6. Scoring Service
   ├─→ Calculate scores
   ├─→ Determine winner
   └─→ Compute flip scenarios
   ↓
7. File Repository: Save comparison
   ↓
8. Response → Frontend (JSON with results + sources)
```

### Secondary Flow: Weight Adjustment

```
1. User adjusts weight → Frontend
   ↓
2. Local recalculation (client-side for instant feedback)
   ↓
3. PATCH /api/comparisons/{id}/weights { weights: {...} }
   ↓
4. Backend: Scoring Service
   ├─→ Recalculate scores
   ├─→ Determine new winner
   └─→ Recompute flip scenarios
   ↓
5. File Repository: Update comparison
   ↓
6. Response → Frontend (updated results)
```

### Tertiary Flow: Regeneration

```
1. User clicks "Regenerate" → Frontend
   ↓
2. POST /api/comparisons/{id}/regenerate
   ↓
3. Backend: Reuse existing research, re-run AI analysis
   ↓
4. Claude: Generate new criteria + weights
   ↓
5. Follow steps 6-8 from Primary Flow
```

## API Design

### Endpoints

Following [RESTful best practices](https://medium.com/algomart/modern-fastapi-architecture-patterns-for-scalable-production-systems-41a87b165a8b) and [FastAPI patterns](https://dev.to/mayowaadeoni/building-scalable-ai-apps-with-react-fastapi-2gg0):

#### 1. Create Comparison
```http
POST /api/v1/comparisons
Content-Type: application/json

{
  "optionA": "iPhone 16 Pro",
  "optionB": "Samsung Galaxy S25",
  "intent": "photography and battery life"
}

Response 202 Accepted:
{
  "id": "uuid",
  "status": "processing",
  "estimatedTime": 30
}
```

#### 2. Get Comparison Status/Results
```http
GET /api/v1/comparisons/{id}

Response 200 OK:
{
  "id": "uuid",
  "status": "complete",
  "input": {...},
  "criteria": [
    {
      "name": "Low-light photography performance",
      "description": "...",
      "weight": 0.25,
      "scores": { "optionA": 8.5, "optionB": 7.2 }
    }
  ],
  "results": {
    "winner": "optionA",
    "scores": { "optionA": 8.1, "optionB": 7.5 },
    "flipAnalysis": {
      "minWeightChange": {...}
    }
  },
  "sources": [...]
}
```

#### 3. Update Weights
```http
PATCH /api/v1/comparisons/{id}/weights
Content-Type: application/json

{
  "weights": {
    "Low-light photography performance": 0.4,
    "Battery degradation over 2 years": 0.3,
    ...
  }
}

Response 200 OK:
{
  "results": { ... },  // Updated results
  "flipAnalysis": { ... }
}
```

#### 4. Regenerate Criteria
```http
POST /api/v1/comparisons/{id}/regenerate

Response 202 Accepted:
{
  "id": "uuid",
  "status": "processing"
}
```

#### 5. Health Check
```http
GET /api/v1/health

Response 200 OK:
{
  "status": "healthy",
  "services": {
    "claude": "operational",
    "tavily": "operational"
  }
}
```

### Request/Response Patterns

**Long-Running Operations:**
- Use **202 Accepted** for async operations
- Return operation ID and status endpoint
- Client polls status endpoint or uses SSE for updates

**Error Handling:**
```json
{
  "error": {
    "code": "AI_SERVICE_ERROR",
    "message": "Claude API rate limit exceeded",
    "details": {...},
    "retryAfter": 60
  }
}
```

## Async Patterns

### Challenge: AI Calls Are Slow
- Tavily searches: 2-5 seconds each
- Claude API calls: 5-15 seconds each
- Total processing: 20-40 seconds per comparison

### Solution: Multi-Layer Async Architecture

#### Backend: FastAPI Async Routes

Following [FastAPI async best practices](https://www.zestminds.com/blog/fastapi-deployment-guide/) and [modern patterns](https://medium.com/algomart/modern-fastapi-architecture-patterns-for-scalable-production-systems-41a87b165a8b):

```python
from fastapi import BackgroundTasks
import asyncio

@app.post("/api/v1/comparisons", status_code=202)
async def create_comparison(
    request: ComparisonRequest,
    background_tasks: BackgroundTasks
):
    comparison_id = str(uuid.uuid4())

    # Save initial state
    await repository.create(comparison_id, request)

    # Run heavy work in background
    background_tasks.add_task(
        process_comparison,
        comparison_id,
        request
    )

    return {
        "id": comparison_id,
        "status": "processing"
    }

async def process_comparison(comparison_id: str, request: ComparisonRequest):
    try:
        # Parallel research
        results = await asyncio.gather(
            tavily_service.search(request.optionA),
            tavily_service.search(request.optionB)
        )

        # Sequential AI analysis
        criteria = await claude_service.generate_criteria(results)
        weights = await claude_service.assign_weights(criteria, request.intent)

        # Calculate and save
        scores = scoring_service.calculate(criteria, weights)
        await repository.update(comparison_id, {
            "status": "complete",
            "criteria": criteria,
            "results": scores
        })

    except Exception as e:
        await repository.update(comparison_id, {
            "status": "failed",
            "error": str(e)
        })
```

#### Frontend: Polling Pattern

Using [React Query](https://frontendmastery.com/posts/the-new-wave-of-react-state-management/) for async state management:

```javascript
// Create comparison
const createComparison = useMutation({
  mutationFn: async (data) => {
    const response = await axios.post('/api/v1/comparisons', data);
    return response.data;
  }
});

// Poll for results
const { data: results } = useQuery({
  queryKey: ['comparison', comparisonId],
  queryFn: async () => {
    const response = await axios.get(`/api/v1/comparisons/${comparisonId}`);
    return response.data;
  },
  enabled: !!comparisonId,
  refetchInterval: (data) => {
    // Stop polling when complete
    return data?.status === 'complete' ? false : 2000;
  }
});
```

#### Alternative: Server-Sent Events (SSE)

For [real-time updates](https://developers.googleblog.com/en/beyond-request-response-architecting-real-time-bidirectional-streaming-multi-agent-system/):

```python
from fastapi.responses import StreamingResponse

@app.get("/api/v1/comparisons/{id}/stream")
async def stream_comparison(id: str):
    async def event_stream():
        while True:
            comparison = await repository.get(id)
            yield f"data: {json.dumps(comparison)}\n\n"

            if comparison['status'] in ['complete', 'failed']:
                break

            await asyncio.sleep(1)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream"
    )
```

### Optimizations

1. **Parallel Execution:** Use `asyncio.gather()` for independent AI calls
2. **Caching:** Cache Tavily results to avoid redundant searches
3. **Retry Logic:** Exponential backoff for API failures
4. **Rate Limiting:** Client-side debouncing for weight adjustments

## Suggested Build Order

### Phase 1: Foundation (Days 1-2)
**Goal:** Basic request/response flow working

1. **Backend Setup**
   - FastAPI project structure
   - Basic routing (`/health`, `/comparisons`)
   - Pydantic schemas for request/response
   - File repository with JSON storage

2. **Frontend Setup**
   - React app with Vite
   - Basic form for comparison input
   - API client setup (axios)
   - Results display component

3. **Integration Test**
   - Submit hardcoded comparison
   - Return mock results
   - Verify full stack communication

**Why this order:** Establishes the communication pipeline before adding complexity. File storage is simplest ([Repository Pattern](https://codesignal.com/learn/courses/refactoring-for-production-readiness/lessons/file-persistence-with-json)).

---

### Phase 2: AI Integration (Days 3-4)
**Goal:** Real AI calls generating actual criteria

1. **Backend AI Services**
   - Tavily service: Web search wrapper
   - Claude service: Structured prompts
   - Orchestration service: Coordinate AI calls
   - Add error handling and retries

2. **Sequential Flow First**
   - Research → Criteria → Weights (one at a time)
   - Log each step for debugging
   - Basic scoring calculation

3. **Frontend Loading States**
   - Show "Researching..." spinner
   - Display progress updates
   - Error messages

**Why this order:** Get AI working sequentially before optimizing for async. Easier to debug.

---

### Phase 3: Async & Performance (Days 5-6)
**Goal:** Handle long-running operations gracefully

1. **Backend Async Pattern**
   - Convert to [BackgroundTasks](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
   - Add status tracking
   - Parallel Tavily calls (`asyncio.gather`)

2. **Frontend Polling**
   - Implement React Query
   - Poll for status updates
   - Show intermediate results as they arrive

3. **Testing**
   - Simulate slow AI responses
   - Handle timeouts and failures
   - Verify no blocking operations

**Why this order:** Async adds complexity; build it on working foundation. [Async patterns are essential](https://blog.pixelfreestudio.com/best-practices-for-handling-async-state-in-frontend-apps/) for good UX.

---

### Phase 4: Interactivity (Days 7-8)
**Goal:** User can adjust weights and see updated results

1. **Client-Side Recalculation**
   - Weight adjustment UI (sliders)
   - Local score recalculation (instant feedback)
   - Optimistic updates

2. **Backend Weight Update Endpoint**
   - PATCH endpoint for weights
   - Persist to file
   - Return updated results

3. **Flip Analysis**
   - Calculate minimum weight changes
   - Display in UI
   - Highlight sensitive criteria

**Why this order:** Interactive features require working async system. [Memoization](https://blog.pixelfreestudio.com/how-to-handle-complex-state-in-large-scale-frontend-projects/) ensures efficient recalculation.

---

### Phase 5: Polish & Sources (Days 9-10)
**Goal:** Production-ready POC

1. **Source Citations**
   - Display Tavily sources
   - Link to original articles
   - Show which sources informed each criterion

2. **Regeneration**
   - "Generate new criteria" button
   - Reuse research, new AI analysis
   - Compare multiple criterion sets

3. **UX Improvements**
   - Better loading states
   - Error recovery
   - Input validation

4. **Testing & Documentation**
   - E2E tests for critical paths
   - API documentation
   - Deployment guide

**Why this order:** Polish comes last. Core functionality must work first.

---

## Technology Stack Summary

### Frontend
- **Framework:** React 18+
- **State Management:** React Query (async) + Zustand (local)
- **HTTP Client:** Axios
- **UI Library:** Tailwind CSS
- **Build Tool:** Vite

### Backend
- **Framework:** FastAPI
- **Async Runtime:** Uvicorn + asyncio
- **Validation:** Pydantic v2
- **Testing:** pytest + httpx

### AI Services
- **LLM:** Claude API (Anthropic)
- **Search:** Tavily API

### Storage
- **POC:** JSON files (file system)
- **Future:** PostgreSQL or SQLite

### Deployment
- **Backend:** Gunicorn + Uvicorn workers
- **Frontend:** Static hosting (Vercel/Netlify)
- **POC:** Docker Compose for local dev

---

## Key Architectural Decisions

### 1. **Separation of Concerns**
Frontend owns presentation, backend owns orchestration. Clear API boundary. ([Best practice](https://github.com/zhanymkanov/fastapi-best-practices))

### 2. **Async-First Design**
AI calls are slow; use [background tasks and polling](https://www.zestminds.com/blog/build-ai-workflows-fastapi-langgraph/) to avoid blocking.

### 3. **File-Based Storage for POC**
JSON files are [simple for POC](https://codesignal.com/learn/courses/refactoring-for-production-readiness/lessons/file-persistence-with-json), easy migration path to database later.

### 4. **Client-Side Recalculation**
Weight changes trigger instant local updates, then sync to backend. Better UX.

### 5. **Structured AI Outputs**
Use [JSON mode](https://www.lindy.ai/blog/ai-agent-architecture) for predictable Claude responses. Easier parsing and error handling.

### 6. **Repository Pattern**
Abstract storage layer for easy swapping ([FastAPI pattern](https://dev.to/mohammad222pr/structuring-a-fastapi-project-best-practices-53l6)).

---

## References & Further Reading

### Architecture & Patterns
- [Building Smart Web AI Agents with MCP, LangGraph & FastAPI](https://sgino209.medium.com/building-smart-web-ai-agents-with-mcp-langgraph-fastapi-da2734fe5256)
- [Modern FastAPI Architecture Patterns for Scalable Production Systems](https://medium.com/algomart/modern-fastapi-architecture-patterns-for-scalable-production-systems-41a87b165a8b)
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [A Complete Guide to AI Agent Architecture in 2026](https://www.lindy.ai/blog/ai-agent-architecture)

### Async & Real-Time
- [Beyond Request-Response: Architecting Real-time Bidirectional Streaming Multi-agent System](https://developers.googleblog.com/en/beyond-request-response-architecting-real-time-bidirectional-streaming-multi-agent-system/)
- [Best Practices for Handling Async State in Frontend Apps](https://blog.pixelfreestudio.com/best-practices-for-handling-async-state-in-frontend-apps/)
- [The New Wave of React State Management](https://frontendmastery.com/posts/the-new-wave-of-react-state-management/)

### Storage & Persistence
- [File Persistence with JSON](https://codesignal.com/learn/courses/refactoring-for-production-readiness/lessons/file-persistence-with-json)
- [A Brief Analysis of JSON File-Backed Storage](https://mozilla.github.io/firefox-browser-architecture/text/0012-jsonfile.html)

### AI Orchestration
- [Build AI Workflows with FastAPI & LangGraph](https://www.zestminds.com/blog/build-ai-workflows-fastapi-langgraph/)
- [Building Effective AI Agents](https://www.anthropic.com/research/building-effective-agents)
- [LLM Orchestration in 2026: Top 12 Frameworks](https://research.aimultiple.com/llm-orchestration/)

### Integration
- [Building Scalable AI Apps with React & FastAPI](https://dev.to/mayowaadeoni/building-scalable-ai-apps-with-react-fastapi-2gg0)
- [Structuring a FastAPI Project: Best Practices](https://dev.to/mohammad222pr/structuring-a-fastapi-project-best-practices-53l6)
