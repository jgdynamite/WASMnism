# WASMnisum Execution Plan

**For:** Opus 4.6 agent (coding)  
**From:** Composer 1.5 (planning)  
**Date:** March 5, 2025

---

## Will This Project Work? Success Probability

### Short Answer

**Yes.** Estimated **70–85% probability** of full success (all 4 platforms deployed, benchmark harness runs, scorecard produced, blog-ready).

### Why It’s Viable

| Factor | Assessment |
|--------|------------|
| **Precedent** | rag-ray-haystack proves you’ve shipped a similar benchmark (3 clouds, Terraform, scorecard, blog). Same pattern. |
| **Architecture** | Split is clear: gateway (portable) vs inference (unchanged). No ML rewrites. |
| **ClipClap** | Small, documented API. Schemas are stable. Inference stays as-is. |
| **Platform maturity** | Spin, Fastly, Cloudflare Workers, Lambda all have stable SDKs and docs. |
| **Benchmark methodology** | k6 + 7-run median is proven (MLPerf/SPEC-style). |

### Risks and Mitigations

| Risk | Probability | Mitigation |
|------|-------------|------------|
| **Platform-specific quirks** (cold starts, limits) | Medium | Start with Spin (best WASM docs), then port. Document differences in benchmark_contract. |
| **Multipart proxy complexity** | Low | Gateway can stream multipart through; or use base64 for benchmark payloads (simpler). |
| **Cost data accuracy** | Low | Use published pricing; document assumptions. Same approach as rag-ray-haystack. |
| **Scope creep** | Medium | Phase 1–2 must be done before adding platforms. Gateway-only benchmark first. |
| **ClipClap maintenance** | Low | Repo is small; fork if needed. API is simple. |

### Success Tiers

- **Tier A (85%):** Gateway on 3+ platforms, benchmark runs, scorecard, blog draft.
- **Tier B (95%):** Gateway on 2 platforms (Spin + Lambda), benchmark runs, scorecard.
- **Tier C (99%):** Gateway on Spin only, gateway-only benchmark, proof of concept.

**Recommendation:** Target Tier A. If blocked on a platform, ship Tier B and document the blocker.

---

## Handoff to Opus 4.6

**Role split:**
- **Composer 1.5:** Planning, contracts, structure, risk assessment.
- **Opus 4.6:** Implementation, coding, deployment, benchmarking.

**Before coding, Opus should:**
1. Read `docs/CLIPCLAP_INSPECTION.md` for API details.
2. Read `docs/benchmark_contract.md` (create in Phase 1).
3. Read `.cursorrules` for security and structure.
4. Use this document as the task list.

---

## Phase 1: Benchmark Contract (Do First)

**Goal:** Lock the benchmark so all implementations measure the same thing.

### Tasks

| # | Task | Deliverable | Notes |
|---|------|--------------|-------|
| 1.1 | Define gateway request/response schema | `docs/benchmark_contract.md` | Match ClipClap `ClassificationResponse` exactly. |
| 1.2 | Define gateway ↔ inference contract | Same doc | `/api/clip/classify`, `/api/clap/classify` as upstream. Timeouts, error mapping. |
| 1.3 | Define gateway-only path | Same doc | e.g. `GET /gateway/health` or `POST /gateway/echo` with deterministic response. Used for pure edge benchmark. |
| 1.4 | Define SLO for benchmark | Same doc | e.g. p95 ≤ 150ms (gateway-only), error rate ≤ 0.1%. |
| 1.5 | Define fairness rules | Same doc | Same payload sizes, same concurrency ladder, same regions. |

### Acceptance Criteria

- [ ] `benchmark_contract.md` exists and is unambiguous.
- [ ] A third party could implement a gateway from the contract alone.

---

## Phase 2: Edge Gateway Core + Spin Adapter

**Goal:** One working gateway on Spin as the reference implementation.

### Tasks

| # | Task | Deliverable | Notes |
|---|------|-------------|-------|
| 2.1 | Create `edge-gateway/` structure | `edge-gateway/core/`, `edge-gateway/adapters/spin/` | Prefer Rust→WASM for portability; JS/TS acceptable if faster to ship. |
| 2.2 | Implement gateway-only handler | `/gateway/health` or `/gateway/echo` | Deterministic JSON response. No inference call. |
| 2.3 | Implement proxy to inference | `/api/clip/classify`, `/api/clap/classify` | Forward multipart to `INFERENCE_URL` env var. |
| 2.4 | Spin manifest + build | `spin.toml`, `make deploy-spin` or equivalent | Deploy to Akamai/Spin. |
| 2.5 | Verify identical JSON schema | Manual test | Same input → same schema across gateway-only and proxy paths. |

### Acceptance Criteria

- [ ] `make deploy-spin` (or `spin deploy`) deploys successfully.
- [ ] Gateway-only path returns valid JSON per contract.
- [ ] Proxy path returns same schema as ClipClap when inference is running.
- [ ] No secrets in code; `INFERENCE_URL` from env.

### Gotchas

- Spin uses `spin.toml`; ensure WASM binary is built for `wasi` target.
- Multipart in Rust/WASM: use `http-body` or similar; or simplify benchmark to base64 + JSON.

---

## Phase 3: Additional Platform Adapters

**Goal:** Same gateway logic on Fastly, Cloudflare, Lambda.

### Tasks

| # | Task | Deliverable | Notes |
|---|------|-------------|-------|
| 3.1 | Fastly Compute adapter | `edge-gateway/adapters/fastly/` | Fastly Compute SDK; same request/response. |
| 3.2 | Cloudflare Workers adapter | `edge-gateway/adapters/workers/` | Workers + WASM or Workers JS with same contract. |
| 3.3 | AWS Lambda adapter | `edge-gateway/adapters/lambda/` | Native Rust or Node; same contract. Lambda is Tier 2 baseline. |
| 3.4 | Deploy scripts | `deploy/fastly/`, `deploy/cloudflare/`, `deploy/aws/` | `make deploy-fastly`, etc. |

### Acceptance Criteria

- [ ] All four platforms return identical JSON schema for same input.
- [ ] One-command deploy per platform.
- [ ] Document runtime differences (WASI vs isolate) in README.

### Order of Implementation

1. Spin (reference)
2. Lambda (simplest, validates contract)
3. Fastly or Cloudflare (pick one; both are edge)
4. Remaining platform

---

## Phase 4: Benchmark Harness

**Goal:** Repeatable k6 runs, raw JSON results, scorecard output.

### Tasks

| # | Task | Deliverable | Notes |
|---|------|-------------|-------|
| 4.1 | k6 script for gateway-only | `bench/gateway-only.js` | Concurrency ladder: 1, 10, 50, 100. |
| 4.2 | k6 script for gateway+inference | `bench/full.js` | Optional; document separately. |
| 4.3 | Run wrapper | `bench/run.sh` or `make bench` | Accept platform, URL, output path. |
| 4.4 | Results aggregation | `bench/aggregate.py` or similar | Median of N runs; output `scorecard.md`, `scorecard.csv`. |
| 4.5 | Multi-region notes | `bench/README.md` | How to run from US, EU, APAC. |

### Acceptance Criteria

- [ ] `make bench` (or equivalent) runs 7 times, outputs median.
- [ ] Raw JSON in `results/` (gitignored).
- [ ] `scorecard.md` with p50/p95/p99, RPS, error rate.

### Config

- Use `bench/run_config.example.yaml` with placeholder URLs.
- Never commit `run_config.yaml` with real URLs.

---

## Phase 5: Cost Model

**Goal:** Cost per 1M requests at SLO for each platform.

### Tasks

| # | Task | Deliverable | Notes |
|---|------|-------------|-------|
| 5.1 | Cost config template | `cost/cost-config.example.yaml` | Platform pricing inputs. |
| 5.2 | Cost calculation script | `cost/compute_cost.py` | Map benchmark results + config → $/1M requests. |
| 5.3 | Scorecard integration | Add cost column to `scorecard.md` | Same format as rag-ray-haystack. |

### Acceptance Criteria

- [ ] Cost per 1M requests at SLO for each platform.
- [ ] Assumptions documented.
- [ ] No real account IDs or internal pricing in repo.

---

## Phase 6: Blog Post Prep (Optional, Post-MVP)

- Executive summary template
- Narrative hook (WASMnisum / “portable module”)
- Disclosure block
- Reproduce instructions (clone, deploy, bench)

---

## Suggested Opus 4.6 Workflow

1. **Session 1:** Phase 1 — draft `benchmark_contract.md`.
2. **Session 2:** Phase 2 — gateway core + Spin adapter.
3. **Session 3:** Phase 3 — Lambda adapter (validates contract across very different runtime).
4. **Session 4:** Phase 3 — Fastly and/or Cloudflare.
5. **Session 5:** Phase 4 — benchmark harness.
6. **Session 6:** Phase 5 — cost model.

Each phase has clear acceptance criteria. If blocked, document the blocker and move to the next phase.

---

## Files to Create (Checklist)

```
docs/
  benchmark_contract.md    # Phase 1
  EXECUTION_PLAN.md       # This file (done)
  CLIPCLAP_INSPECTION.md  # Done

edge-gateway/
  core/                   # Shared logic
  adapters/
    spin/
    fastly/
    workers/
    lambda/

deploy/
  spin/
  fastly/
  cloudflare/
  aws/

bench/
  gateway-only.js
  run.sh
  run_config.example.yaml
  aggregate.py
  README.md

cost/
  cost-config.example.yaml
  compute_cost.py

.env.example
```

---

## Security Reminders for Opus

- Never commit: `.env`, `cost-config.yaml`, `run_config.yaml`, raw benchmark JSON.
- Use `INFERENCE_URL`, `FASTLY_API_TOKEN`, etc. from env.
- `.gitignore` already excludes these; double-check before commit.
