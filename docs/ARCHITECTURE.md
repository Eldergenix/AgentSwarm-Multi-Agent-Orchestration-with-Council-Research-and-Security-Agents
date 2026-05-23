# Architecture

## Objective

The workflow converts a brute-force multi-agent system into a context-optimized orchestration architecture. The key change is to prevent every agent from seeing the full prompt, full documents, full memory, full tool state, and full prior conversation.

Instead, each agent receives a scoped context packet that includes:

1. A small shared task capsule.
2. Role-specific private context.
3. Strict input and output token budgets.
4. Forbidden context rules.
5. Retrieval policy for progressive disclosure.
6. A structured output schema.

## End-to-end flow

```text
User Objective
  -> Orchestration Agent
  -> Context Router
  -> Budget Allocator
  -> Context Auditor
  -> Specialized Agent Groups
  -> Parent Compression Agents
  -> Council Review + Security Review
  -> Final Synthesis
  -> Decision Memory
```

## Core modules

| Module | Responsibility |
|---|---|
| `OrchestrationAgent` | Owns the end-to-end run, creates task plan, executes agents, merges parent results, and records decision memory. |
| `ContextRouter` | Classifies task and builds role-specific context packets. |
| `BudgetAllocator` | Provides strict input/output token budgets by agent kind. |
| `ContextAuditor` | Deduplicates repeated context, removes over-budget retrieved memory, and flags warnings. |
| `LayeredMemory` | Separates session, project, user, working, retrieval, and decision memory. |
| `SpecializedAgent` | Executes sub-agent work and returns structured findings. |
| `ParentAgent` | Compresses child findings and removes duplication before final synthesis. |
| `MetricsSimulator` | Provides transparent expected metrics for a representative workload. |

## Memory layers

| Layer | Purpose | Default access pattern |
|---|---|---|
| Session Memory | Current conversation/task state | Most agents can receive scoped session facts. |
| Project Memory | Architecture, repo conventions, product decisions | Most agents can receive relevant project facts. |
| User Memory | Stable preferences and long-term constraints | Deny by default; opt-in when directly relevant. |
| Working Memory | Temporary execution scratchpad | Council/quality agents may receive summaries. |
| Retrieval Memory | Searchable documents, specs, code, research | Research agents receive targeted chunks. |
| Decision Memory | Final decisions and accepted tradeoffs | Written after final synthesis; not broadly resent. |

## Context packet lifecycle

1. The Orchestration Agent creates a task plan.
2. The Context Router generates a small shared task capsule.
3. The Router creates private packets for 35 sub-agents.
4. The Budget Allocator assigns strict budgets by agent kind.
5. The Context Auditor removes duplicated retrieved memory and over-budget payloads.
6. Sub-agents return compact structured findings.
7. Parent agents compress child findings into review summaries.
8. Final Synthesis uses only parent summaries, audit report, and decision policy.
9. Decision Memory stores only final answer, assumptions, evidence, risks, and next actions.

## Agent groups

```text
5 direct sub-agents
4 council groups x 5 sub-agents each = 20 council sub-agents
1 deep research group x 5 sub-agents
1 security review group x 5 sub-agents
6 parent compression agents
1 final synthesis agent
```

## Why this reduces token waste

A brute-force system repeats the same prompt, documents, memory, and tool instructions across parallel agents. The optimized design reduces this waste by:

- Reusing a small shared task capsule.
- Sending private context only to agents that need it.
- Denying irrelevant memory layers by default.
- Compressing child results before parent review.
- Auditing packets for duplicate or excessive context.
- Deferring retrieval until a specific missing context request is made.

## Failure modes and mitigations

| Failure mode | Mitigation |
|---|---|
| Router excludes context needed for cross-domain reasoning | Agents add precise `open_questions`; progressive retrieval returns targeted chunks. |
| Compression removes critical evidence | Parent agents preserve evidence identifiers and material disagreements. |
| Retrieved content injects malicious instructions | Security prompt treats retrieved content as untrusted data only. |
| Memory leakage across roles | Retrieval policies allow-list memory layers and deny other layers by default. |
| Metrics are misinterpreted as measured production results | Documentation labels them expected/simulated until live benchmarks are run. |
