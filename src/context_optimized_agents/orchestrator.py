"""Top-level context-optimized multi-agent orchestration."""
from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List

from .agents import ParentAgent, SpecializedAgent
from .auditor import ContextAuditor
from .budgets import BudgetAllocator
from .llm import LLMClient, MockLLMClient
from .memory import LayeredMemory, MemoryLayer
from .metrics import MetricsSimulator
from .prompts import prompt_for
from .router import ContextRouter
from .schemas import (
    AgentKind,
    AgentResult,
    AuditReport,
    FinalSynthesis,
    ParentResult,
    TaskPlan,
    WorkflowResult,
    to_dict,
)
from .utils import estimate_tokens, stable_hash


class OrchestrationAgent:
    """Executes the full workflow:

    User Objective -> Orchestration Agent -> Context Router + Budget Allocator ->
    Specialized Agents -> Compressed Findings -> Council/Security Review -> Final Synthesis.
    """

    def __init__(
        self,
        *,
        model: str = "gpt-5.5",
        llm_client: LLMClient | None = None,
        memory: LayeredMemory | None = None,
        budget_allocator: BudgetAllocator | None = None,
        router: ContextRouter | None = None,
        auditor: ContextAuditor | None = None,
        max_parallel_agents: int = 12,
    ) -> None:
        self.model = model
        self.llm_client = llm_client or MockLLMClient()
        self.memory = memory or LayeredMemory.seeded_defaults()
        self.budget_allocator = budget_allocator or BudgetAllocator()
        self.router = router or ContextRouter(default_model=model)
        self.auditor = auditor or ContextAuditor()
        self.max_parallel_agents = max_parallel_agents

    async def arun(self, objective: str, required_output: str = "final synthesis") -> WorkflowResult:
        plan = self.router.make_task_plan(objective, required_output=required_output)
        plan.max_parallel_agents = self.max_parallel_agents
        self.memory.add(MemoryLayer.SESSION, "current_objective", objective, ["session", "objective"])

        packets = self.router.route(plan, self.memory, self.budget_allocator)
        audited_packets, audit_report = self.auditor.audit(packets)

        semaphore = asyncio.Semaphore(plan.max_parallel_agents)

        async def run_packet(packet):
            async with semaphore:
                return await SpecializedAgent(packet, self.llm_client).run()

        agent_results = await asyncio.gather(*(run_packet(packet) for packet in audited_packets))
        parent_results = await self._run_parent_agents(agent_results)
        final = await self._final_synthesis(plan, parent_results, audit_report)
        metrics = MetricsSimulator().simulate()
        decision_record = self._record_decision(plan, final)
        return WorkflowResult(
            task_plan=plan,
            audit_report=audit_report,
            agent_results=list(agent_results),
            parent_results=parent_results,
            final_synthesis=final,
            metrics=metrics,
            decision_memory_record=decision_record,
        )

    def run(self, objective: str, required_output: str = "final synthesis") -> WorkflowResult:
        return asyncio.run(self.arun(objective, required_output=required_output))

    async def _run_parent_agents(self, agent_results: List[AgentResult]) -> List[ParentResult]:
        grouped: Dict[str, List[AgentResult]] = defaultdict(list)
        for result in agent_results:
            grouped[result.parent_group].append(result)

        parent_specs = []
        for group in sorted(grouped):
            if group == "direct_subagents":
                # Direct subagents are merged by a council-style parent to keep a
                # consistent compression step.
                kind = AgentKind.COUNCIL_PARENT.value
                role = "Direct Findings Compression Parent"
                budget = self.budget_allocator.get(AgentKind.COUNCIL_PARENT)
            elif group == "deep_research":
                kind = AgentKind.RESEARCH_PARENT.value
                role = "Deep Research Parent Agent"
                budget = self.budget_allocator.get(AgentKind.RESEARCH_PARENT)
            elif group == "security_review":
                kind = AgentKind.SECURITY_PARENT.value
                role = "Security Review Parent Agent"
                budget = self.budget_allocator.get(AgentKind.SECURITY_PARENT)
            else:
                kind = AgentKind.COUNCIL_PARENT.value
                role = f"Council Parent Agent - {group.replace('council_', '').title()}"
                budget = self.budget_allocator.get(AgentKind.COUNCIL_PARENT)
            parent_specs.append((group, kind, role, budget))

        async def run_parent(group: str, kind: str, role: str, budget):
            parent = ParentAgent(
                parent_id=f"parent-{stable_hash(group, 8)}",
                parent_role=role,
                parent_group=group,
                agent_kind=kind,
                model=self.model,
                input_budget=budget.input_tokens,
                output_budget=budget.output_tokens,
                llm_client=self.llm_client,
                reasoning_effort="high",
            )
            return await parent.run(grouped[group])

        return list(await asyncio.gather(*(run_parent(*spec) for spec in parent_specs)))

    async def _final_synthesis(
        self,
        plan: TaskPlan,
        parent_results: List[ParentResult],
        audit_report: AuditReport,
    ) -> FinalSynthesis:
        budget = self.budget_allocator.get(AgentKind.FINAL_SYNTHESIS)
        system_prompt = prompt_for("final_synthesis")
        payload = {
            "objective": plan.objective,
            "required_output": plan.required_output,
            "parent_results": [to_dict(result) for result in parent_results],
            "audit_report": to_dict(audit_report),
            "decision_memory_policy": [
                "Store final answer.",
                "Store key assumptions.",
                "Store verified evidence.",
                "Store open risks.",
                "Store next actions.",
                "Do not store hidden reasoning traces.",
            ],
        }
        input_tokens = estimate_tokens(system_prompt) + estimate_tokens(payload)
        if input_tokens > budget.input_tokens:
            payload["parent_results"] = [
                {
                    "parent_group": result.parent_group,
                    "compressed_findings": [to_dict(f) for f in result.compressed_findings[:4]],
                    "recommended_actions": result.recommended_actions[:4],
                    "confidence": result.confidence,
                }
                for result in parent_results
            ]
        data = await asyncio.to_thread(
            self.llm_client.generate_json,
            model=self.model,
            system_prompt=system_prompt,
            user_payload=payload,
            schema_name="final_synthesis",
            max_output_tokens=budget.output_tokens,
            reasoning_effort="high",
        )
        return FinalSynthesis(
            final_answer=str(data.get("final_answer", "")),
            key_assumptions=[str(x) for x in data.get("key_assumptions", [])],
            verified_evidence=[str(x) for x in data.get("verified_evidence", [])],
            open_risks=[str(x) for x in data.get("open_risks", [])],
            next_actions=[str(x) for x in data.get("next_actions", [])],
            quality_score=float(data.get("quality_score", 0.0)),
            hallucination_exposure_score=float(data.get("hallucination_exposure_score", 1.0)),
        )

    def _record_decision(self, plan: TaskPlan, final: FinalSynthesis) -> Dict[str, object]:
        record = {
            "id": f"decision-{stable_hash(plan.objective + final.final_answer, 10)}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "objective": plan.objective,
            "final_answer": final.final_answer,
            "key_assumptions": final.key_assumptions,
            "verified_evidence": final.verified_evidence,
            "open_risks": final.open_risks,
            "next_actions": final.next_actions,
        }
        self.memory.add(
            MemoryLayer.DECISION,
            str(record["id"]),
            " | ".join(
                [
                    str(record["objective"]),
                    str(record["final_answer"]),
                    "assumptions=" + "; ".join(final.key_assumptions),
                    "risks=" + "; ".join(final.open_risks),
                ]
            ),
            ["decision", "final-synthesis"],
        )
        return record
