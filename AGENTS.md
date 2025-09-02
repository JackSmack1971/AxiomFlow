# AGENTS.md: AI Collaboration Guide

This document provides essential context for AI models interacting with this project. Adhering to these guidelines will ensure consistency, maintain code quality, and optimize agent performance within the AxiomFlow platform.

*It is Monday, September 01, 2025. This guide is optimized for clarity, efficiency, and maximum utility for modern AI coding agents working on the AxiomFlow agentic development orchestration platform.*

## 1. Project Overview & Purpose
*   **Primary Goal:** AxiomFlow is a logic-first agent orchestration platform that coordinates specialized AI agents through schema-driven workflows, deterministic context management, and evaluator-optimizer cycles. It enables reliable, auditable, and repeatable software development outcomes through multi-agent collaboration.
*   **Business Domain:** AI-Assisted Software Development, Developer Tools, Agent Orchestration, DevOps Automation
*   **Key Features:** Workflow orchestration via DSL, multi-agent runtime with intelligent routing, context-preserving handoffs, anti-vibe coding controls (PF-01 to PF-10), quality assurance gates, integration framework, audit & compliance capabilities

## 2. Core Technologies & Stack
*   **Languages:** Python 3.12+, TypeScript 5.x, JavaScript ES2023, YAML/JSON for DSL definitions
*   **Frameworks & Runtimes:** Django 5.2+ (backend), React 18.x (frontend), Node.js 20.x, FastAPI (API layer), PostgreSQL (transactional data), Redis (cache/sessions)
*   **Databases:** PostgreSQL (main database), Redis (session cache, task queues), InfluxDB (time-series metrics), Elasticsearch (logs and search indexing)
*   **Key Libraries/Dependencies:** 
    - Backend: Django REST Framework, Celery, SQLAlchemy, Pydantic, pytest-django
    - Frontend: React hooks, TypeScript, Vite, Tailwind CSS
    - ML/AI: OpenAI SDK, Anthropic SDK, Azure OpenAI
    - Infrastructure: Docker, Kubernetes, S3-compatible storage
*   **Platforms:** Linux containers, Kubernetes, Cloud-native deployment (AWS/Azure/GCP), on-premises enterprise
*   **Package Manager:** uv (Python), pnpm (JavaScript/TypeScript)

## 3. Architectural Patterns
*   **Overall Architecture:** Microservices-based orchestration platform with clear separation between workflow DSL parsing, agent runtime execution, context management, and evaluator systems. Event-driven architecture with message queues for agent coordination.
*   **Directory Structure Philosophy:** 
    - `/src`: Contains all primary source code organized by service boundaries
    - `/workflows`: Workflow DSL definitions and templates  
    - `/agents`: Agent persona definitions and routing logic
    - `/adapters`: Tool integration adapters with security sandboxing
    - `/evaluators`: Gate implementations (PF-01 to PF-10) and quality checks
    - `/tests`: Comprehensive unit, integration, and end-to-end tests
    - `/docs`: Technical documentation, API specs, and architectural decisions
    - `/configs`: Environment configurations and deployment manifests
*   **Module Organization:** Domain-driven design with bounded contexts for workflow management, agent runtime, context storage, adapter framework, and evaluation system. Each service has its own data models and API boundaries.

## 4. Coding Conventions & Style Guide
*   **Formatting:** 
    - Python: Follow PEP 8, use Black formatter with 100-character line limit
    - TypeScript: Use Prettier with 2-space indentation, single quotes, trailing commas
    - YAML: 2-space indentation for workflow DSL files
*   **Naming Conventions:**
    - Python: `snake_case` for variables/functions, `PascalCase` for classes, `SCREAMING_SNAKE_CASE` for constants
    - TypeScript: `camelCase` for variables/functions, `PascalCase` for components/types/interfaces
    - Workflow DSL: `kebab-case` for workflow names, `snake_case` for variable names
    - Files: `snake_case` for Python modules, `camelCase` for TypeScript files
*   **API Design:** RESTful APIs with OpenAPI specifications, consistent error response formats, versioned endpoints, idempotent operations where possible
*   **Common Patterns & Idioms:**
    - **Async/Await:** Extensive use for non-blocking agent coordination
    - **Context Preservation:** Immutable context objects passed between agents with cryptographic hashing
    - **Circuit Breakers:** For handling external service failures and rate limits
    - **Event Sourcing:** For audit trails and workflow replay capabilities
    - **Dependency Injection:** For testable adapter and evaluator implementations
*   **Error Handling:** 
    - Custom exception hierarchy with detailed error codes
    - Structured logging with correlation IDs across services
    - Graceful degradation with fallback strategies
    - Automatic retry with exponential backoff for transient failures
*   **Documentation Style:** 
    - Python: Comprehensive docstrings following Google style
    - TypeScript: JSDoc comments for all public interfaces
    - API documentation: OpenAPI 3.0 specifications with examples

## 5. Key Files & Entrypoints
*   **Main Entrypoints:** 
    - `src/orchestrator/main.py` - Main orchestration service
    - `src/api/server.py` - REST API server
    - `src/ui/app.tsx` - React frontend application
*   **Configuration:** 
    - `configs/orchestrator.yaml` - Main platform configuration
    - `configs/agents/*.yaml` - Agent persona definitions
    - `configs/policies/*.yaml` - Security and evaluation policies
    - `.env` files for environment-specific settings
*   **CI/CD Pipeline:** `.github/workflows/` - GitHub Actions for automated testing, security scanning, and deployment
*   **DSL Schema:** `schemas/workflow-dsl.json` - JSON schema for workflow validation

## 6. Development & Testing Workflow
*   **Local Development Environment:**
    1. Install Python 3.12+ and uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
    2. Install Node.js 20+ and pnpm: `npm install -g pnpm`
    3. Set up backend: `cd backend && uv install`
    4. Set up frontend: `cd frontend && pnpm install`
    5. Start services: `docker-compose up -d` (databases), `uv run python manage.py runserver`, `pnpm dev`
*   **Build Commands:**
    - Backend: `uv run python -m build`
    - Frontend: `pnpm build`
    - Docker images: `docker build -t axiomflow .`
*   **Testing Commands:** **All new code requires corresponding unit tests**
    - Backend tests: `uv run pytest tests/ --cov=src/`
    - Frontend tests: `pnpm test --run --coverage`
    - Integration tests: `uv run pytest tests/integration/`
    - End-to-end tests: `pnpm test:e2e`
    - **MUST** mock external dependencies (OpenAI, GitHub APIs, etc.) using pytest-mock and Mock Service Worker
*   **Linting/Formatting Commands:** **All code MUST pass lint checks before committing**
    - Backend: `uv run black . && uv run isort . && uv run ruff check .`
    - Frontend: `pnpm lint --fix && pnpm format`
    - Security scanning: `uv run bandit -r src/ && pnpm audit`
*   **CI/CD Process:** GitHub Actions run automated tests, security scans (Semgrep, Bandit), dependency checks, and deploy to staging on PR merge. Production deploys require manual approval.

## 7. Specific Instructions for AI Collaboration
*   **Anti-Vibe Coding Controls:** This project implements PF-01 to PF-10 gates to prevent common AI coding failures. **You MUST ensure your code passes all relevant gates:**
    - **PF-01 API Validation:** Verify all API calls use real, documented endpoints
    - **PF-02 Deprecation Checks:** Avoid deprecated APIs and patterns
    - **PF-03 Security Analysis:** Pass SAST scans (Bandit, Semgrep)
    - **PF-04 Cross-File Dependencies:** Maintain proper import relationships
    - **PF-05 Replay Validation:** Ensure deterministic behavior where possible
    - **PF-06 Integration Testing:** New features must pass full CI pipeline
    - **PF-07 Diff Scope Control:** Keep changes focused and minimal
    - **PF-08 Budget Management:** Be mindful of API rate limits and costs
    - **PF-09 Test Quality:** Maintain >80% branch coverage, >60% mutation score
    - **PF-10 Drift Detection:** Keep dependencies up-to-date and compatible

*   **Security Best Practices:**
    - **NEVER** hardcode secrets, API keys, or sensitive credentials
    - Use environment variables and secure secret management
    - Validate all user inputs on both client and server
    - Follow OWASP guidelines for web application security
    - Generate secure code that prevents CWE Top 25 weaknesses

*   **Dependencies:** 
    - Python: Use `uv add <package>` for adding new dependencies
    - TypeScript: Use `pnpm add <package>` for new dependencies
    - **Always** update lock files and verify compatibility

*   **Commit Messages & Pull Requests:**
    - Follow Conventional Commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`
    - Include clear description of what changed and why
    - Reference issue numbers when applicable
    - Ensure all PR checks pass before requesting review

*   **Forbidden Actions:**
    - **NEVER** use `@ts-expect-error` or `@ts-ignore` without clear justification
    - **NEVER** push directly to `main` branch - always use pull requests
    - **NEVER** commit secrets or credentials to version control
    - **DO NOT** modify production configuration files without approval
    - **NEVER** bypass security gates or evaluator checks

*   **Workflow DSL Guidelines:**
    - Follow the JSON schema in `schemas/workflow-dsl.json`
    - Use semantic versioning for workflow versions
    - Include comprehensive input/output documentation
    - Test workflows in sandbox before deploying

*   **Agent Development:**
    - Agents must declare their capabilities and constraints clearly
    - Use typed interfaces for agent communication
    - Implement proper error handling and timeout mechanisms
    - Follow the persona schema for agent definitions

*   **Context Management:**
    - Preserve immutable context across agent handoffs
    - Include provenance information for audit trails  
    - Use cryptographic hashing for context integrity
    - Implement deterministic serialization where possible

*   **Quality Assurance & Verification:**
    - **ALWAYS** run the full test suite after making changes
    - Verify all evaluator gates pass before submitting code
    - Include evidence and metrics for code quality claims
    - Run security scans and address any findings

*   **Debugging Guidance:**
    - Include full stack traces and error details when reporting bugs
    - Use structured logging with correlation IDs
    - Leverage the replay system for reproducing issues
    - Check evaluator gate outputs for specific failure reasons

*   **Performance Considerations:**
    - Target <2s for step execution (p95)
    - Keep routing decisions under 150ms
    - Use caching and circuit breakers for external services
    - Monitor resource usage and implement proper limits

Remember: This platform is designed to eliminate "vibe coding" through systematic quality controls. Every code change should pass the anti-vibe gates and contribute to measurable, reproducible outcomes.
