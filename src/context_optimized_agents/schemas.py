"""Dataclasses and JSON Schemas for the context-optimized agent workflow.

The runtime intentionally uses standard-library dataclasses rather than Pydantic so
that the default offline mode is install-free. Live OpenAI mode still sends strict
JSON schemas to the Responses API.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from typing import Any, Dict, List, Mapping


class TaskType(str, Enum):
    RESEARCH = "research"
    SECURITY = "security"
    COUNCIL_REVIEW = "council_review"
    IMPLEMENTATION = "implementation"
    MEMORY = "memory"
    GENERAL_SYNTHESIS = "general_synthesis"


class AgentKind(str, Enum):
    ORCHESTRATION = "orchestration"
    CONTEXT_ROUTER = "context_router"
    BUDGET_ALLOCATOR = "budget_allocator"
    CONTEXT_AUDITOR = "context_auditor"
    DIRECT_SUBAGENT = "direct_subagent"
    COUNCIL_SUBAGENT = "council_subagent"
    COUNCIL_PARENT = "council_parent"
    RESEARCH_SUBAGENT = "research_subagent"
    RESEARCH_PARENT = "research_parent"
    SECURITY_SUBAGENT = "security_subagent"
    SECURITY_PARENT = "security_parent"
    FINAL_SYNTHESIS = "final_synthesis"


class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class AgentBudget:
    input_tokens: int
    output_tokens: int


@dataclass
class TaskPlan:
    objective: str
    task_type: str
    constraints: List[str]
    required_output: str
    acceptance_criteria: List[str]
    risk_policy: List[str]
    max_parallel_agents: int = 12


@dataclass
class SharedTaskCapsule:
    objective: str
    task_type: str
    constraints: List[str]
    definitions: Dict[str, str]
    output_schema_name: str
    acceptance_criteria: List[str]


@dataclass
class ContextPacket:
    agent_id: str
    agent_kind: str
    agent_role: str
    parent_group: str
    focus_area: str
    model: str
    reasoning_effort: str
    budget: AgentBudget
    shared_capsule: SharedTaskCapsule
    private_context: Dict[str, Any]
    forbidden_context: List[str]
    retrieval_policy: Dict[str, Any]
    output_schema: str


@dataclass
class Finding:
    claim: str
    evidence: List[str]
    confidence: str
    risk: str
    recommended_action: str


@dataclass
class IssueFinding:
    issue: str
    severity: str
    evidence: str
    recommendation: str


@dataclass
class AgentResult:
    agent_id: str
    agent_role: str
    agent_kind: str
    parent_group: str
    focus_area: str
    findings: List[Finding]
    issues: List[IssueFinding]
    confidence: str
    open_questions: List[str]
    input_tokens_estimate: int
    output_tokens_estimate: int
    budget_compliance: Dict[str, bool]


@dataclass
class ParentResult:
    parent_id: str
    parent_role: str
    parent_group: str
    compressed_findings: List[Finding]
    material_disagreements: List[str]
    duplicate_findings_removed: int
    confidence: str
    recommended_actions: List[str]
    token_summary: Dict[str, int]


@dataclass
class AuditReport:
    packets_reviewed: int
    estimated_input_tokens_before: int
    estimated_input_tokens_after: int
    duplicate_context_tokens_removed: int
    over_budget_packets: List[str]
    redactions: List[str]
    warnings: List[str]


@dataclass
class MetricRow:
    metric: str
    brute_force: float
    optimized: float
    unit: str
    improvement_pct: float
    note: str


@dataclass
class WorkflowMetrics:
    rows: List[MetricRow]
    assumptions: Dict[str, Any]


@dataclass
class FinalSynthesis:
    final_answer: str
    key_assumptions: List[str]
    verified_evidence: List[str]
    open_risks: List[str]
    next_actions: List[str]
    quality_score: float
    hallucination_exposure_score: float


@dataclass
class WorkflowResult:
    task_plan: TaskPlan
    audit_report: AuditReport
    agent_results: List[AgentResult]
    parent_results: List[ParentResult]
    final_synthesis: FinalSynthesis
    metrics: WorkflowMetrics
    decision_memory_record: Dict[str, Any]


def to_dict(obj: Any) -> Any:
    """Recursively convert dataclasses, enums, and containers to JSON-safe objects."""
    if isinstance(obj, Enum):
        return obj.value
    if is_dataclass(obj):
        return {k: to_dict(v) for k, v in asdict(obj).items()}
    if isinstance(obj, Mapping):
        return {str(k): to_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [to_dict(v) for v in obj]
    return obj


def finding_from_dict(data: Mapping[str, Any]) -> Finding:
    return Finding(
        claim=str(data.get("claim", "")),
        evidence=[str(x) for x in data.get("evidence", [])],
        confidence=str(data.get("confidence", Confidence.MEDIUM.value)),
        risk=str(data.get("risk", "")),
        recommended_action=str(data.get("recommended_action", "")),
    )


def issue_from_dict(data: Mapping[str, Any]) -> IssueFinding:
    return IssueFinding(
        issue=str(data.get("issue", "")),
        severity=str(data.get("severity", Severity.MEDIUM.value)),
        evidence=str(data.get("evidence", "")),
        recommendation=str(data.get("recommendation", "")),
    )


def agent_result_from_dict(
    data: Mapping[str, Any], packet: ContextPacket, input_tokens: int, output_tokens: int
) -> AgentResult:
    findings = [finding_from_dict(item) for item in data.get("findings", [])]
    issues = [issue_from_dict(item) for item in data.get("issues", [])]
    return AgentResult(
        agent_id=packet.agent_id,
        agent_role=str(data.get("agent_role", packet.agent_role)),
        agent_kind=packet.agent_kind,
        parent_group=packet.parent_group,
        focus_area=str(data.get("focus_area", packet.focus_area)),
        findings=findings,
        issues=issues,
        confidence=str(data.get("confidence", Confidence.MEDIUM.value)),
        open_questions=[str(x) for x in data.get("open_questions", [])],
        input_tokens_estimate=input_tokens,
        output_tokens_estimate=output_tokens,
        budget_compliance={
            "input": input_tokens <= packet.budget.input_tokens,
            "output": output_tokens <= packet.budget.output_tokens,
        },
    )


FINDING_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "claim": {"type": "string"},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
        "risk": {"type": "string"},
        "recommended_action": {"type": "string"},
    },
    "required": ["claim", "evidence", "confidence", "risk", "recommended_action"],
    "additionalProperties": False,
}

ISSUE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "issue": {"type": "string"},
        "severity": {
            "type": "string",
            "enum": ["info", "low", "medium", "high", "critical"],
        },
        "evidence": {"type": "string"},
        "recommendation": {"type": "string"},
    },
    "required": ["issue", "severity", "evidence", "recommendation"],
    "additionalProperties": False,
}

AGENT_RESULT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "agent_role": {"type": "string"},
        "focus_area": {"type": "string"},
        "findings": {"type": "array", "items": FINDING_SCHEMA, "minItems": 1, "maxItems": 10},
        "issues": {"type": "array", "items": ISSUE_SCHEMA, "maxItems": 10},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
        "open_questions": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
    },
    "required": ["agent_role", "focus_area", "findings", "issues", "confidence", "open_questions"],
    "additionalProperties": False,
}

PARENT_RESULT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "compressed_findings": {
            "type": "array",
            "items": FINDING_SCHEMA,
            "minItems": 3,
            "maxItems": 15,
        },
        "material_disagreements": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
        "duplicate_findings_removed": {"type": "integer", "minimum": 0},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
        "recommended_actions": {"type": "array", "items": {"type": "string"}, "maxItems": 10},
    },
    "required": [
        "compressed_findings",
        "material_disagreements",
        "duplicate_findings_removed",
        "confidence",
        "recommended_actions",
    ],
    "additionalProperties": False,
}

FINAL_SYNTHESIS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "final_answer": {"type": "string"},
        "key_assumptions": {"type": "array", "items": {"type": "string"}, "maxItems": 10},
        "verified_evidence": {"type": "array", "items": {"type": "string"}, "maxItems": 12},
        "open_risks": {"type": "array", "items": {"type": "string"}, "maxItems": 10},
        "next_actions": {"type": "array", "items": {"type": "string"}, "maxItems": 10},
        "quality_score": {"type": "number", "minimum": 0, "maximum": 1},
        "hallucination_exposure_score": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": [
        "final_answer",
        "key_assumptions",
        "verified_evidence",
        "open_risks",
        "next_actions",
        "quality_score",
        "hallucination_exposure_score",
    ],
    "additionalProperties": False,
}


def schema_for_name(name: str) -> Dict[str, Any]:
    mapping = {
        "agent_result": AGENT_RESULT_SCHEMA,
        "parent_result": PARENT_RESULT_SCHEMA,
        "final_synthesis": FINAL_SYNTHESIS_SCHEMA,
    }
    try:
        return mapping[name]
    except KeyError as exc:
        raise ValueError(f"Unknown schema name: {name}") from exc
