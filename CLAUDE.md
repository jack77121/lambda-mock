# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **POXA Calc Service** - a serverless ESS (Energy Storage System) IRR evaluation platform built with SST (Serverless Stack). The architecture combines Next.js frontend, Python FastAPI backend, and AWS Lambda functions with PostgreSQL database.

## Essential Commands

### Development

```bash
# Frontend development
pnpm dev                    # Start Next.js dev server with Turbopack

# Backend development server
PYTHONPATH=./backend uv run fastapi dev backend/server/main.py

# Build frontend
pnpm build
```

### Database Operations

```bash
# Run from backend/server/ directory
alembic upgrade head                              # Apply all migrations
alembic revision --autogenerate -m "description" # Create new migration
alembic downgrade -1                             # Rollback one migration
```

### Testing

```bash
# Load testing (50 concurrent requests)
./concurrent_test.sh                 # Run concurrent API tests
```

## Architecture

### Project Structure

- **Backend Server**: FastAPI development server in `backend/server/`
- **Shared Models**: Common Pydantic models in `backend/shared/`
- **Lambda Functions**: Production handlers in `v1_lambda_ess_irr_evaluation/`
- **Infrastructure**: SST config in `sst.config.ts`

### Database Schema

Two main tables managed by SQLAlchemy with async support:

- **`reqs`**: Stores API requests with JSONB `input_params`
- **`ans`**: Stores API responses with JSONB `output_result`, foreign key to `reqs`

All models use UUID primary keys and automatic timestamps. Migrations are in `backend/server/alembic/versions/`.

### Lambda Architecture

The ESS IRR evaluation Lambda (`v1_lambda_ess_irr_evaluation/`) handles:

- Async database operations with proper session management
- Request/response logging to PostgreSQL
- JSON validation with Pydantic models
- Container runtime for improved performance

## Package Management

### Python (UV Workspace)

The project uses UV workspace with `pyproject.toml` files:

- Root workspace coordinates shared dependencies
- Each component has its own dependencies in `pyproject.toml`
- Custom SST Python SDK from dev branch

### Node.js (PNPM Workspace)

Frontend managed by PNPM with `pnpm-workspace.yaml`:

- Shared dependencies across workspace
- Turbopack for fast development builds

## Environment Setup

### AWS Configuration

- Uses profiles: `calc-poxa-staging` and `calc-poxa-production`
- API Gateway v1 with custom domains
- Manual API key setup required in AWS console

## Development Patterns

### Async Database Operations

All database operations use async/await pattern:

```python
async with get_async_session() as session:
    # Database operations here
```

### Request/Response Logging

API calls are logged to database with unique IDs:

- `request_id`: Links request to response
- `answer_id`: Unique response identifier

### Error Handling

Lambda functions return structured JSON responses:

```python
{
    "success": bool,
    "request_id": str,
    "answer_id": str,
    "result": {...}
}
```

## Deployment

### Staging vs Production

- **Staging**: `staging.api.calc.poxa.app`
- **Production**: `api.calc.poxa.app`
- Both use SSL with custom certificates
- API Gateway usage plans with API keys

### Infrastructure as Code

All AWS resources defined in `sst.config.ts`:

- Lambda functions with container runtime
- API Gateway with CORS enabled
- Database secrets management
- Custom domain mapping
