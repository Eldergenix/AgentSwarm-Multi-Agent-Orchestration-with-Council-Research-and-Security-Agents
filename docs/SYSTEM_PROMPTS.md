# System Prompts

The canonical prompt file is:

```text
prompts/system_prompts.json
```

The Python source copy is:

```text
src/context_optimized_agents/prompts.py
```

## Orchestration Agent

Creates the task plan, roles, budgets, schemas, and review sequence. It prevents unnecessary context broadcast.

## Context Router

Classifies the task and decides the minimum context each agent should see, what it must never see, and what can be retrieved later.

## Budget Allocator

Enforces strict input/output budgets and recommends compression or retrieval deferral when packets are over budget.

## Context Auditor

Detects duplication, irrelevant chunks, budget overruns, and sensitive information leakage. It does not solve the task.

## Sub-Agent

Works only on the assigned focus area and returns compact structured findings without chain-of-thought or long prose.

## Council Parent

Merges child findings, removes duplicates, identifies disagreements, and evaluates conclusions against the rubric.

## Research Parent

Compresses evidence-oriented findings, separates evidence from assumptions, and flags unsupported claims.

## Security Parent

Checks permissions, retrieved content, prompt injection, tool calls, memory leakage, and hallucination exposure.

## Final Synthesis

Uses compressed findings only, distinguishes evidence from assumptions, and writes decision-grade memory.
