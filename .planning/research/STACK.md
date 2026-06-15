# Stack Research

## Frontend

### Core Framework
- **React 18.3+** with **Vite 6.x**
  - Rationale: Vite provides lightning-fast HMR and build times. React 18's concurrent features enable better UX for async operations.
  - Confidence: **High** - Industry standard for greenfield React projects in 2025
  - Source: [Complete Guide to Setting Up React with TypeScript and Vite (2026)](https://medium.com/@robinviktorsson/complete-guide-to-setting-up-react-with-typescript-and-vite-2025-468f6556aaf2)

### Styling
- **Tailwind CSS 4.x** with Vite plugin
  - Version: `tailwindcss@latest` + `@tailwindcss/vite`
  - Rationale: Tailwind v4 includes a dedicated Vite plugin, no longer requires PostCSS/Autoprefixer. Simpler setup, better performance.
  - Note: Use `@import "tailwindcss"` in CSS instead of v3's `@tailwind` directives
  - Confidence: **High** - v4 is specifically optimized for Vite
  - Source: [Installation of tailwind 4.0 + vite (react + javascript or typescript)](https://medium.com/@npguapo/installation-of-tailwind-vite-react-javascript-or-typescript-ec1abdfa56b2)

### State Management
- **TanStack Query v5** (React Query) for server state
  - Package: `@tanstack/react-query@^5.0.0`
  - Rationale: Purpose-built for server state. Handles caching, background updates, loading/error states automatically. Perfect for AI API calls.
  - DevTools: Include `@tanstack/react-query-devtools` for development
  - Confidence: **High** - Solves 80% of state management needs for API-heavy apps
  - Source: [TanStack Query: A Powerful Tool for Data Management in React](https://medium.com/@ignatovich.dm/tanstack-query-a-powerful-tool-for-data-management-in-react-0c5ae6ef037c)

- **Zustand 4.x** for client state (optional, start without it)
  - Package: `zustand@^4.0.0`
  - Rationale: Under 1KB, zero boilerplate, fine-grained reactivity. Use only if Context API causes performance issues.
  - When to add: If you need global UI state (theme, modals) and Context API re-renders become problematic
  - Confidence: **Medium** - Start with Context API, graduate to Zustand if needed
  - Source: [React State Management in 2025: Context API vs Zustand](https://dev.to/cristiansifuentes/react-state-management-in-2025-context-api-vs-zustand-385m)

### Form Handling
- **React Hook Form 7.x**
  - Package: `react-hook-form@^7.0.0`
  - Rationale: 8KB bundle (vs Formik's 15KB), zero dependencies, better performance via uncontrolled components. Formik is no longer actively maintained.
  - Confidence: **High** - Clear winner in 2025
  - Source: [React Hook Form vs Formik - 2025 Comparison](https://www.digitalogy.co/blog/react-hook-form-vs-formik/)

### HTTP Client
- **Axios 1.x** (built into TanStack Query patterns)
  - Package: `axios@^1.0.0`
  - Rationale: Simpler API than fetch, automatic JSON transformation, request/response interceptors. Works seamlessly with TanStack Query.
  - Alternative: Native `fetch` is fine for simple cases, but Axios reduces boilerplate
  - Confidence: **Medium** - Either Axios or fetch works; Axios provides better DX

### TypeScript
- **TypeScript 5.x** (optional but recommended)
  - Package: `typescript@^5.0.0`
  - Rationale: Type safety for API responses, better IDE support, catches bugs at compile time
  - Configuration: Enable `strict: true` for maximum safety
  - Confidence: **Medium** - POC can skip, but adds value for production
  - Source: [Best Practices for React.js with Vite and TypeScript](https://medium.com/@taedmonds/best-practices-for-react-js-with-vite-and-typescript-what-i-use-and-why-f4482558ed89)

---

## Backend

### Framework
- **FastAPI 0.128+** with **Python 3.11 or 3.12**
  - Package: `fastapi>=0.128.0`
  - Rationale: Native async support, automatic OpenAPI docs, excellent for AI integration. Python 3.11/3.12 provide significant performance improvements.
  - Confidence: **High** - Perfect fit for async AI workloads
  - Source: [Building FastAPI APIs in 2025: Best Practices & Real-World Guide](https://www.joinmytutor.com/blog/building-fastapi-apis-2025.php)

### ASGI Server
- **Uvicorn 0.32+** with Gunicorn for production
  - Development: `uvicorn main:app --reload`
  - Production: Gunicorn with Uvicorn workers
    - Package: `gunicorn>=21.0.0` + `uvicorn[standard]>=0.32.0`
    - Workers: `(multiprocessing.cpu_count() * 2) + 1`
    - Worker class: `uvicorn.workers.UvicornWorker`
  - Rationale: Uvicorn is built with uvloop and httptools for maximum async performance. Gunicorn provides multi-core utilization and fault isolation.
  - Confidence: **High** - Recommended in FastAPI docs
  - Source: [FastAPI production deployment best practices](https://render.com/articles/fastapi-production-deployment-best-practices)

### Validation
- **Pydantic v2**
  - Package: `pydantic>=2.0.0`
  - Rationale: Core validation for FastAPI. V2 uses Rust (pydantic-core) for 5-50x performance improvement. Automatic OpenAPI schema generation.
  - Best Practices:
    - Keep validators focused (one rule per validator)
    - Use `@model_validator` for multi-field validation
    - Separate models for create/update/response (separation of concerns)
  - Confidence: **High** - Built into FastAPI, v2 is production-ready
  - Source: [FastAPI + Pydantic v2: Validation Without the Drag](https://medium.com/@bhagyarana80/fastapi-pydantic-v2-validation-without-the-drag-17fe1f1771e2)

### Async HTTP Client
- **HTTPX 0.27+**
  - Package: `httpx>=0.27.0`
  - Rationale: Both sync and async support (flexibility), HTTP/2 support, similar API to requests. Better for mixed workloads than aiohttp (async-only).
  - When to use aiohttp instead: If you need absolute maximum performance for high-concurrency scenarios (1000+ concurrent requests)
  - Confidence: **High** - Best balance of features and performance for this use case
  - Source: [Python HTTP Clients: Requests vs. HTTPX vs. AIOHTTP](https://www.speakeasy.com/blog/python-http-clients-requests-vs-httpx-vs-aiohttp)

### CORS Middleware
- **FastAPI built-in CORSMiddleware**
  - Package: Included in FastAPI (`fastapi.middleware.cors`)
  - Configuration:
    ```python
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],  # Vite dev server
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    ```
  - Important: Add CORS middleware FIRST (before other middleware) so it can add headers to all responses including errors
  - Production: Replace wildcard with specific origins
  - Confidence: **High** - Standard approach
  - Source: [CORS (Cross-Origin Resource Sharing) - FastAPI](https://fastapi.tiangolo.com/tutorial/cors/)

---

## AI Integration

### Claude API
- **Anthropic Python SDK 0.40+**
  - Package: `anthropic>=0.40.0`
  - Use `AsyncAnthropic` client for FastAPI integration:
    ```python
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    message = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": "..."}]
    )
    ```
  - Streaming Support:
    ```python
    async with client.messages.stream(...) as stream:
        async for text in stream.text_stream:
            print(text, end="", flush=True)
    ```
  - Rationale: Official SDK with excellent async support, streaming, and type hints
  - Confidence: **High** - Official SDK, well-maintained
  - Source: [Anthropic SDK for Python](https://github.com/anthropics/anthropic-sdk-python)

### Tavily Search API
- **Tavily Python SDK 0.7.21+**
  - Package: `tavily-python>=0.7.21`
  - Usage:
    ```python
    from tavily import TavilyClient

    tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    response = tavily_client.search("query here")
    # Returns: dict with 'results' (list of dicts with 'title', 'url', 'content', 'score')
    ```
  - Async Support: SDK supports both sync and async clients
  - Free Tier: 1,000 credits/month (sufficient for POC)
  - Rationale: Purpose-built for LLM/AI agents, returns structured, pre-processed data with sources
  - Confidence: **High** - Official SDK, actively maintained (last update Jan 30, 2026)
  - Source: [Tavily API: Complete Developer Guide 2025](https://datalevo.com/tavily-api/)

### Async Patterns for AI Calls
- **asyncio.gather()** for parallel AI calls
  - Pattern:
    ```python
    async def analyze_options(option1: str, option2: str):
        results = await asyncio.gather(
            research_option(option1),  # Tavily + Claude
            research_option(option2),  # Tavily + Claude
            return_exceptions=True     # Continue if one fails
        )
        return results
    ```
  - Rationale: Maximize throughput by running AI calls concurrently. Critical for comparing two options simultaneously.
  - Confidence: **High** - Standard pattern for async FastAPI
  - Source: [Concurrency and async / await - FastAPI](https://fastapi.tiangolo.com/async/)

- **FastAPI BackgroundTasks** for long-running operations (optional)
  - Use case: If analysis takes >30s, offload to background task and poll for results
  - For POC: Keep it simple with direct async/await
  - Confidence: **Medium** - Only add if needed

---

## File Persistence

### JSON Storage Pattern
- **pathlib + Atomic Writes**
  - Packages: Built-in `pathlib`, `json`
  - Pattern (atomic write):
    ```python
    from pathlib import Path
    import json
    import tempfile
    import os

    def save_result(data: dict, filename: str):
        results_dir = Path("./results")
        results_dir.mkdir(exist_ok=True)

        target = results_dir / filename

        # Write to temp file, then atomic rename
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=results_dir,
            delete=False,
            suffix='.tmp'
        ) as tmp:
            json.dump(data, tmp, indent=2)
            tmp_path = tmp.name

        os.replace(tmp_path, target)  # Atomic on POSIX/Windows
    ```
  - Rationale: Atomic writes prevent corruption during power loss or crashes. `os.replace()` is atomic on all platforms.
  - Confidence: **High** - Production pattern, survives crashes
  - Source: [Crash-safe JSON at scale: atomic writes + recovery without a DB](https://dev.to/constanta/crash-safe-json-at-scale-atomic-writes-recovery-without-a-db-3aic)

### File Structure
```
results/
  {timestamp}_{sanitized_option1}_vs_{sanitized_option2}.json
```
- Include: full comparison data, criteria, weights, sources, timestamps
- Filename encoding: Use `urllib.parse.quote()` to sanitize option names
- Confidence: **High** - Simple, works for POC

### Library Alternative (if complexity grows)
- **superjson** package for atomic JSON operations
  - Package: `superjson>=1.0.0`
  - Built-in atomic writes, recovery from corrupted files
  - Use if: Manual atomic writes become repetitive
  - Confidence: **Medium** - Nice-to-have, not required for POC

---

## Development Tools

### Linting & Formatting

#### Frontend
- **ESLint 9.x** with TypeScript plugin
  - Packages: `eslint@^9.0.0`, `@typescript-eslint/parser`, `@typescript-eslint/eslint-plugin`
  - Config: Use `eslint.config.js` (flat config, new in ESLint 9)
  - Confidence: **Medium** - Helpful but not critical for POC

- **Prettier 3.x**
  - Package: `prettier@^3.0.0`
  - Config: `.prettierrc` with Tailwind plugin
  - Confidence: **Medium** - Nice for consistency

#### Backend
- **Ruff** (replaces Flake8, Black, isort)
  - Package: `ruff>=0.8.0`
  - Rationale: 10-100x faster than existing tools, written in Rust. Single tool replaces multiple linters/formatters.
  - Commands: `ruff check .` (lint), `ruff format .` (format)
  - Confidence: **High** - Industry standard in 2025
  - Source: [FastAPI Best Practices: Production-Ready Patterns for 2025](https://orchestrator.dev/blog/2025-1-30-fastapi-production-patterns/)

### Testing (Optional for POC)

#### Frontend
- **Vitest** (Vite-native test runner)
  - Package: `vitest@^2.0.0`
  - Rationale: Same config as Vite, instant HMR for tests
  - Confidence: **Low** - Skip for POC, add later

#### Backend
- **pytest** with **pytest-asyncio**
  - Packages: `pytest>=8.0.0`, `pytest-asyncio>=0.24.0`
  - Rationale: Standard for Python testing, excellent async support
  - Confidence: **Low** - Skip for POC, add later

### Environment Management
- **python-dotenv**
  - Package: `python-dotenv>=1.0.0`
  - Usage: Store API keys in `.env` file, load with `load_dotenv()`
  - Confidence: **High** - Essential for security

- **Frontend (.env)**
  - Vite built-in: Use `VITE_` prefix for env vars
  - Example: `VITE_API_URL=http://localhost:8000`
  - Confidence: **High** - Standard Vite pattern

### Dev Server Commands
```bash
# Frontend
cd frontend
npm run dev  # Vite dev server on :5173

# Backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## What NOT to Use

### Frontend
- **Next.js / Remix** - Over-engineered for POC. Adds SSR complexity you don't need. Vite + React is simpler and faster for development.
- **Redux / Redux Toolkit** - TanStack Query handles server state better. For client state, Context API or Zustand are simpler.
- **Formik** - No longer actively maintained. React Hook Form is smaller, faster, and better supported.
- **Tailwind v3** - v4 offers better Vite integration. Use latest.
- **CSS-in-JS (Emotion, Styled Components)** - Tailwind covers styling needs. CSS-in-JS adds runtime overhead.

### Backend
- **Django / Flask** - FastAPI is purpose-built for async APIs. Django's async support is incomplete. Flask lacks native async.
- **aiohttp HTTP client** - HTTPX provides better flexibility (sync+async). Only use aiohttp if you need extreme concurrency (1000+ req/s).
- **SQLAlchemy / any ORM** - You're using JSON files for POC. Don't add database complexity prematurely.
- **Celery for background tasks** - Overkill for POC. FastAPI's BackgroundTasks or simple async is sufficient.
- **Poetry for dependency management** - pip + venv or pip-tools is simpler for small projects. Poetry adds complexity.

### AI Integration
- **LangChain / LlamaIndex** - You have simple, direct API needs (Claude + Tavily). These frameworks add abstraction overhead without value.
- **Custom prompt template engines** - Use f-strings or simple string templates. Don't over-engineer.
- **Vector databases (Pinecone, Weaviate)** - Not needed for POC. You're doing live web search + reasoning, not RAG over stored docs.

### General
- **Docker / Kubernetes** - POC doesn't need containerization. Add when deploying to production.
- **Monorepo tools (Nx, Turborepo)** - Simple frontend/backend split doesn't need tooling overhead.
- **GraphQL** - REST is simpler for this use case. GraphQL adds complexity without clear benefit.

---

## Confidence Levels Summary

### High Confidence (use these)
- React 18 + Vite 6
- Tailwind CSS v4
- TanStack Query v5 (server state)
- React Hook Form
- FastAPI 0.128+ with Python 3.11/3.12
- Uvicorn (dev) + Gunicorn with Uvicorn workers (prod)
- Pydantic v2
- HTTPX (async HTTP client)
- Anthropic SDK (async client)
- Tavily SDK
- pathlib + atomic writes for JSON storage
- Ruff (Python linting/formatting)
- python-dotenv

### Medium Confidence (use if needed)
- TypeScript 5.x (adds value, but POC can skip)
- Zustand (start with Context API, upgrade if needed)
- Axios (fetch is fine too)
- ESLint + Prettier (nice for teams, skip for solo POC)
- FastAPI BackgroundTasks (only if analysis >30s)
- superjson library (if atomic write patterns become repetitive)

### Low Confidence (skip for POC, add later)
- Vitest / pytest (testing frameworks)
- Docker / containerization
- Advanced monitoring/observability tools

---

## Recommended Package Versions

### Frontend (package.json)
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-hook-form": "^7.53.2",
    "@tanstack/react-query": "^5.62.8",
    "axios": "^1.7.9"
  },
  "devDependencies": {
    "vite": "^6.0.5",
    "tailwindcss": "^4.0.0",
    "@tailwindcss/vite": "^4.0.0",
    "@vitejs/plugin-react": "^4.3.4",
    "@tanstack/react-query-devtools": "^5.62.8"
  }
}
```

### Backend (requirements.txt)
```
fastapi>=0.128.0
uvicorn[standard]>=0.32.0
pydantic>=2.10.0
anthropic>=0.40.0
tavily-python>=0.7.21
httpx>=0.27.0
python-dotenv>=1.0.0

# Production
gunicorn>=21.0.0

# Development
ruff>=0.8.0
```

---

## Additional Resources

### Documentation
- [FastAPI Official Docs](https://fastapi.tiangolo.com/)
- [TanStack Query Docs](https://tanstack.com/query/latest)
- [Anthropic API Reference](https://docs.anthropic.com/)
- [Tavily API Docs](https://docs.tavily.com/)
- [React Hook Form](https://react-hook-form.com/)
- [Tailwind CSS v4](https://tailwindcss.com/docs)

### Key Articles Referenced
- [Installing Tailwind CSS with Vite](https://tailwindcss.com/docs)
- [React State Management in 2025: Context API vs Zustand](https://dev.to/cristiansifuentes/react-state-management-in-2025-context-api-vs-zustand-385m)
- [FastAPI production deployment best practices](https://render.com/articles/fastapi-production-deployment-best-practices)
- [Python HTTP Clients: Requests vs. HTTPX vs. AIOHTTP](https://www.speakeasy.com/blog/python-http-clients-requests-vs-httpx-vs-aiohttp)
- [React Hook Form vs Formik - 2025 Comparison](https://www.digitalogy.co/blog/react-hook-form-vs-formik/)
- [Tavily API: Complete Developer Guide 2025](https://datalevo.com/tavily-api/)
- [Crash-safe JSON at scale: atomic writes + recovery without a DB](https://dev.to/constanta/crash-safe-json-at-scale-atomic-writes-recovery-without-a-db-3aic)
- [FastAPI Best Practices: Production-Ready Patterns for 2025](https://orchestrator.dev/blog/2025-1-30-fastapi-production-patterns/)
- [Building FastAPI APIs in 2025: Best Practices & Real-World Guide](https://www.joinmytutor.com/blog/building-fastapi-apis-2025.php)
- [TanStack Query: A Powerful Tool for Data Management in React](https://medium.com/@ignatovich.dm/tanstack-query-a-powerful-tool-for-data-management-in-react-0c5ae6ef037c)

---

*Last updated: 2026-02-01*
*Research conducted for: Prism (AI-powered decision comparison tool)*
