# Product Requirements Document (PRD)

> **Template v2025.9 — B‑MAD Team Fullstack**  
> Status: `Draft v0` · Owner: `<your-name>` · Reviewers: PM • Architect • PO • Security • UX  
> Repo Path: `docs/prd.md` (Shardable via `docs/prd/NN-*.md`)

---

## 1) Executive Summary
- **Product/Initiative:** Agentic Development Methodology & Orchestration Platform *(working title: AxiomFlow)*
- **Problem:** AI coding remains brittle and ad‑hoc (“vibe coding”): context is lost between steps, multi‑agent collaboration is chaotic, and outputs are hard to reproduce or validate. Teams lack a logic‑first, auditable way to plan → execute → evaluate → recover across agents and tools.
- **Proposed Outcome:** A modular, context‑preserving orchestration layer and methodology that enables specialized agents to collaborate via schema‑driven roles, workflow DSLs, and evaluator–optimizer cycles—delivering reliable, measurable, and repeatable software outcomes with minimal manual oversight.
- **Primary KPIs (North Star):** `Workflow success rate`, `Reproducible run rate`, `Time‑to‑First‑Value`, `p95 step latency`, `Handoff defect rate`, `Cost per completed workflow`
- **Guardrails:** `p95 step latency < 2s`, `Routing decision < 150ms`, `SLO 99.5%`, `0 P0 security issues`, `WCAG AA`, `No unreviewed tool invocations in restricted projects`

## 2) Goals & Non‑Goals
### 2.1 Goals (SMART)
- **[G1] Orchestration Kernel + DSL (M3 Beta):** Provide a workflow DSL with schema‑based personas, deterministic context flows, retries, and compensation steps; support local + API tools.
- **[G2] Reproducibility (M4 GA):** ≥ **85%** reproducible runs from the same inputs/config; provenance captured (prompts, tools, artifacts).
- **[G3] Routing Quality:** ≥ **95%** correct agent/skill routing vs. human‑labeled evaluator set; online evaluator backs off misroutes.
- **[G4] Performance:** p95 **<2s** for single step; routing decisions **<150ms**; cold‑start **<2s**.
- **[G5] Integrations:** ≥ **10** first‑party adapters (GitHub/GitLab, Jira, Slack, VCS, shell, HTTP, OpenAI/Anthropic/Azure, Postgres/Redis, S3/GCS).
- **[G6] Safety & Compliance:** Signed adapters, least‑privilege RBAC, project‑scoped secrets, SBOM + policy checks in CI.

### 2.2 Non‑Goals
- Not a model provider or a full IDE replacement (integrates with them).
- Not building a hosted marketplace in MVP; focus on open plugin spec + local/enterprise deploy.
- Not attempting AGI autonomy; emphasize **human‑in‑the‑loop** controls and auditability.

## 3) Users, Personas, JTBD
- **Primary Persona:** Senior Software Engineer / Tech Lead  · **Context:** orchestrating multi‑agent coding & reviews in CI/local  · **Motivation:** ship faster with fewer regressions and less glue code.
- **Secondary Personas:** DevOps/SRE (runtime + policy), Security Engineer (tool permissioning, audits), Product Manager (planning & evidence), QA/AE (spec tests & gates).

**Jobs‑To‑Be‑Done (top 5):**
1. When starting a new feature, I want to compose a logic‑first workflow from reusable blocks so I can get **predictable, audited outcomes**.
2. When an agent fails, I want **automatic recovery** (retry/compensate/escalate) so I can maintain flow without hand‑holding.
3. When multiple agents collaborate, I want **precise control hand‑offs** and shared context so I can avoid duplication and drift.
4. When reviewing outputs, I want **evaluator‑backed validation** and evidence so I can trust merges and deployments.
5. When scaling to a team, I want **role/RBAC + cost controls** so I can run safely in enterprise environments.

## 4) Problem Statement & Evidence
- **Hypothesis:** Current AI‑assisted development breaks down across planning→execution→validation because workflows are not modeled as **explicit logic graphs** with **persisted context** and **evaluable checkpoints**. Multi‑agent tools lack robust routing, structured roles, and deterministic recovery.
- **Evidence (internal target set):** low reproducibility of prompts; hidden tool side effects; handoff defects; long tail of flaky runs; security incidents via over‑permissive tools; high median time lost to glue code.
- **Constraints:** 6–9 person core team; budgeted inference spend; formal security reviews; on‑prem/air‑gapped option for regulated clients.

## 5) Competitive & Alternatives Analysis (Brief)
- **Direct/Adjacent (illustrative):** graph‑based orchestrators and multi‑agent frameworks; dev‑centric copilots with plugins; internal RPA tooling.
- **Strength:** our focus on **logic‑first graphs + evaluator–optimizer cycles + context determinism** and **policy‑guarded tool execution**.
- **Do‑Nothing/DIY:** ad‑hoc scripts + manual review → brittle flows, poor auditability, rising ops cost.

## 6) Solution Overview
- **Concept:** A **logic‑first agent orchestration platform** and **methodology** that composes specialized personas into **modular, context‑preserving workflows**. It integrates planning → execution → evaluator validation → optimization → error recovery, with strong RBAC and audit trails.
- **Key Tenets:** Multi‑Agent Collaboration · Modular Workflows · Flexible Integrations · Role Specialization · End‑to‑End Automation · Precise Handoffs · Evaluator–Optimizer cycles.
- **Scope (MVP → V1):**
  - **MVP:** Orchestration kernel; workflow DSL (YAML/JSON + SDK); persona schema; context store; adapters: shell, HTTP, Git, VCS, LLM APIs; evaluator hooks (spec tests, linters); local runner + minimal web UI; project RBAC + secrets; run provenance.
  - **V1:** Advanced routing (learned + rule hybrid); test‑time self‑play optimizers; UI for graph editing; policy packs (security/compliance); team collaboration (reviews, sign‑offs); enterprise deploy (OIDC/SAML, signed plugins, audit exports).
- **High‑Level Flow:** 1) **Plan** (PM/Architect agents) → 2) **Execute** (Coder/Tooling agents) → 3) **Evaluate** (Spec/Evidence agents) → 4) **Optimize** (Refactor/Retry) → 5) **Archive** (provenance + metrics).

### 6.1 Anti‑Vibe Coding Strategy (System Goal)
To **mitigate the Top‑10 code‑generation failures** common in vibe‑coding tools, we bake controls into three layers:
1. **Design‑time**: schema‑driven personas; typed workflow graphs; policy‑scoped adapters.
2. **Gate‑time**: evaluator gates (PF‑01…PF‑10) enforce compile/security/docs/version checks before merge/deploy.
3. **Run‑time**: routing + retries + compensation; minimal‑diff patcher; rate‑limit aware planner; replayable provenance.

### 6.2 Top‑10 Failure Mitigations (Design → Gate → Metric)
| # | Failure | Controls (Design/Run‑time) | Gate / Evaluator | Metric (Target) |
|---|---|---|---|---|
| 1 | API/Package Hallucinations | Package/API resolver (PyPI/npm); doc cross‑check; stub/compile probe; allow‑list; SCA | **PF‑01 Pre‑Flight**: package exists, symbol resolves, import compiles | Unknown‑symbol compile errors < **0.5/1k LOC** |
| 2 | Deprecated/Misused APIs | Versioned SDK manifests; deprecation DB; safe defaults; parameter validators | **PF‑02 Deprecation**: no deprecated calls; param schema match | CI deprecation warnings < **1%** of builds |
| 3 | Security Vulns | Secure templates; taint‑aware prompts; sandboxed tools; signed adapters | **PF‑03 AppSec**: Semgrep/Bandit/ESLint+security pass; SAST/DAST gates | High/Critical findings = **0** at merge |
| 4 | Context Blindness | Repo indexer; cross‑file dependency graph; constrained edit region | **PF‑04 Cross‑File**: imports/refs validated; graph lints | Cross‑file regressions < **1%** |
| 5 | Non‑Determinism | Seed/temperature policy; stable tool mocks; replay IDs | **PF‑05 Replay**: `replay` reproduces outputs within tolerance | Replay match ≥ **85%** |
| 6 | Repo‑level Reasoning | CI harness; integration test planners; dependency wiring checks | **PF‑06 Integration**: patch passes full CI in sandbox | CI pass‑rate for agent patches ≥ **80%** MVP |
| 7 | Unscoped File Churn | Minimal‑diff patcher; file‑scope guards; write quotas; review hints | **PF‑07 Diff Scope**: max lines changed ratio; forbidden paths | Mean diff size ≤ **1.3×** touched lines |
| 8 | Rate‑Limit/Token Friction | Budget‑aware planner; adaptive batching; retry/backoff; circuit breakers | **PF‑08 Budget**: per‑run token/time caps; graceful degrade | 429s per 100 runs < **1**; success after backoff ≥ **95%** |
| 9 | Weak Auto‑Tests | Spec‑first tasks; coverage goals; mutation tests; property‑based tests | **PF‑09 Test Quality**: branch ≥ 80%; mutation ≥ 60% MVP | Mutation score ≥ **60%** MVP → **75%** GA |
|10 | Version/Dependency Drift | Lockfiles; Renovate‑style updates; compat matrix; semver policy | **PF‑10 Drift**: lock verified; compatibility check | Failing builds from drift < **1%** |

> PF‑XX = Pre‑Flight/Evaluator Gate IDs used throughout the system and CI.
## 7) Functional Requirements
> Epics → User Stories with testable Acceptance Criteria.

### 7.1 Epics
- **E1 — Onboarding & Project Setup** (init project, secrets, adapters, policies)
- **E2 — Workflow Authoring** (DSL + SDK + visual graph editor)
- **E3 — Multi‑Agent Runtime** (routing, handoffs, retries, compensation, minimal‑diff patching)
- **E4 — Evaluator–Optimizer** (spec tests, offline/online evals, **PF‑01…PF‑10** gates, improvement loops)
- **E5 — Context & Memory** (artifact store, session memory, provenance, replay)
- **E6 — Integrations & Tools** (GitHub/GitLab, Jira, Slack, shell/HTTP, LLMs, DBs)
- **E7 — Collaboration & UI** (runs dashboard, evidence view, approvals)
- **E8 — Admin, Billing, Permissions** (RBAC, orgs/teams, usage limits)

### 7.2 User Stories & Acceptance Criteria (sample)
**E1‑S1: Initialize Project**  
_As a lead, I can scaffold a new project with policies, secrets, and adapters._
- **AC:** Template creates `project.yaml`, `secrets` mounts, default RBAC; smoke test passes.

**E2‑S1: Author Workflow (DSL)**  
_As an engineer, I can define a workflow graph with typed inputs/outputs and gates._
- **AC:** Schema validated; deterministic context edges; dry‑run lints unresolved deps.

**E3‑S1: Precise Handoffs**  
_As a runtime, I hand off control between agents with full context and role constraints._
- **AC:** Handoff includes state hash; receiving agent honors role policy; p95 < 200ms.

**E3‑S2: Robust Routing**  
_As a runtime, I route tasks to the best agent/skill using rules + evaluator feedback._
- **AC:** ≥95% agreement with gold set; misroutes trigger backoff/escalation.

**E3‑S3: Error Recovery**  
_As a runtime, I auto‑retry/transact with compensation when tools fail._
- **AC:** Idempotent retries; exponential backoff; compensation steps logged; no data loss.

**E3‑S4: Minimal‑Diff Patching**  
_As a runtime, I generate smallest necessary diffs within allowed scopes._
- **AC:** Diff scope policy enforced; PR template explains changes; forbidden paths blocked.

**E4‑S1: Evaluator Gates**  
_As a reviewer, I require spec tests/linters to pass before progression._
- **AC:** Failing gates halt graph with clear evidence; override requires approver role.

**E4‑S2: Optimizer Loop**  
_As a system, I run targeted refinement using evaluator signals._
- **AC:** At least one measurable metric improves or loop stops with reason.

**E4‑S3: Pre‑Flight Gate (PF‑01…PF‑10)**  
_As a system, I execute all relevant PF checks before commit/merge/deploy._
- **AC:** PF statuses recorded; artifacts attached; gate failures block; replayable locally.

**E5‑S1: Provenance & Replay**  
_As a user, I can replay any run from inputs, config, and artifacts._
- **AC:** Run includes prompt/tool/config digests; `replay` reproduces ≥85% outputs.

**E6‑S1: Tool Adapters**  
_As an engineer, I can add an adapter with signed manifests and permissions._
- **AC:** Adapter declares scopes; signed; sandboxed; audited invocations.

**E7‑S1: Runs Dashboard**  
_As a team, we can view live runs, traces, costs, and evidence._
- **AC:** Real‑time stream; filters by project/workflow/status; export JSON/CSV.

**E8‑S1: RBAC & Quotas**  
_As an admin, I enforce least‑privilege roles and usage limits._
- **AC:** Roles (Owner/Admin/Editor/Runner/Viewer); per‑project quotas; audit log.
## 8) Non‑Functional Requirements (Quality Attributes)
- **Performance:** Routing decision <150ms p95; step execution <2s p95 (tool‑bound); cold‑start <2s.
- **Reliability:** SLO 99.5%; circuit breakers for flaky tools; error budget policy.
- **Determinism & Replay:** Seed locking for model calls where supported; deterministic post‑processing; `replay` achieves ≥85% output match.
- **Scalability:** Horizontal scale to 100 concurrent workflows/node; queue‑backed; stateless runners; sharded stores.
- **Security:** Signed adapters; KMS‑backed secrets; per‑project RBAC; policy engine for tool scopes; SBOM + supply chain attestations.
- **Privacy:** Project isolation; redact PII in logs; retention policies by class.
- **Compliance:** SOC‑2 control mapping; audit log immutability; export for GRC.
- **Accessibility:** WCAG 2.2 AA.
- **Internationalization:** Locale/time‑zone aware; UTF‑8; ISO 8601 times.
## 9) AI/ML‑Specific Requirements
- **Model Targets:** Open/closed models via provider‑agnostic interface; context caps configurable; temperature/cost budgets per step.
- **Latency Budgets:** retrieval ≤ 300 ms; model ≤ 1.2 s; post‑proc ≤ 300 ms.
- **Prompt/Policy:** Central prompt registry; versioned with checksums; change review required.
- **RAG/Data:** Optional; chunking policy; eval set + metrics (recall@k, nDCG) when used.
- **Safety:** Jailbreak filters; output classification; tool‑scope enforcement; sandboxed code tools.
- **Evals:** Spec tests per workflow; regression evals weekly; canaries pre‑deploy.
## 10) Data & Integration
- **Data Model (high level):** Project ▶ Workflows ▶ Runs ▶ Steps ▶ Artifacts ▶ Evaluations ▶ Costs; identities & roles.
- **Sources/Sinks:** Git/VCS, issue trackers, chat, HTTP services, DBs (Postgres, Redis), blob stores (S3/GCS), vector stores (optional), LLM APIs.
- **Retention & Lifecycle:** Runs hot 30–90d → warm 1y → cold/archive; TTL per artifact class.
- **Interoperability:** Open JSON/Parquet exports; import from CI logs; webhook triggers.
## 11) Security, Trust & Compliance Plan
- **Threat Model:** Top: over‑privileged tool execution; prompt injection via artifacts; data exfiltration; supply‑chain compromise; replay tampering.
- **Controls:**
  - Identity/Access: OIDC/SAML; MFA; project‑scoped tokens; IP allow‑lists.
  - AppSec: SAST/DAST; dep scanning; license policy; signed releases.
  - Infra: IaC scanning; secrets via KMS; container isolation; least‑priv RBAC.
  - Supply Chain: SBOM (CycloneDX); SLSA provenance; artifact signing + verify on run.
- **Auditability:** Append‑only audit log; tamper‑evident hashing; export to SIEM.
## 12) Telemetry, Quality & Experimentation
- **Product Analytics:** Workflow funnel (auth → author → run → success); cohort retention; cost per success.
- **Operational Metrics:** Latency, error rate, queue depth, cache hit, tool failures, token consumption, **429 rate**, retry success rate.
- **Gate Metrics:** PF‑01…PF‑10 pass/fail counts; time‑to‑fix; top failing rules; drift alerts.
- **Test Quality:** Branch/line coverage; **mutation score**; flaky test index.
- **Observability:** Structured logs + metrics + traces; per‑step span IDs; flamegraphs for planning/routing.
- **Experimentation:** Feature flags; A/B agent policies; MDE planning; guardrails to cap cost/latency.
## 13) Rollout & Delivery Plan
- **Milestones:**
  - **M0:** PRD Approved (DOR)
  - **M1:** MVP Spec Locked; kernel + DSL + 3 adapters + local runner
  - **M2:** Alpha (internal): evaluator gates + provenance + UI dashboard
  - **M3:** Beta (limited): RBAC, 10 adapters, replay, signed plugins
  - **M4:** GA: enterprise auth, audit exports, policy packs
- **Launch Readiness:** Docs/runbooks; support playbook; pricing/packaging; legal + security sign‑off.
- **Rollback Plan:** Versioned configs; blue/green; reversible migrations.
## 14) Dependencies & Assumptions
- **Internal:** Runtime/SDK team; adapter owners; security review; CI/CD infra.
- **External:** LLM providers; VCS/issue tracker APIs; DBs/blob stores; OIDC IdP.
- **Assumptions:** Users can run containers; network egress to providers; teams adopt workflow DSL incrementally.
## 15) Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| Model/provider drift | M | M | Contract tests; provider abstraction; canaries | Eng |
| Tool API changes | M | H | Adapter versioning; contract tests; feature flags | Eng |
| Over‑permissioned adapters | L | H | RBAC + signed scopes; approvals; audits | Sec |
| Cost overruns | M | M | Budgets, throttles, caching; cost dashboards | PM |
| Low adoption of DSL | M | M | Great DX; codegen; examples; progressive adoption | DX |

## 16) Success Metrics & Targets
- **Workflow Success Rate:** ≥ 80% MVP → ≥ 90% GA  
- **Reproducible Run Rate:** ≥ 85% GA  
- **Handoff Defect Rate:** ≤ 3% GA  
- **Time‑to‑First‑Value:** ≤ 15 min (author → successful run)  
- **p95 Step Latency:** ≤ 2s  
- **Cost per Success:** −30% vs baseline DIY flows  
- **Top‑10 Mitigation Targets:**
  - (1) Unknown‑symbol compile errors < 0.5 / 1k LOC
  - (2) CI deprecation warnings < 1% of builds
  - (3) High/Critical SAST findings at merge = 0
  - (4) Cross‑file regression rate < 1%
  - (5) Replay match ≥ 85%
  - (6) Agent‑patch CI pass‑rate ≥ 80% MVP → 90% GA
  - (7) Mean diff size ≤ 1.3× touched lines
  - (8) 429s < 1 per 100 runs; backoff success ≥ 95%
  - (9) Mutation score ≥ 60% MVP → 75% GA; branch ≥ 80%
  - (10) Drift‑caused failures < 1%
## 17) Open Questions (Track to Close)
- **Q1:** Naming + licensing (OSS core? dual‑license modules?).
- **Q2:** Plugin sandbox model (Wasm vs container vs subprocess isolation?).
- **Q3:** Policy engine (OPA/Rego vs custom) and where to enforce.
- **Q4:** Determinism budget—where to tolerate nondeterminism vs require strict replay.
- **Q5:** UI scope at MVP (CLI‑first vs minimal web vs Graph editor).
## 18) Appendix
- **Glossary:** `<domain terms>`
- **References/Links:** `<relevant docs, ADRs, tickets>`
- **Gate IDs:**
  - **PF‑01 Pre‑Flight (API/Package):** existence, import, symbol resolution, SCA
  - **PF‑02 Deprecation:** no deprecated/unsafe APIs; parameter schema checks
  - **PF‑03 AppSec:** SAST/DAST security gates; policy packs
  - **PF‑04 Cross‑File:** dependency graph validation; unresolved refs lint
  - **PF‑05 Replay:** seed & provenance checks; deterministic post‑processing
  - **PF‑06 Integration:** full CI in sandbox; contract tests
  - **PF‑07 Diff Scope:** minimal‑diff enforcement; path guards
  - **PF‑08 Budget:** token/time budgets; rate‑limit handling
  - **PF‑09 Test Quality:** coverage thresholds; mutation/property tests
  - **PF‑10 Drift:** lock verification; compatibility matrix; Renovate‑style updates

---

### Sharding Plan (optional)
If this file exceeds ~300 lines, split into:
- `docs/prd/01-exec-context.md`
- `docs/prd/02-users-problem.md`
- `docs/prd/03-solution-requirements.md`
- `docs/prd/04-quality-security.md`
- `docs/prd/05-rollout-metrics-risks.md`

> Use PO to validate and shard: `*agent po` → “Shard `docs/prd.md` and produce review checklist results.”


