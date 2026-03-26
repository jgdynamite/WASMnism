# WASMnism Benchmark Contract

**Version:** 3.0  
**Date:** March 26, 2026  
**Status:** Active

---

## 1. Purpose

This document defines the measurement contract for the WASMnism benchmark.
Any compliant gateway implementation — on any platform — MUST conform to these
schemas, SLOs, and fairness rules so results are directly comparable.

A third party should be able to implement a gateway from this contract alone,
deploy it on any of the target platforms, and produce results that are
apples-to-apples comparable with every other implementation.

v3.0 replaces the v2.0 three-mode benchmark with a **five-test suite**
that isolates cold start, warm-light, warm-heavy (ML inference),
concurrency scaling, and latency consistency. The gateway now performs
content moderation with an embedded ML toxicity classifier (MiniLMv2,
22.7M params) running entirely inside the WASM sandbox — the dominant
compute cost on every request containing text.

---

## 2. Architecture Overview

```
┌──────────────┐      ┌─────────────────────────────────────┐
│  k6 runner   │─────▶│  Edge Moderation Gateway (WASM)     │
│              │◀─────│                                      │
└──────────────┘      │  1. Unicode NFC normalize            │
                      │  2. SHA-256 content hash             │
                      │  3. Leetspeak expansion              │
                      │  4. Prohibited content scan          │
                      │  5. PII detection (regex)            │
                      │  6. Injection detection              │
                      │  7. ML toxicity classifier           │
                      │     (MiniLMv2, Tract NNEF, in-WASM)  │
                      │  8. Policy verdict composition       │
                      └─────────────────────────────────────┘
```

Five benchmark tests:

| Test | Script | What It Measures |
|------|--------|-----------------|
| **Cold Start** | `cold-start.js` | WASM module instantiation + ML model deserialization |
| **Warm Light** | `warm-light.js` | Minimal-work latency (`GET /gateway/health`) |
| **Warm Heavy** | `warm-heavy.js` | Full moderation + ML inference (`POST /gateway/moderate` with text) |
| **Concurrency Ladder** | `concurrency-ladder.js` | Scaling behavior under increasing VUs (1→50) with ML |
| **Consistency** | `consistency.js` | Latency jitter over a sustained 120s run with ML |

The gateway is self-contained — no external inference service calls. All
computation including neural network inference runs inside the WASM sandbox.

---

## 3. Moderation Request / Response Schemas

### 3.1 Moderation Request

`POST /gateway/moderate` — `application/json`

```json
{
  "labels": ["safe", "unsafe"],
  "nonce": "<string>",
  "text": "The prompt text to evaluate"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `labels` | array of strings | yes | 1–1000 items |
| `nonce` | string | yes | max 256 chars |
| `text` | string | conditionally | Required for ML inference; omit for policy-only |

When `text` is provided and non-empty, the ML toxicity classifier runs.
When `text` is absent or empty, only rule-based policy checks execute.

### 3.2 Moderation Response

All platforms MUST return this exact JSON schema. Field order MAY vary;
field names, types, and nesting MUST NOT.

```json
{
  "verdict": "allow | block | review",
  "moderation": {
    "policy_flags": ["prohibited_term", "pii_detected", "injection_attempt"],
    "confidence": 0.0,
    "blocked_terms": ["kill", "[injection]"],
    "processing_ms": 862.1,
    "ml_toxicity": {
      "toxic": 0.001,
      "severe_toxic": 0.0001,
      "inference_ms": 858.9,
      "model": "MiniLMv2-toxic-jigsaw"
    }
  },
  "classification": { ... },
  "cache": {
    "hit": false,
    "hash": "sha256:<64 hex chars>"
  },
  "gateway": {
    "platform": "<spin | fastly | workers | lambda>",
    "region": "<string>",
    "request_id": "<uuid>"
  }
}
```

**Validation rules:**

- `verdict` MUST be one of: `allow`, `block`, `review`.
- `moderation.policy_flags` MUST be an array (may be empty).
- `moderation.confidence` MUST be a float 0.0–1.0.
- `moderation.processing_ms` MUST reflect actual gateway processing time (including ML inference).
- `moderation.ml_toxicity` MUST be present when `text` was provided and non-empty; null otherwise.
- `moderation.ml_toxicity.inference_ms` MUST reflect actual ML forward pass time.
- `cache.hit` MUST be a boolean.
- `cache.hash` MUST start with `sha256:` followed by 64 hex characters.
- `gateway.platform` MUST be one of the four target platforms.
- `gateway.request_id` MUST be a UUID v4.
- HTTP status MUST be `200` on success.

### 3.3 Verdict Logic

**Pre-check (all modes):**

| Condition | Verdict | Flag |
|-----------|---------|------|
| Input contains prohibited terms | `block` | `prohibited_term` |
| Input contains PII patterns (email, phone, SSN) | `review` | `pii_detected` |
| Input contains injection patterns (XSS, SQL) | `block` | `injection_attempt` |
| No flags | `allow` | _(none)_ |

**ML toxicity check (when text is provided):**

| Condition | Verdict | Flag |
|-----------|---------|------|
| `toxic` or `severe_toxic` ≥ 0.80 | `block` | ML toxicity score in response |
| `toxic` ≥ 0.50 | `review` | ML toxicity score in response |
| Below thresholds | `allow` | _(none)_ |

**Merge rule:** The stricter verdict wins (block > review > allow).

### 3.4 Cache Behavior

| Endpoint | Cache Read | Cache Write |
|----------|-----------|-------------|
| `POST /gateway/moderate` | No | No |
| `POST /gateway/moderate-cached` | Yes (by label hash) | No |

Cache key: SHA-256 of normalized labels (NFC + lowercase + whitespace collapsed).

---

## 4. ML Inference Contract

### 4.1 Embedded Inference

The gateway performs ML inference **locally** inside the WASM sandbox.
There is no external inference service call. The Tract NNEF runtime
loads the model from bundled files at startup.

| Component | Detail |
|-----------|--------|
| Model | MiniLMv2-toxic-jigsaw (22.7M params) |
| Format | NNEF (Tract native) |
| Vocab | 8,000 WordPiece tokens |
| Model size | ~53 MB |
| Categories | `toxic`, `severe_toxic` |

### 4.2 Inference Timing

| Phase | Typical | Notes |
|-------|---------|-------|
| Model deserialization | ~800ms | Cold start only |
| WordPiece tokenization | <1ms | Custom Rust tokenizer |
| Forward pass | ~850ms | Warm, on Fermyon Cloud |
| Total gateway processing | ~860ms | Including all 8 pipeline steps |

### 4.3 Headers

The gateway MUST set the following response headers:

| Header | Value |
|--------|-------|
| `Content-Type` | `application/json` |
| `X-Gateway-Platform` | `spin`, `fastly`, `workers`, or `lambda` |
| `X-Gateway-Region` | Deployment region (e.g., `us-ord`) |
| `X-Gateway-Request-Id` | UUID v4, generated per request |

---

## 5. Platform KV Store Mapping

Each platform uses its native KV store:

| Platform | KV Implementation | Store Name |
|----------|------------------|------------|
| Akamai Functions (Spin) | `spin_sdk::key_value::Store` | `default` |
| Fastly Compute | `fastly::KVStore` | `moderation_cache` |
| Cloudflare Workers | `worker::kv` | `MODERATION_CACHE` |
| AWS Lambda | DynamoDB | `moderation-cache` |

---

## 6. Service Level Objectives (SLO)

SLOs define the performance bar. They are NOT pass/fail gates for the
benchmark; they are the reference lines on the scorecard.

### 6.1 Cold Start SLO

| Metric | Target | Notes |
|--------|--------|-------|
| p50 cold start | ≤ 3000 ms | WASM instantiation + ML model deserialization |
| p90 cold start | ≤ 5000 ms | Includes platform scheduling variance |
| Error rate | 0% | Cold starts must not fail |

### 6.2 Warm Light SLO (GET /gateway/health)

| Metric | Target | Notes |
|--------|--------|-------|
| p50 latency | ≤ 20 ms | Minimal-work, no ML |
| p95 latency | ≤ 60 ms | Includes platform overhead |
| Error rate | ≤ 0.1% | Over full benchmark run |
| Throughput | ≥ 400 RPS | At 10 concurrent connections |

### 6.3 Warm Heavy SLO (POST /gateway/moderate with text)

| Metric | Target | Notes |
|--------|--------|-------|
| p50 latency | ≤ 1500 ms | Dominated by ML inference (~850ms) |
| p95 latency | ≤ 3000 ms | Includes model reload or scheduling |
| Error rate | ≤ 1% | ML inference may occasionally time out |
| Throughput | ≥ 1 RPS | At 5 concurrent connections |

### 6.4 Concurrency Ladder SLO

| Metric | Target | Notes |
|--------|--------|-------|
| Error rate | ≤ 10% | At peak 50 VUs with ML inference |
| Latency degradation | ≤ 5x baseline | p50 at 50 VUs vs p50 at 1 VU |

### 6.5 Consistency SLO

| Metric | Target | Notes |
|--------|--------|-------|
| Jitter (p95/p50) | ≤ 3.0x | Predictable latency over 120s |
| Error rate | ≤ 5% | Over sustained run |

### 6.6 Measurement Method

- **Timing source:** Client-side (k6 `http_req_duration`). This is the
  source of truth for the scorecard.
- **Server-side timing** (`moderation.processing_ms`, `ml_toxicity.inference_ms`)
  is recorded for analysis but does not determine scorecard values.
- **Suite runner:** `bench/run-suite.sh` orchestrates all 5 tests with a
  pre-flight health check and warm-up request.
- **Warm-up:** The suite sends one `POST /gateway/moderate` request before
  starting any test to trigger ML model loading.
- **Scorecard:** Generated by `bench/build-scorecard.py` comparing any two
  results directories.

---

## 7. Fairness Rules

Every platform is benchmarked under identical conditions. Any deviation
invalidates the comparison.

### 7.1 Payload Invariance

| Rule | Detail |
|------|--------|
| Same labels | `["safe", "unsafe"]` — consistent across all ML tests |
| Same prompt pool | 5 rotating prompts (see `warm-heavy.js`) |
| Same nonce pattern | `<test>-<vu>-<iter>` for traceability |

Changing the prompt pool or labels invalidates all prior results.

### 7.2 Concurrency Ladder

The `concurrency-ladder.js` test uses this progression:

| Stage | Duration | Virtual Users (VUs) |
|-------|----------|---------------------|
| Hold 1 | 30 s | 1 |
| Hold 2 | 30 s | 5 |
| Hold 3 | 30 s | 10 |
| Hold 4 | 30 s | 25 |
| Hold 5 | 30 s | 50 |

**Total:** 150 seconds. No explicit warm-up stage — the suite runner
sends a warm-up request before starting any test.

### 7.3 Multi-Region Testing

Tests are run from **3 geographic locations** to capture regional variance:

| Region | Runner Location | Purpose |
|--------|----------------|---------|
| US Central | Linode us-ord (Chicago) | Near inference service |
| Europe | Linode eu-west (London) | Transatlantic latency |
| Asia-Pacific | Linode ap-south (Singapore) | Maximum distance |

Each region runs the full benchmark suite independently.

### 7.4 Cold Start Protocol

Cold start latency is measured by `cold-start.js`:

1. Send a `POST /gateway/moderate` request with text (triggers ML).
2. Record full round-trip time.
3. Wait 120 seconds for the WASM instance to be evicted.
4. Repeat for 10 iterations.
5. Report p50, p90, and max cold start latency.

The `--cold` flag on `run-suite.sh` enables this test (skipped by default
because it takes ~20 minutes).

### 7.5 Deployment Configuration

| Parameter | Requirement |
|-----------|-------------|
| Memory | Platform default (document actual value) |
| CPU | Platform default (document actual value) |
| Scaling | Single instance, no auto-scale during run |
| KV Store | Platform-native (see §5) |
| Caching | No CDN or response caching; bypass if platform enables by default |
| TLS | Required (HTTPS). All platforms use TLS. |

### 7.6 ML Model Consistency

- All platforms MUST use the same model file (`model.nnef.tar`) and
  vocabulary (`vocab.txt`).
- Model files are bundled into the WASM component at build time.
- No external inference service is called.

### 7.7 Result Integrity

- Raw k6 JSON output is saved to `results/<platform>/<timestamp>/`.
- Each test produces one JSON file: `warm-light.json`, `warm-heavy.json`,
  `concurrency-ladder.json`, `consistency.json`, and optionally `cold-start.json`.
- Raw results are **gitignored** (may contain IPs/hostnames).
- Scorecards are generated by `bench/build-scorecard.py` and also gitignored.
- All results from a benchmark session use the same k6 version and runner.

---

## 8. Scorecard Format

The scorecard is generated by `bench/build-scorecard.py` from the k6
JSON exports. For cross-platform comparison, run the suite against each
platform and compare any two results directories.

### 8.1 Warm Latency Table (per platform pair)

```
| Metric         | Platform A | Platform B | Ratio |
|----------------|-----------|-----------|-------|
| Light p50      |           |           |       |
| Light p95      |           |           |       |
| Heavy p50      |           |           |       |
| Heavy p95      |           |           |       |
| ML infer p50   |           |           |       |
| Heavy RPS      |           |           |       |
| Error rate     |           |           |       |
```

### 8.2 Concurrency & Consistency Table

```
| Metric               | Platform A | Platform B | Ratio |
|----------------------|-----------|-----------|-------|
| Ladder p50           |           |           |       |
| Ladder p95           |           |           |       |
| Ladder error rate    |           |           |       |
| Consistency p50      |           |           |       |
| Jitter (p95/p50)     |           |           |       |
```

### 8.3 Cold Start Table

```
| Metric         | Platform A | Platform B | Ratio |
|----------------|-----------|-----------|-------|
| Cold p50       |           |           |       |
| Cold p90       |           |           |       |
| Cold max       |           |           |       |
```

### 8.4 Cost Table

```
| Platform | $/1M Requests (warm heavy) | $/1M Requests (warm light) |
|----------|---------------------------|---------------------------|
| Spin     |                           |                           |
| Fastly   |                           |                           |
| Workers  |                           |                           |
| Lambda   |                           |                           |
```

---

## 9. Moderation Validation

Before running performance benchmarks, each platform MUST pass the moderation
validation suite to prove correctness. The suite sends the same safe image
(`bench/fixtures/benchmark.jpg`) with different label/text payloads and
asserts identical verdicts across all platforms.

### 9.1 Validation Scenarios

| # | Name | Labels | Text | Expected Verdict | Expected Flag |
|---|------|--------|------|-----------------|---------------|
| S1 | Clean input | `["cat","dog","<unique>"]` | — | `allow` | _(none)_ |
| S2 | XSS injection | `["<script>alert(1)</script>"]` | — | `block` | `injection_attempt` |
| S3 | Prohibited terms | `["kill","bomb","cat"]` | — | `block` | `prohibited_term` |
| S4 | PII email | `["cat","dog"]` | `"contact user@example.com"` | `review` | `pii_detected` |
| S5 | PII phone | `["cat"]` | `"call 555-123-4567"` | `review` | `pii_detected` |
| S6 | Leetspeak evasion | `["h@t3","k1ll"]` | — | `block` | `prohibited_term` |
| S7 | SQL injection | `["cat'; DROP TABLE users;--"]` | — | `block` | `injection_attempt` |
| S8 | Cache hit | _(repeat S1 labels)_ | — | `allow` | `cache.hit: true` |
| S9 | Image not blocklisted | `["sunrise","mountain","river"]` | — | `allow` | `image_blocklisted: false` |

S1 uses a timestamped label to guarantee a cache miss and fresh inference.

### 9.2 Additional Assertions (S1 only)

- `moderation.safety_scores` MUST be present (array of 10 safety labels).
- All safety scores MUST be below 0.50 (safe image).
- `classification.results` MUST contain only user-supplied labels (safety labels stripped).

### 9.3 Running Validation

```bash
./bench/run-validation.sh <platform> <gateway_url>
```

Exit code 0 = all 9 scenarios passed. Any non-zero exit = at least one check failed.

All four platforms must produce 9/9 pass before performance benchmarks are run.

---

## 10. Versioning

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-03-05 | Initial contract (thin proxy architecture) |
| 2.0 | 2026-03-10 | Moderation gateway: 3 benchmark modes, multi-region, cold start protocol, KV store caching, updated scorecard |
| 2.1 | 2026-03-25 | Safety labels, image blocklist, moderation validation suite (9 scenarios), text field extraction |
| 3.0 | 2026-03-26 | Embedded ML toxicity classifier; 5-test benchmark suite (cold start, warm light, warm heavy, concurrency ladder, consistency); removed external inference proxy; updated SLOs for ML workload |
