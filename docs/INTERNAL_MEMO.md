# Internal Memo: WASMnisum — Edge Gateway Benchmark Initiative

**To:** Internal team  
**From:** [Your name]  
**Re:** FYI + feedback on feasibility  
**Date:** March 2025

---

## TL;DR

We're building a **portable edge gateway** that runs the same logic on four platforms (Akamai/Spin, Fastly, Cloudflare Workers, AWS Lambda), then benchmarking **price-per-performance** to produce decision-grade data. The goal: prove that WASM-first edge compute can be compared fairly—and show what it costs to run the same workload across providers. We're asking for feedback on feasibility before we go deeper.

---

## The Idea

**WASMnisum** is a benchmark initiative that answers one question:

> *For the same application workload, what performance do we get and what does it cost—across WASM-first edge platforms and a traditional serverless baseline?*

We use **ClipClap** (CLIP/CLAP image and audio classification) as the "real app" users can understand. Because the ML models are too large for edge runtimes, we split the system:

- **Edge Gateway** (portable): HTTP entrypoint, routing, auth, caching, metrics—deployable as WASM on edge platforms.
- **Inference Service** (unchanged): Existing Python/FastAPI backend that runs the models; hosted separately (container/VM).

The benchmark compares the **gateway layer** across platforms. Same logic, same contract, different runtimes—so the comparison is apples-to-apples.

---

## Why Multiple Tiers?

We use a **two-tier structure** to make the benchmark credible to different audiences:

| Tier | Platforms | Purpose |
|------|-----------|---------|
| **Tier 1** | Akamai Functions (Spin), Fastly Compute, Cloudflare Workers | WASM-first or WASM-capable edge. Answers: *How do edge runtimes compare?* |
| **Tier 2** | AWS Lambda (regional) | Enterprise baseline. Answers: *How does edge compare to our default serverless?* |

**Business rationale:** Executives care about "edge vs Lambda" and cost. Engineers care about "Spin vs Fastly vs Workers" and latency. One benchmark serves both.

**Technical rationale:** Tier 1 platforms share a WASM/edge story but differ in runtime (WASI-first vs isolate-with-WASM). Tier 2 validates that our gateway logic is portable beyond edge—and gives a familiar reference point.

---

## Justification

1. **Precedent:** We've done this before (rag-ray-haystack: RAG across LKE, EKS, GKE). Same methodology: infra parity, measurement contract, median of N runs, cost per outcome. It worked.

2. **Narrative:** "WASMnisum" frames the methodology—portable module, minimal host coupling, benchmarking tied to cost-per-outcome—without claiming industry adoption of the term. Useful for a blog series and internal storytelling.

3. **Decision-grade:** Raw numbers (p50/p95 latency, RPS, error rate, cost per 1M requests at SLO) that engineers can verify and executives can use for budgeting.

4. **Reproducibility:** Open methodology, scripts, and config templates. Others can run it and validate.

---

## Feasibility Snapshot

| Factor | Assessment |
|--------|------------|
| Architecture | Clear split; no ML rewrites. Gateway is the portable unit. |
| Platforms | Spin, Fastly, Workers, Lambda all have mature SDKs. |
| ClipClap | Small, documented API. Inference stays as-is. |
| Risk | Platform quirks (cold starts, limits). Mitigation: start with Spin, document differences. |

**Estimated success:** 70–85% for full delivery (all platforms, benchmark, scorecard). Higher if we scope to 2–3 platforms first.

---

## Ask

We'd like your feedback on:

1. **Feasibility:** Any concerns or blind spots we're missing?
2. **Tier structure:** Does Tier 1 vs Tier 2 make sense for how we talk about this internally?
3. **Scope:** Should we target all four platforms, or ship with 2–3 and add the rest later?

Reply with thoughts or schedule a short sync.
