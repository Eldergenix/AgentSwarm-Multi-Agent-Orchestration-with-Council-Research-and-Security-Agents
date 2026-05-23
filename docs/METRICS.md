# Expected Metrics

The project includes a deterministic metrics simulator in `src/context_optimized_agents/metrics.py`.

These values are **expected/simulated** for a representative 35-sub-agent workload. They should be treated as planning estimates until validated against production traces.

## Representative workload

```text
5 direct sub-agents
20 council sub-agents
5 deep research sub-agents
5 security review sub-agents
6 parent agents
1 final synthesis agent
```

## Main results

| Metric | Brute-force | Context-optimized | Unit | Improvement |
|---|---:|---:|---|---:|
| Input tokens | 701,000 | 181,700 | tokens | 74.1% less |
| Output tokens | 53,600 | 23,300 | tokens | 56.5% less |
| Estimated GPT-5.5 token cost | 5.113 | 1.6075 | USD | 68.6% less |
| Duplicate-context ratio | 0.42 | 0.10 | ratio | 76.2% less |
| Mean prompt-to-final latency | 47.5 | 31.2 | seconds | 34.3% less |
| Hallucination exposure score | 0.34 | 0.18 | 0-1 | 47.1% lower |
| Relevant-context density | 0.46 | 0.81 | 0-1 | 76.1% higher |

## Cost assumptions

The simulator uses:

```text
GPT-5.5 input:  $5.00 per 1M tokens
GPT-5.5 output: $30.00 per 1M tokens
```

Tool-call fees, web-search fees, code interpreter fees, and hosted tool fees are excluded.

## Interpretation

The largest savings come from input-token reduction, not output-token reduction. In the brute-force design, every sub-agent receives the same large context. In the optimized design, agents receive a shared capsule plus private role-specific context, and parent agents receive compressed child findings rather than full transcripts.

## Reproduce

```bash
coa metrics
```

Or from Python:

```python
from context_optimized_agents.metrics import MetricsSimulator

metrics = MetricsSimulator().simulate()
for row in metrics.rows:
    print(row)
```
