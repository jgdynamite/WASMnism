# Cost Model: Price per 1M Requests

## Methodology

Cost is calculated for 1 million requests at each benchmark mode.
Pricing uses the public rate card for each platform as of March 2026.
All costs are in USD.

---

## Platform Pricing Summary

### Akamai Functions (Fermyon Cloud / Spin)

| Component | Rate |
|-----------|------|
| Requests | $0.50 per 1M requests |
| Compute | $18/mo per dedicated core (included in free tier for low volume) |
| KV Store reads | $0.50 per 1M reads |
| KV Store writes | $1.00 per 1M writes |
| Bandwidth | $0.08/GB |

### Fastly Compute

| Component | Rate |
|-----------|------|
| Requests | $0.40 per 10K requests ($40 per 1M) |
| Compute (WASM exec) | Included in request price |
| KV Store reads | $0.50 per 1M reads |
| KV Store writes | $5.00 per 1M writes |
| Bandwidth | $0.08/GB |

### Cloudflare Workers

| Component | Rate |
|-----------|------|
| Requests (Standard) | $0.30 per 1M requests |
| CPU time | $0.02 per 1M ms of CPU time |
| KV reads | $0.50 per 1M reads |
| KV writes | $5.00 per 1M writes |
| Bandwidth | Free (included) |

### AWS Lambda

| Component | Rate |
|-----------|------|
| Requests | $0.20 per 1M requests |
| Compute | $0.0000133 per GB-second (128MB ARM64) |
| DynamoDB reads | $0.25 per 1M read capacity units |
| DynamoDB writes | $1.25 per 1M write capacity units |
| NAT Gateway | $0.045/hr + $0.045/GB (for outbound to inference) |
| Bandwidth | $0.09/GB |

---

## Cost Calculation Template

### Per-Test Assumptions

| Test | Avg Response Size | KV Reads | Compute Weight | Notes |
|------|------------------|----------|----------------|-------|
| Warm Light (health) | ~0.2 KB | 0 | Minimal | No ML, no policy |
| Warm Heavy (ML) | ~1 KB | 0 | ~850ms CPU | ML toxicity inference |

### Cost per 1M Requests

*To be filled after benchmark runs with actual response sizes and timing data.*

| Platform | Test | Requests | Compute | KV | Bandwidth | Total |
|----------|------|----------|---------|----|-----------| ------|
| Spin | warm-light | | | N/A | | |
| Spin | warm-heavy | | | N/A | | |
| Fastly | warm-light | | | N/A | | |
| Fastly | warm-heavy | | | N/A | | |
| Workers | warm-light | | | N/A | | |
| Workers | warm-heavy | | | N/A | | |
| Lambda | warm-light | | | N/A | | |
| Lambda | warm-heavy | | | N/A | | |

---

## Notes

- Pricing is based on public rate cards and may differ from negotiated enterprise contracts.
- Free tier allocations are NOT included in calculations (we assume production-scale volume).
- The gateway is self-contained — no external inference calls, so no NAT Gateway costs.
- Warm-heavy cost is dominated by CPU time (ML inference ~850ms per request).
- Bandwidth costs use average response size from benchmark measurements.
- All prices are pay-as-you-go; reserved capacity or committed use discounts are excluded.
