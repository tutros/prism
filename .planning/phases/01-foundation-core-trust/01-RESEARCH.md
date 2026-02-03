# Phase 1: Foundation + Core Trust - Research

**Researched:** 2026-02-02
**Domain:** Full-stack comparison UI with React + FastAPI
**Confidence:** HIGH

## Summary

Phase 1 establishes the foundation for a source-cited option comparison tool using React 18 + Vite 6 + TanStack Query v5 on the frontend and FastAPI 0.128+ + Pydantic v2 on the backend. The core pattern is a **submit-poll-display** workflow where users submit two options for comparison, the backend processes (initially with mock data), and the frontend polls for results. Weight sliders enable client-side score recalculation without server round-trips.

The research confirms this stack is current and well-supported as of 2026. Key findings:
- TanStack Query v5 provides robust patterns for mutations (submit), optimistic updates (sliders), and query invalidation
- FastAPI + Pydantic v2 offers type-safe JSON serialization with atomic file writes using pathlib
- Tailwind CSS v4's mobile-first breakpoint system aligns with responsive requirements
- React controlled components with useState handle real-time slider updates efficiently

**Primary recommendation:** Use FastAPI BackgroundTasks for mock processing with 202 Accepted + polling pattern; implement atomic JSON writes with temp file + os.replace(); structure frontend as feature-based modules (comparison/, results/, weights/); use controlled range inputs with local state for instant slider feedback.

## Standard Stack

The established libraries/tools for this domain:

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 18.x | UI rendering with hooks | Industry standard, excellent TypeScript support, mature ecosystem |
| Vite | 6.x | Build tool and dev server | Fastest dev server (sub-second starts), ES modules native, official Vite+React template |
| TanStack Query | v5.84.1 | Server state management | De facto standard for async state (replaces Redux for server data), great DevTools |
| FastAPI | 0.128+ | Python API framework | Modern, high-performance, auto-generates OpenAPI docs, async support |
| Pydantic | v2.x | Data validation | Rust-powered validation (60% faster), tight FastAPI integration, JSON schema generation |
| Tailwind CSS | v4.x | Utility-first styling | Mobile-first breakpoints, CSS-variable theming (@theme), minimal runtime overhead |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pathlib | Python 3.11+ stdlib | File system operations | Standard library, type-safe paths, cross-platform |
| atomicwrites | 1.4.0 (optional) | Atomic file operations | Production atomic writes (stdlib os.replace() sufficient for same-filesystem writes) |
| React Hook Form | 7.x (future) | Form validation | When adding complex validation in Phase 2+ |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| TanStack Query | SWR, RTK Query | SWR lacks mutation helpers; RTK Query requires Redux ecosystem |
| Tailwind CSS | styled-components, CSS Modules | Component-scoped styles vs utility-first; Tailwind faster for prototyping |
| FastAPI | Flask, Django | FastAPI has better async, auto-docs, and type hints; Flask more minimal |

**Installation:**
```bash
# Frontend
npm create vite@latest frontend -- --template react
cd frontend
npm install @tanstack/react-query
npm install -D tailwindcss@next postcss autoprefixer
npx tailwindcss init -p

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install "fastapi[standard]>=0.128.0" "pydantic>=2.0" uvicorn
```

## Architecture Patterns

### Recommended Project Structure

```
orchids-option-analysis-ui/
├── frontend/
│   ├── src/
│   │   ├── features/           # Feature-based organization
│   │   │   ├── comparison/     # Submit form, input handling
│   │   │   ├── results/        # Side-by-side display, winner indication
│   │   │   └── weights/        # Slider controls, score recalculation
│   │   ├── components/         # Reusable UI (Button, Card, Loading)
│   │   ├── hooks/              # Custom hooks (useComparison, useWeights)
│   │   ├── lib/                # Utils (api client, queryClient config)
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── package.json
└── backend/
    ├── app/
    │   ├── main.py              # FastAPI app, CORS, routers
    │   ├── models.py            # Pydantic models
    │   ├── storage.py           # JSON file persistence
    │   └── routers/
    │       ├── comparison.py    # POST /compare, GET /results/{id}
    │       └── health.py        # GET /health
    ├── data/                    # JSON storage directory
    ├── tests/
    └── requirements.txt
```

**Rationale:**
- Frontend uses **feature folders** (comparison, results, weights) not technical folders (pages, containers) - scales better
- Backend uses **routers** pattern from FastAPI docs for modularity
- Separate `storage.py` abstracts file I/O from business logic
- `data/` directory keeps JSON files organized and gitignored

### Pattern 1: Submit-Poll-Display with TanStack Query

**What:** Client submits comparison → backend returns task ID → client polls for results
**When to use:** Any async operation where processing time is unpredictable

**Example:**
```typescript
// Source: TanStack Query v5 docs + FastAPI BackgroundTasks pattern
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

// 1. Submit comparison
const submitComparison = useMutation({
  mutationFn: async (data: ComparisonInput) => {
    const res = await fetch('/api/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('Comparison failed')
    return res.json() // { comparison_id: string }
  },
  onSuccess: (data) => {
    // Start polling for results
    queryClient.invalidateQueries({ queryKey: ['comparison', data.comparison_id] })
  },
})

// 2. Poll for results
const { data: results, isLoading } = useQuery({
  queryKey: ['comparison', comparisonId],
  queryFn: async () => {
    const res = await fetch(`/api/results/${comparisonId}`)
    if (!res.ok) throw new Error('Failed to fetch results')
    return res.json()
  },
  enabled: !!comparisonId, // Only poll if we have an ID
  refetchInterval: (query) => {
    // Stop polling when data arrives or on error
    return query.state.data?.status === 'completed' ? false : 2000
  },
})
```

**Backend (FastAPI):**
```python
# Source: FastAPI BackgroundTasks + polling pattern
from fastapi import BackgroundTasks, HTTPException
from pydantic import BaseModel
import uuid

class ComparisonInput(BaseModel):
    option_a: str
    option_b: str
    intent: str

@router.post("/compare")
async def submit_comparison(
    data: ComparisonInput,
    background_tasks: BackgroundTasks
):
    comparison_id = str(uuid.uuid4())

    # Write initial status
    storage.write_status(comparison_id, {"status": "processing"})

    # Add mock processing to background
    background_tasks.add_task(process_comparison, comparison_id, data)

    return {"comparison_id": comparison_id}, 202  # Accepted

@router.get("/results/{comparison_id}")
async def get_results(comparison_id: str):
    result = storage.read_result(comparison_id)
    if not result:
        raise HTTPException(404, "Comparison not found")
    return result
```

### Pattern 2: Optimistic Weight Updates (Client-Side Only)

**What:** Slider changes immediately update UI scores without server calls
**When to use:** When calculation is fast and doesn't require server (e.g., weighted sum)

**Example:**
```typescript
// Source: React controlled components + local state
import { useState } from 'react'

function WeightSliders({ criteria, onWeightsChange }) {
  const [weights, setWeights] = useState(
    criteria.reduce((acc, c) => ({ ...acc, [c.id]: 50 }), {})
  )

  const handleSliderChange = (criterionId: string, value: number) => {
    const newWeights = { ...weights, [criterionId]: value }
    setWeights(newWeights)

    // Immediately recalculate scores (no API call)
    const newScores = calculateScores(criteria, newWeights)
    onWeightsChange(newScores)
  }

  return (
    <>
      {criteria.map((criterion) => (
        <div key={criterion.id}>
          <label>{criterion.name}</label>
          <input
            type="range"
            min="0"
            max="100"
            value={weights[criterion.id]}
            onChange={(e) => handleSliderChange(criterion.id, parseInt(e.target.value))}
            className="w-full"
          />
          <span>{weights[criterion.id]}%</span>
        </div>
      ))}
    </>
  )
}

function calculateScores(criteria, weights) {
  // Pure client-side calculation
  return {
    option_a: criteria.reduce((sum, c) => sum + c.score_a * (weights[c.id] / 100), 0),
    option_b: criteria.reduce((sum, c) => sum + c.score_b * (weights[c.id] / 100), 0),
  }
}
```

### Pattern 3: Atomic JSON File Writes

**What:** Write to temp file, then atomic rename to prevent corruption
**When to use:** Any file-based persistence where partial writes could corrupt data

**Example:**
```python
# Source: Python atomic writes best practices + pathlib
from pathlib import Path
import json
import os
import tempfile

class JSONStorage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def write_result(self, comparison_id: str, data: dict) -> None:
        """Atomically write JSON to prevent corruption"""
        target_path = self.data_dir / f"{comparison_id}.json"

        # Write to temp file in same directory (required for atomic move)
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=self.data_dir,
            delete=False,
            suffix='.tmp'
        ) as tmp:
            json.dump(data, tmp, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())  # Ensure written to disk
            tmp_path = tmp.name

        # Atomic rename (POSIX guarantees atomicity on same filesystem)
        os.replace(tmp_path, target_path)

    def read_result(self, comparison_id: str) -> dict | None:
        target_path = self.data_dir / f"{comparison_id}.json"
        if not target_path.exists():
            return None
        return json.loads(target_path.read_text())
```

### Pattern 4: Mobile-First Responsive Layout

**What:** Tailwind v4's mobile-first breakpoints with stack→grid progression
**When to use:** Any responsive UI (default pattern)

**Example:**
```tsx
// Source: Tailwind CSS v4 responsive patterns
function ComparisonResults({ optionA, optionB }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Mobile: stacked vertically, Desktop: side-by-side */}
      <div className="border rounded-lg p-4">
        <h2 className="text-lg font-bold">{optionA.name}</h2>
        <p className="text-sm text-gray-600">{optionA.summary}</p>
      </div>

      <div className="border rounded-lg p-4">
        <h2 className="text-lg font-bold">{optionB.name}</h2>
        <p className="text-sm text-gray-600">{optionB.summary}</p>
      </div>
    </div>
  )
}

// Tailwind v4 breakpoints (mobile-first):
// - Base (unprefixed): all screens (mobile first)
// - sm:  ≥40rem (640px)
// - md:  ≥48rem (768px)
// - lg:  ≥64rem (1024px)
// - xl:  ≥80rem (1280px)
```

### Anti-Patterns to Avoid

- **Don't use `sm:` for mobile styles** - Use unprefixed utilities for mobile; `sm:` applies at small breakpoint and up
- **Don't poll indefinitely** - Always have stop conditions (max attempts, timeout, completion status)
- **Don't use `useState` for server data** - Use TanStack Query's `useQuery` for cache management
- **Don't write files without atomic operations** - Direct writes can corrupt on crash/interruption
- **Don't put business logic in components** - Extract to custom hooks or utility functions

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Polling with retry logic | Custom setInterval loop | TanStack Query `refetchInterval` | Handles cleanup, errors, stop conditions, cache invalidation |
| Atomic file writes | `open(file, 'w').write()` | `tempfile.NamedTemporaryFile` + `os.replace()` | Prevents corruption on crashes, race conditions |
| Form state management | Manual `useState` for each field | React Hook Form (Phase 2+) | Validation, error handling, performance optimization |
| API client with types | `fetch()` + manual typing | TanStack Query + generated types | Cache management, deduplication, error handling |
| CORS in development | Custom headers in fetch | FastAPI `CORSMiddleware` | Handles preflight, credentials, origin validation |
| Loading indicators | Custom spinners | Tailwind + SVG icons | Accessible, consistent, theme-aware |

**Key insight:** TanStack Query handles 90% of async complexity (caching, deduplication, retries, background refetching). Don't recreate this with `useState` + `useEffect`.

## Common Pitfalls

### Pitfall 1: Infinite Polling Loop
**What goes wrong:** Query keeps refetching even after results are ready, wasting resources
**Why it happens:** Missing stop condition in `refetchInterval`
**How to avoid:**
```typescript
refetchInterval: (query) => {
  // Stop when completed, errored, or disabled
  const data = query.state.data
  if (!data || data.status === 'completed' || query.state.error) {
    return false  // Stop polling
  }
  return 2000  // Continue every 2s
}
```
**Warning signs:** Network tab shows continuous requests after results load

### Pitfall 2: File Corruption on Server Restart
**What goes wrong:** JSON files contain partial data or invalid JSON
**Why it happens:** Writing directly to file without atomic operation
**How to avoid:** Always use temp file + `os.replace()` pattern (see Pattern 3)
**Warning signs:** `JSONDecodeError` when reading files after crashes

### Pitfall 3: Slider Updates Trigger API Calls
**What goes wrong:** Every slider drag sends request to server, causing lag and server load
**Why it happens:** Confusing server-derived data (comparison results) with client calculations (weighted scores)
**How to avoid:** Keep weight calculations purely client-side; only initial data comes from server
**Warning signs:** Network waterfall shows many requests during slider interaction

### Pitfall 4: CORS Errors in Development
**What goes wrong:** Frontend can't fetch from backend (Vite:5173 → FastAPI:8000)
**Why it happens:** Browsers block cross-origin requests by default
**How to avoid:**
```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
**Warning signs:** Console errors: "CORS policy: No 'Access-Control-Allow-Origin' header"

### Pitfall 5: Mobile Layout Breaks on Narrow Screens
**What goes wrong:** Text overflows, buttons too small, horizontal scrolling
**Why it happens:** Using fixed widths or forgetting mobile-first approach
**How to avoid:**
- Test in Chrome DevTools mobile view (375px width)
- Use `min-w-0` to allow flex items to shrink
- Use relative units (`rem`, `%`) not `px`
- Start with mobile styles, add `md:` for desktop
**Warning signs:** Horizontal scrollbar on mobile, tiny tap targets

### Pitfall 6: Stale Query Cache After Updates
**What goes wrong:** User submits new comparison but sees old cached results
**Why it happens:** Not invalidating queries after mutations
**How to avoid:**
```typescript
const mutation = useMutation({
  mutationFn: submitComparison,
  onSuccess: (data) => {
    // Invalidate old comparison queries
    queryClient.invalidateQueries({ queryKey: ['comparison'] })
  },
})
```
**Warning signs:** UI shows outdated data after form submission

## Code Examples

Verified patterns from official sources:

### CORS Setup for Vite + FastAPI
```python
# Source: FastAPI CORS documentation
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Development: allow Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### TanStack Query Setup
```typescript
// Source: TanStack Query v5 docs
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60,  // 1 minute
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <YourApp />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
```

### Pydantic v2 Response Model
```python
# Source: FastAPI + Pydantic v2 docs
from pydantic import BaseModel, Field
from typing import Literal

class Criterion(BaseModel):
    name: str
    score_a: float = Field(ge=0, le=100)
    score_b: float = Field(ge=0, le=100)
    sources: list[str] = []

class ComparisonResult(BaseModel):
    comparison_id: str
    status: Literal["processing", "completed", "error"]
    option_a_name: str
    option_b_name: str
    criteria: list[Criterion] = []
    winner: Literal["a", "b", "tie"] | None = None

    class Config:
        # Pydantic v2 uses model_config instead of Config class
        json_schema_extra = {
            "example": {
                "comparison_id": "abc123",
                "status": "completed",
                "option_a_name": "React",
                "option_b_name": "Vue",
                "criteria": [
                    {
                        "name": "Performance",
                        "score_a": 85,
                        "score_b": 80,
                        "sources": ["https://example.com/benchmark"]
                    }
                ],
                "winner": "a"
            }
        }
```

### Controlled Range Slider with Live Preview
```tsx
// Source: React docs + Tailwind patterns
import { useState } from 'react'

function WeightSlider({
  label,
  initialValue = 50,
  onChange
}: {
  label: string
  initialValue?: number
  onChange: (value: number) => void
}) {
  const [value, setValue] = useState(initialValue)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = parseInt(e.target.value)
    setValue(newValue)
    onChange(newValue)  // Trigger recalculation
  }

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <label className="font-medium">{label}</label>
        <span className="text-gray-600">{value}%</span>
      </div>
      <input
        type="range"
        min="0"
        max="100"
        step="1"
        value={value}
        onChange={handleChange}
        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
      />
    </div>
  )
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Create React App | Vite | 2023 (CRA sunset early 2025) | 10-30x faster dev server, native ESM |
| Pydantic v1 | Pydantic v2 | 2023 | 60% faster validation (Rust core), better TypeScript integration |
| Redux for server state | TanStack Query | 2020-2022 | Less boilerplate, automatic cache management |
| `parse_raw()` | `model_validate_json()` | Pydantic v2 (2023) | Clearer API, better error messages |
| CSS-in-JS (styled-components) | Tailwind utility-first | 2020-2025 | Zero runtime, better tree-shaking, faster builds |
| `sm:` for mobile | Unprefixed for mobile | Always (mobile-first) | Correct mobile-first thinking |

**Deprecated/outdated:**
- **Create React App**: Officially sunset; use Vite instead
- **Pydantic v1 methods**: `parse_obj()`, `parse_raw()` → use `model_validate()`, `model_validate_json()`
- **TanStack Query v4**: v5 has better TypeScript inference and simpler API
- **FastAPI <0.100**: Older versions lack latest Pydantic v2 features

## Open Questions

Things that couldn't be fully resolved:

1. **Polling Interval Tuning**
   - What we know: 2-3 second intervals are common; too fast wastes resources, too slow feels unresponsive
   - What's unclear: Optimal interval for mock processing (which is instant)
   - Recommendation: Start with 1s interval for Phase 1 (mock data); adjust based on real AI latency in Phase 2

2. **Result Persistence Duration**
   - What we know: JSON files will accumulate in `data/` directory
   - What's unclear: Should we auto-delete old comparisons? How long to keep?
   - Recommendation: Keep all files in Phase 1 for debugging; add cleanup task in Phase 2+

3. **Weight Default Values**
   - What we know: Need sensible defaults for criteria weights
   - What's unclear: Should all criteria start at equal weight (e.g., 50%) or vary by importance?
   - Recommendation: Start with equal weights (50%) for simplicity; let users adjust

4. **Mobile Slider UX**
   - What we know: Touch targets should be ≥44px per iOS guidelines
   - What's unclear: Whether to show numeric input alongside slider on mobile for precision
   - Recommendation: Test with range slider only first; add numeric input if user feedback suggests need

## Sources

### Primary (HIGH confidence)
- **TanStack Query v5.84.1** - [/tanstack/query/v5_84_1](https://github.com/tanstack/query/tree/v5_84_1/docs) - useMutation, refetchInterval, optimistic updates
- **FastAPI Official Docs** - [/websites/fastapi_tiangolo](https://fastapi.tiangolo.com) - Project structure, CORS, BackgroundTasks, error handling
- **React Official Docs** - [/websites/react_dev](https://react.dev) - Controlled components, form handling, useState patterns
- **Tailwind CSS Responsive Design** - [https://tailwindcss.com/docs/responsive-design](https://tailwindcss.com/docs/responsive-design) - Mobile-first breakpoints, utility patterns
- **Pydantic v2 Docs** - [https://docs.pydantic.dev/latest/](https://docs.pydantic.dev/latest/) - model_validate_json, serialization modes

### Secondary (MEDIUM confidence)
- **Vite 6 Project Structure** - [https://vite.dev/guide/](https://vite.dev/guide/) + [Medium: Complete Guide to Vite 2026](https://medium.com/@robinviktorsson/complete-guide-to-setting-up-react-with-typescript-and-vite-2025-468f6556aaf2) - Feature-based organization, entry point patterns
- **FastAPI Polling Pattern** - [https://openillumi.com/en/en-fastapi-long-task-progress-polling/](https://openillumi.com/en/en-fastapi-long-task-progress-polling/) - 202 Accepted + task ID pattern
- **Python Atomic Writes** - [GitHub Gist: Safe atomic file writes](https://gist.github.com/therightstuff/cbdcbef4010c20acc70d2175a91a321f) + [DEV: Crash-safe JSON](https://dev.to/constanta/crash-safe-json-at-scale-atomic-writes-recovery-without-a-db-3aic) - tempfile + os.replace() pattern
- **React Form Best Practices 2026** - [Daily.dev: Form Best Practices](https://daily.dev/blog/form-on-react-best-practices) - Controlled inputs, validation timing
- **Tailwind Best Practices 2025-2026** - [FrontendTools: Tailwind Best Practices](https://www.frontendtools.tech/blog/tailwind-css-best-practices-design-system-patterns) - Design tokens, responsive patterns

### Tertiary (LOW confidence - for awareness)
- **React Range Slider Libraries** - [ReactScript: Best Range Sliders 2026](https://reactscript.com/best-range-slider/) - rc-slider, react-range options (not needed for Phase 1 native HTML)
- **FastAPI Background Tasks vs Celery** - [TestDriven.io: FastAPI + Celery](https://testdriven.io/blog/fastapi-and-celery/) - Future consideration for Phase 2+ if real AI processing is slow

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** - All libraries verified via Context7 and official docs
- Architecture: **HIGH** - Patterns from official documentation and production examples
- Pitfalls: **HIGH** - Based on documented CORS issues, polling patterns, atomic write requirements

**Research date:** 2026-02-02
**Valid until:** 2026-03-02 (30 days - stack is stable, but re-verify Vite/FastAPI minor versions)

**Notes:**
- Phase 1 uses MOCK AI responses - no actual LLM integration yet (Phase 2)
- File persistence is POC-level (JSON files) - not production-grade database
- No authentication/authorization in Phase 1 - anyone can access any comparison by ID
- Source citations are stored as plain URLs - no link validation or metadata extraction
