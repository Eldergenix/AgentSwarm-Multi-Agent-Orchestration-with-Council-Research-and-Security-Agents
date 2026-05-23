"""Context budget allocation for agent roles."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from .schemas import AgentBudget, AgentKind


@dataclass
class BudgetAllocator:
    """Maps agent kinds to strict input/output token budgets.

    The default ranges follow the design in the user-provided workflow and choose
    conservative midpoints suitable for a practical 35-sub-agent workload.
    """

    budgets: Dict[str, AgentBudget] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.budgets:
            return
        self.budgets = {
            AgentKind.ORCHESTRATION.value: AgentBudget(12_000, 1_500),
            AgentKind.CONTEXT_ROUTER.value: AgentBudget(2_000, 600),
            AgentKind.BUDGET_ALLOCATOR.value: AgentBudget(1_000, 400),
            AgentKind.CONTEXT_AUDITOR.value: AgentBudget(2_500, 500),
            AgentKind.DIRECT_SUBAGENT.value: AgentBudget(2_500, 600),
            AgentKind.COUNCIL_SUBAGENT.value: AgentBudget(4_500, 750),
            AgentKind.COUNCIL_PARENT.value: AgentBudget(6_000, 1_000),
            AgentKind.RESEARCH_SUBAGENT.value: AgentBudget(8_000, 1_200),
            AgentKind.RESEARCH_PARENT.value: AgentBudget(10_000, 1_500),
            AgentKind.SECURITY_SUBAGENT.value: AgentBudget(6_000, 900),
            AgentKind.SECURITY_PARENT.value: AgentBudget(8_000, 1_000),
            AgentKind.FINAL_SYNTHESIS.value: AgentBudget(12_000, 2_000),
        }

    def get(self, kind: str | AgentKind) -> AgentBudget:
        key = kind.value if isinstance(kind, AgentKind) else str(kind)
        try:
            return self.budgets[key]
        except KeyError as exc:
            raise ValueError(f"No budget configured for agent kind: {key}") from exc

    def with_override(self, kind: str | AgentKind, input_tokens: int, output_tokens: int) -> "BudgetAllocator":
        key = kind.value if isinstance(kind, AgentKind) else str(kind)
        new = dict(self.budgets)
        new[key] = AgentBudget(input_tokens=input_tokens, output_tokens=output_tokens)
        return BudgetAllocator(new)
