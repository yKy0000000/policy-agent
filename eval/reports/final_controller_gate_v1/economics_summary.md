# Gate 3 - Economics Summary

Authoritative basis: provider-reported tokens and live per-call latency. No judge calls are counted.
No actions were executed (Gate 1 failed), so there is no action cost and no cache-inflated latency.

## All-request sensor overhead (24 calls)

| metric | value |
|---|---:|
| calls | 24 |
| provider input tokens / request | 2,685.6 |
| provider output tokens / request | 90.2 |
| provider total tokens / request | **2,775.8** |
| latency p50 / p95 (s) | 0.934 / 1.428 |
| estimated cost / request | ~$0.000574 |
| executed actions / action cost | 0 / $0 |

Reference: historical `fixed_top5` is **2,533.1 total tokens/query** and **$0.00052381/query**.

## Consequence

- The sensor alone costs more per request in tokens and estimated dollars than the **entire** current
  fixed pipeline answer. Adding it to every request for zero confirmed detections is strictly
  dominated by the existing baseline.
- Trigger rate on this cohort: 1/24 calls produced a non-`RETURN_DRAFT` action; **0** were stable and
  correct. No production prevalence is claimed from a 12-case screen.
- Price basis is an estimate: the repository does not store the external price table
  (`input_per_million` / `output_per_million` were supplied at run time in Stage 1). The blended
  historical `fixed_top5` rate is used only to give an order-of-magnitude comparison; the
  token/latency figures are authoritative.

**Gate 3 verdict: dominated by the simpler baseline.** Even if Gate 1 had passed, an always-on sensor
would need to be justified per request; at ~2.8k tokens it cannot be.
