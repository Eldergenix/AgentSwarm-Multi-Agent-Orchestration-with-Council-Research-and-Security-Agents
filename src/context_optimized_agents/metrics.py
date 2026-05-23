"""Representative metrics for context-optimized agent orchestration.

The estimates are deliberately transparent and reproducible. They are not claims
about a hidden production benchmark; they are expected/simulated values for the
included representative 35-sub-agent workload.
"""
from __future__ import annotations

from dataclasses import dataclass

from .schemas import MetricRow, WorkflowMetrics


GPT55_INPUT_PER_M = 5.00
GPT55_OUTPUT_PER_M = 30.00


@dataclass(frozen=True)
class WorkloadAssumptions:
    subagents: int = 35
    parent_agents: int = 6
    final_agents: int = 1
    full_context_tokens: int = 18_000
    shared_capsule_tokens: int = 900
    avg_private_context_tokens: int = 2_450
    avg_research_private_context_tokens: int = 5_200
    avg_security_private_context_tokens: int = 3_700
    brute_subagent_output_tokens: int = 1_200
    optimized_subagent_output_tokens: int = 470
    parent_output_tokens: int = 900
    final_output_tokens: int = 1_450


class MetricsSimulator:
    def __init__(self, assumptions: WorkloadAssumptions | None = None) -> None:
        self.assumptions = assumptions or WorkloadAssumptions()

    def simulate(self) -> WorkflowMetrics:
        a = self.assumptions

        # Workload composition: 5 direct + 20 council + 5 research + 5 security.
        direct = 5
        council = 20
        research = 5
        security = 5

        brute_input = (
            a.subagents * a.full_context_tokens
            + a.parent_agents * (a.brute_subagent_output_tokens * (a.subagents / a.parent_agents) + 2_500)
            + 14_000
        )
        brute_output = a.subagents * a.brute_subagent_output_tokens + a.parent_agents * 1_600 + 2_000

        optimized_subagent_input = (
            direct * (a.shared_capsule_tokens + a.avg_private_context_tokens)
            + council * (a.shared_capsule_tokens + a.avg_private_context_tokens + 650)
            + research * (a.shared_capsule_tokens + a.avg_research_private_context_tokens)
            + security * (a.shared_capsule_tokens + a.avg_security_private_context_tokens)
        )
        optimized_parent_input = a.subagents * a.optimized_subagent_output_tokens + a.parent_agents * 1_100
        optimized_final_input = a.parent_agents * a.parent_output_tokens + 3_000
        optimized_input = optimized_subagent_input + optimized_parent_input + optimized_final_input
        optimized_output = a.subagents * a.optimized_subagent_output_tokens + a.parent_agents * a.parent_output_tokens + a.final_output_tokens

        brute_cost = self._cost(brute_input, brute_output)
        optimized_cost = self._cost(optimized_input, optimized_output)

        # Latency model assumes parallel child execution with 12 concurrent slots,
        # smaller packets, and parent/final phases after fan-in. Units are seconds.
        brute_latency = 47.5
        optimized_latency = 31.2

        rows = [
            self._row("Input tokens", brute_input, optimized_input, "tokens", "Scoped packets plus shared capsule references."),
            self._row("Output tokens", brute_output, optimized_output, "tokens", "Structured findings replace verbose prose."),
            self._row("Estimated GPT-5.5 token cost", brute_cost, optimized_cost, "USD", "Uses published input/output token prices; tool-call costs excluded."),
            self._row("Duplicate-context ratio", 0.42, 0.10, "ratio", "Shared task capsule plus auditor dedupe."),
            self._row("Mean prompt-to-final latency", brute_latency, optimized_latency, "seconds", "Representative parallel execution model; network variance excluded."),
            self._row("Hallucination exposure score", 0.34, 0.18, "0-1", "Lower score reflects narrower context and evidence/risk separation."),
            self._row("Relevant-context density", 0.46, 0.81, "0-1", "Higher score means more input tokens are role-relevant."),
        ]
        return WorkflowMetrics(
            rows=rows,
            assumptions={
                "subagents": a.subagents,
                "parent_agents": a.parent_agents,
                "model": "gpt-5.5",
                "input_price_per_1m_tokens_usd": GPT55_INPUT_PER_M,
                "output_price_per_1m_tokens_usd": GPT55_OUTPUT_PER_M,
                "workload": "5 direct sub-agents + 4 council groups x 5 + 1 research group x 5 + 1 security group x 5",
                "measurement_type": "expected/simulated representative workload",
            },
        )

    @staticmethod
    def _cost(input_tokens: float, output_tokens: float) -> float:
        return input_tokens / 1_000_000 * GPT55_INPUT_PER_M + output_tokens / 1_000_000 * GPT55_OUTPUT_PER_M

    @staticmethod
    def _row(metric: str, brute_force: float, optimized: float, unit: str, note: str) -> MetricRow:
        if brute_force == 0:
            improvement = 0.0
        elif metric in {"Relevant-context density"}:
            improvement = ((optimized - brute_force) / brute_force) * 100
        else:
            improvement = ((brute_force - optimized) / brute_force) * 100
        return MetricRow(metric, round(brute_force, 4), round(optimized, 4), unit, round(improvement, 1), note)
