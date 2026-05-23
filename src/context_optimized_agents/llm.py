"""LLM client abstraction with deterministic offline and OpenAI live implementations."""
from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Mapping

from .schemas import schema_for_name
from .utils import stable_hash


class LLMClient(ABC):
    @abstractmethod
    def generate_json(
        self,
        *,
        model: str,
        system_prompt: str,
        user_payload: Mapping[str, Any],
        schema_name: str,
        max_output_tokens: int,
        reasoning_effort: str = "medium",
    ) -> Dict[str, Any]:
        """Return JSON-conformant data for the requested schema."""


class MockLLMClient(LLMClient):
    """Deterministic local implementation used for tests and no-key demos."""

    def generate_json(
        self,
        *,
        model: str,
        system_prompt: str,
        user_payload: Mapping[str, Any],
        schema_name: str,
        max_output_tokens: int,
        reasoning_effort: str = "medium",
    ) -> Dict[str, Any]:
        if schema_name == "agent_result":
            return self._agent_result(user_payload)
        if schema_name == "parent_result":
            return self._parent_result(user_payload)
        if schema_name == "final_synthesis":
            return self._final_synthesis(user_payload)
        raise ValueError(f"Unsupported schema for mock client: {schema_name}")

    def _agent_result(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        packet = payload.get("packet", payload)
        role = str(packet.get("agent_role", "Specialized Agent"))
        focus = str(packet.get("focus_area", "General focus"))
        kind = str(packet.get("agent_kind", "direct_subagent"))
        objective = str(packet.get("shared_capsule", {}).get("objective", "the task"))
        seed = stable_hash(role + focus + objective, 6)

        findings = [
            {
                "claim": f"Scoped context improves {focus.lower()} by limiting each agent to role-relevant evidence.",
                "evidence": [
                    "Packet contains shared_capsule plus private_context rather than full conversation or corpus.",
                    f"Agent kind {kind} receives a strict input/output budget.",
                ],
                "confidence": "high",
                "risk": "Overly narrow routing can hide cross-domain dependencies.",
                "recommended_action": "Use progressive disclosure and explicit open_questions when missing context is detected.",
            },
            {
                "claim": "Structured findings reduce synthesis overhead and make deduplication tractable.",
                "evidence": [
                    "Output schema requires claim, evidence, confidence, risk, and recommended_action fields.",
                    "Parent agents merge compact child findings rather than rereading verbose traces.",
                ],
                "confidence": "high",
                "risk": "Rigid schemas can omit nuance when an issue does not fit the schema.",
                "recommended_action": "Keep an open_questions field and allow severity-tagged issue findings.",
            },
            {
                "claim": f"The {focus.lower()} review should preserve evidence while removing repeated background context.",
                "evidence": [
                    f"Deterministic audit marker {seed} confirms role-specific routing was applied.",
                    "Forbidden context lists prevent accidental exposure of unrelated memory and hidden scratchpads.",
                ],
                "confidence": "medium",
                "risk": "Evidence may be compressed too aggressively for high-stakes decisions.",
                "recommended_action": "Attach evidence identifiers and permit targeted retrieval for contested claims.",
            },
        ]
        issues = []
        if "security" in kind or "risk" in focus.lower() or "injection" in focus.lower():
            issues.append(
                {
                    "issue": "Untrusted retrieved content can attempt to steer tool calls or override instructions.",
                    "severity": "high",
                    "evidence": "The architecture uses retrieval memory and research agents that may ingest external text.",
                    "recommendation": "Sandbox retrieved content as data, separate it from system instructions, and require explicit tool-call authorization.",
                }
            )
        if "memory" in focus.lower():
            issues.append(
                {
                    "issue": "Memory overexposure can leak irrelevant user or project facts into unrelated agents.",
                    "severity": "medium",
                    "evidence": "Memory is split into session, project, user, working, retrieval, and decision layers.",
                    "recommendation": "Use allow-listed memory layers per role and deny-by-default retrieval policies.",
                }
            )

        return {
            "agent_role": role,
            "focus_area": focus,
            "findings": findings,
            "issues": issues,
            "confidence": "high" if issues == [] or all(i["severity"] != "critical" for i in issues) else "medium",
            "open_questions": [],
        }

    def _parent_result(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        parent_role = str(payload.get("parent_role", "Parent Agent"))
        group = str(payload.get("parent_group", "group"))
        child_results = payload.get("child_results", [])
        compressed = []
        seen = set()
        duplicates = 0
        for child in child_results:
            for finding in child.get("findings", []):
                claim = str(finding.get("claim", ""))
                key = " ".join(claim.lower().split()[:10])
                if key in seen:
                    duplicates += 1
                    continue
                seen.add(key)
                compressed.append(finding)
                if len(compressed) >= 10:
                    break
            if len(compressed) >= 10:
                break
        if len(compressed) < 3:
            compressed.append(
                {
                    "claim": f"{parent_role} found the optimized context path suitable for {group} synthesis.",
                    "evidence": ["Child outputs were structured and mergeable."],
                    "confidence": "medium",
                    "risk": "Small child sample may underrepresent edge cases.",
                    "recommended_action": "Run additional evals on larger task classes.",
                }
            )
        actions = []
        for finding in compressed[:5]:
            action = finding.get("recommended_action")
            if action and action not in actions:
                actions.append(str(action))
        return {
            "compressed_findings": compressed[:12],
            "material_disagreements": [],
            "duplicate_findings_removed": duplicates,
            "confidence": "high",
            "recommended_actions": actions[:8],
        }

    def _final_synthesis(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        parent_results = payload.get("parent_results", [])
        evidence = []
        risks = []
        actions = []
        for parent in parent_results:
            for finding in parent.get("compressed_findings", []):
                evidence.extend(str(x) for x in finding.get("evidence", [])[:1])
                if finding.get("risk"):
                    risks.append(str(finding.get("risk")))
                if finding.get("recommended_action"):
                    actions.append(str(finding.get("recommended_action")))
            actions.extend(str(x) for x in parent.get("recommended_actions", []))

        evidence = list(dict.fromkeys(evidence))[:10]
        risks = list(dict.fromkeys(risks))[:8]
        actions = list(dict.fromkeys(actions))[:8]
        objective = str(payload.get("objective", "the submitted objective"))
        final_answer = (
            "The optimized workflow should be implemented as a scoped-context multi-agent system: "
            "an Orchestration Agent creates the task plan, a Context Router and Budget Allocator build "
            "minimal role-specific packets, specialized agents return compact structured findings, parent "
            "agents compress and deduplicate those findings, Council and Security reviews resolve quality and "
            "risk concerns, and the Final Synthesis Agent stores only decision-grade artifacts. "
            f"For this run, the objective was: {objective}"
        )
        return {
            "final_answer": final_answer,
            "key_assumptions": [
                "The representative workload uses 35 sub-agents plus parent review agents.",
                "Metrics are expected/simulated unless a live benchmark run is executed.",
                "All model-routed agents default to gpt-5.5.",
            ],
            "verified_evidence": evidence,
            "open_risks": risks,
            "next_actions": actions,
            "quality_score": 0.91,
            "hallucination_exposure_score": 0.18,
        }


class OpenAIResponsesClient(LLMClient):
    """OpenAI Responses API client.

    Uses strict JSON schema output through the `text.format` mechanism. The class
    is imported only in live mode so local/offline use has no OpenAI dependency.
    """

    def __init__(self, api_key: str | None = None, timeout: float | None = None) -> None:
        try:
            from openai import OpenAI  # type: ignore
        except Exception as exc:
            raise RuntimeError(
                "OpenAI live mode requires the optional dependency: pip install -e .[live]"
            ) from exc
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"), timeout=timeout)

    def generate_json(
        self,
        *,
        model: str,
        system_prompt: str,
        user_payload: Mapping[str, Any],
        schema_name: str,
        max_output_tokens: int,
        reasoning_effort: str = "medium",
    ) -> Dict[str, Any]:
        schema = schema_for_name(schema_name)
        text_format = {
            "type": "json_schema",
            "name": schema_name,
            "schema": schema,
            "strict": True,
        }
        response = self.client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            text={"format": text_format},
            max_output_tokens=max_output_tokens,
            reasoning={"effort": reasoning_effort},
        )
        # New SDKs expose output_text; parse helpers may expose output_parsed.
        parsed = getattr(response, "output_parsed", None)
        if parsed is not None:
            if hasattr(parsed, "model_dump"):
                return parsed.model_dump()
            if isinstance(parsed, Mapping):
                return dict(parsed)
        output_text = getattr(response, "output_text", None)
        if not output_text:
            raise RuntimeError("OpenAI response did not contain output_text for JSON parsing")
        return json.loads(output_text)


def client_from_mode(mode: str) -> LLMClient:
    if mode == "mock":
        return MockLLMClient()
    if mode == "live":
        return OpenAIResponsesClient()
    raise ValueError("mode must be 'mock' or 'live'")
