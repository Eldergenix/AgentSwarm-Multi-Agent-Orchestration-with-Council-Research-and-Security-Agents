"""Agent execution primitives."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from .llm import LLMClient
from .prompts import prompt_for
from .schemas import (
    AgentKind,
    AgentResult,
    ContextPacket,
    ParentResult,
    agent_result_from_dict,
    finding_from_dict,
    to_dict,
)
from .utils import estimate_tokens, unique_preserve_order


class SpecializedAgent:
    def __init__(self, packet: ContextPacket, llm_client: LLMClient) -> None:
        self.packet = packet
        self.llm_client = llm_client

    async def run(self) -> AgentResult:
        system_prompt = prompt_for("subagent")
        payload = {"packet": to_dict(self.packet)}
        input_tokens = estimate_tokens(system_prompt) + estimate_tokens(payload)
        data = await asyncio.to_thread(
            self.llm_client.generate_json,
            model=self.packet.model,
            system_prompt=system_prompt,
            user_payload=payload,
            schema_name="agent_result",
            max_output_tokens=self.packet.budget.output_tokens,
            reasoning_effort=self.packet.reasoning_effort,
        )
        output_tokens = estimate_tokens(data)
        return agent_result_from_dict(data, self.packet, input_tokens, output_tokens)


class ParentAgent:
    def __init__(
        self,
        parent_id: str,
        parent_role: str,
        parent_group: str,
        agent_kind: str,
        model: str,
        input_budget: int,
        output_budget: int,
        llm_client: LLMClient,
        reasoning_effort: str = "high",
    ) -> None:
        self.parent_id = parent_id
        self.parent_role = parent_role
        self.parent_group = parent_group
        self.agent_kind = agent_kind
        self.model = model
        self.input_budget = input_budget
        self.output_budget = output_budget
        self.llm_client = llm_client
        self.reasoning_effort = reasoning_effort

    async def run(self, child_results: List[AgentResult]) -> ParentResult:
        prompt_key = {
            AgentKind.COUNCIL_PARENT.value: "council_parent",
            AgentKind.RESEARCH_PARENT.value: "research_parent",
            AgentKind.SECURITY_PARENT.value: "security_parent",
        }.get(self.agent_kind, "council_parent")
        system_prompt = prompt_for(prompt_key)
        compressed_children = [self._child_summary(child) for child in child_results]
        payload = {
            "parent_role": self.parent_role,
            "parent_group": self.parent_group,
            "child_results": compressed_children,
            "merge_policy": {
                "dedupe": True,
                "max_compressed_findings": 12,
                "preserve_material_disagreements": True,
                "drop_verbose_reasoning": True,
            },
        }
        input_tokens = estimate_tokens(system_prompt) + estimate_tokens(payload)
        if input_tokens > self.input_budget:
            # Deterministic pre-compression before invoking the model/mock.
            payload["child_results"] = compressed_children[: max(1, int(len(compressed_children) / 2))]
            input_tokens = estimate_tokens(system_prompt) + estimate_tokens(payload)
        data = await asyncio.to_thread(
            self.llm_client.generate_json,
            model=self.model,
            system_prompt=system_prompt,
            user_payload=payload,
            schema_name="parent_result",
            max_output_tokens=self.output_budget,
            reasoning_effort=self.reasoning_effort,
        )
        findings = [finding_from_dict(item) for item in data.get("compressed_findings", [])]
        recommended = unique_preserve_order(str(x) for x in data.get("recommended_actions", []))
        token_summary = {
            "child_input_tokens": sum(r.input_tokens_estimate for r in child_results),
            "child_output_tokens": sum(r.output_tokens_estimate for r in child_results),
            "parent_input_tokens": input_tokens,
            "parent_output_tokens": estimate_tokens(data),
        }
        return ParentResult(
            parent_id=self.parent_id,
            parent_role=self.parent_role,
            parent_group=self.parent_group,
            compressed_findings=findings,
            material_disagreements=[str(x) for x in data.get("material_disagreements", [])],
            duplicate_findings_removed=int(data.get("duplicate_findings_removed", 0)),
            confidence=str(data.get("confidence", "medium")),
            recommended_actions=recommended,
            token_summary=token_summary,
        )

    @staticmethod
    def _child_summary(child: AgentResult) -> Dict[str, Any]:
        return {
            "agent_id": child.agent_id,
            "agent_role": child.agent_role,
            "focus_area": child.focus_area,
            "findings": [to_dict(f) for f in child.findings[:4]],
            "issues": [to_dict(i) for i in child.issues[:4]],
            "confidence": child.confidence,
            "open_questions": child.open_questions[:3],
        }
