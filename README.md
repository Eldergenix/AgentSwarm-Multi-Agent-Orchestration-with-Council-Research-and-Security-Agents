# Context-Optimized Agents

A runnable Python project implementing a context-optimized multi-agent orchestration pattern:

```text
User Objective
  -> Orchestration Agent
  -> Context Router + Budget Allocator
  -> Specialized Agent Groups
  -> Compressed Findings
  -> Council Review + Security Review
  -> Final Synthesis + Decision Memory
```

The core design principle is **minimum sufficient context**: each agent receives a scoped context packet, returns compact structured findings, and passes only compressed outputs upward.

## What is included

- Python package: `context_optimized_agents`
- CLI entry point: `coa`
- Offline deterministic mock mode requiring no API key
- Optional OpenAI live mode using `gpt-5.5`
- Strict input/output budget allocation by agent type
- Context Router, Context Auditor, layered memory, hierarchical compression, council review, security review, and final synthesis
- Structured JSON output schemas for sub-agents, parent agents, and final synthesis
- Academic-style architecture diagram in SVG, PNG, and PDF
- Reproducible expected metrics simulator
- Bundled system prompts for every workflow role
- Unit tests

## Quick start

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[diagram]
python -m context_optimized_agents run --print-final \
  "Create a context optimized multi-agent workflow with routing, budgets, compression, council review, security review, metrics, and decision memory."
```

The command writes a full JSON run artifact to:

```text
runs/workflow_result.json
```

## CLI usage

### Run the workflow offline

```bash
coa run --mode mock --print-final \
  "Design a context-optimized agent architecture for a production AI workflow."
```

### Run against OpenAI live mode

```bash
pip install -e .[live]
export OPENAI_API_KEY="..."
coa run --mode live --model gpt-5.5 --output runs/live_result.json \
  "Evaluate this architecture and produce a final synthesis."
```

Live mode uses the OpenAI Responses API with strict JSON schema output. The default project configuration routes all model calls to `gpt-5.5`.

### Generate the diagram

```bash
pip install -e .[diagram]
coa diagram --output-dir docs/figures
```

Generated files:

```text
docs/figures/context_orchestrator_academic_diagram.svg
docs/figures/context_orchestrator_academic_diagram.png
docs/figures/context_orchestrator_academic_diagram.pdf
```

### Print metrics

```bash
coa metrics
```

### Export system prompts

```bash
coa prompts --output prompts/system_prompts.json
```

## Agent topology

The implemented workflow uses the topology specified in the prompt:

| Group | Count | Purpose |
|---|---:|---|
| Direct Sub-Agents | 5 | Architecture, implementation, metrics, memory, output contracts |
| Council Agents | 4 x 5 = 20 | Factuality, reasoning, product, and quality review |
| Deep Research Agents | 5 | Evidence, tradeoffs, cost, latency, reliability |
| Security Review Agents | 5 | Injection, memory leakage, permissions, sensitive operations, hallucination exposure |
| Parent Agents | 6 | Compress, deduplicate, compare, and summarize child findings |
| Final Synthesis Agent | 1 | Produces final answer and decision-memory record |

## Context packet contract

Each sub-agent receives:

```json
{
  "agent_id": "...",
  "agent_kind": "security_subagent",
  "agent_role": "Security Review Sub-Agent",
  "parent_group": "security_review",
  "focus_area": "Prompt injection risk",
  "model": "gpt-5.5",
  "budget": {"input_tokens": 6000, "output_tokens": 900},
  "shared_capsule": {
    "objective": "...",
    "task_type": "implementation",
    "constraints": ["..."],
    "definitions": {"progressive_disclosure": "..."},
    "output_schema_name": "agent_result"
  },
  "private_context": {
    "role_instruction": "...",
    "focus_area": "...",
    "retrieved_memory": [],
    "task_specific_rubric": ["..."]
  },
  "forbidden_context": ["Full raw conversation", "Credentials", "Hidden scratchpad"],
  "retrieval_policy": {
    "allowed_memory_layers": ["project", "session"],
    "requires_specific_request": true
  },
  "output_schema": "agent_result"
}
```

## Structured finding contract

Sub-agent output:

```json
{
  "agent_role": "Security Review Sub-Agent",
  "focus_area": "Prompt injection risk",
  "findings": [
    {
      "claim": "Untrusted retrieved content can steer tool calls if not isolated.",
      "evidence": ["Research agents may ingest arbitrary external text."],
      "confidence": "high",
      "risk": "Tool misuse or instruction override.",
      "recommended_action": "Sandbox retrieved content as data and separate it from system instructions."
    }
  ],
  "issues": [
    {
      "issue": "Untrusted retrieved content can attempt to override instructions.",
      "severity": "high",
      "evidence": "Retrieval memory is used by research agents.",
      "recommendation": "Treat retrieved content as data only."
    }
  ],
  "confidence": "high",
  "open_questions": []
}
```

## Expected metrics

The included simulator models a representative 35-sub-agent workload. These are expected/simulated metrics, not claims from a production benchmark.

| Metric | Brute-force | Context-optimized | Expected improvement |
|---|---:|---:|---:|
| Input tokens | 701,000 | 181,700 | 74.1% less |
| Output tokens | 53,600 | 23,300 | 56.5% less |
| Estimated GPT-5.5 token cost | $5.11 | $1.61 | 68.6% less |
| Duplicate-context ratio | 0.42 | 0.10 | 76.2% less |
| Mean prompt-to-final latency | 47.5s | 31.2s | 34.3% less |
| Hallucination exposure score | 0.34 | 0.18 | 47.1% lower |
| Relevant-context density | 0.46 | 0.81 | 76.1% higher |

Cost estimates use the published GPT-5.5 token price assumption bundled in `metrics.py`: $5.00 per 1M input tokens and $30.00 per 1M output tokens. Tool-call fees are excluded.

## Run tests

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## Key files

```text
src/context_optimized_agents/orchestrator.py  # full workflow execution
src/context_optimized_agents/router.py        # task classification and scoped context packets
src/context_optimized_agents/auditor.py       # dedupe, redaction, budget enforcement
src/context_optimized_agents/agents.py        # sub-agent and parent-agent execution
src/context_optimized_agents/llm.py           # mock and OpenAI Responses API clients
src/context_optimized_agents/metrics.py       # expected metrics simulator
src/context_optimized_agents/diagrams.py      # academic diagram generation
prompts/system_prompts.json                   # workflow system prompts
examples/sample_output.json                   # sample run artifact
```

## Source notes

OpenAI API conventions were checked against the official OpenAI API documentation. The project uses the Responses API and `gpt-5.5` as the default model. See `docs/SOURCES.md` for source URLs and notes.
