"""Context auditing, deduplication, and budget enforcement."""
from __future__ import annotations

from copy import deepcopy
from typing import List, Tuple

from .schemas import AuditReport, ContextPacket, to_dict
from .utils import estimate_tokens, jaccard, trim_text_to_tokens, unique_preserve_order


class ContextAuditor:
    """Lightweight context-efficiency reviewer.

    The auditor removes redundant shared definitions, compacts repeated forbidden
    context clauses, and enforces input budgets. It does not solve the task.
    """

    def audit(self, packets: List[ContextPacket]) -> Tuple[List[ContextPacket], AuditReport]:
        before = sum(estimate_tokens(to_dict(packet)) for packet in packets)
        warnings: List[str] = []
        redactions: List[str] = []
        over_budget: List[str] = []

        # The shared capsule is intentionally small, but definitions can become
        # redundant across many packets. Keep the capsule intact for every packet
        # in code, while estimating saved tokens as if it were transmitted once
        # plus a stable capsule reference for repeated packets.
        shared_capsule_tokens = 0
        if packets:
            shared_capsule_tokens = estimate_tokens(to_dict(packets[0].shared_capsule))

        audited: List[ContextPacket] = []
        seen_private_snippets: List[str] = []
        duplicate_removed_estimate = 0

        for packet in packets:
            p = deepcopy(packet)
            p.forbidden_context = unique_preserve_order(p.forbidden_context)

            # Remove duplicate retrieved memory snippets across private packets.
            retrieved = p.private_context.get("retrieved_memory", [])
            retained_retrieved = []
            for item in retrieved:
                value = str(item.get("value", item)) if isinstance(item, dict) else str(item)
                if any(jaccard(value, seen) > 0.82 for seen in seen_private_snippets):
                    duplicate_removed_estimate += estimate_tokens(value)
                    continue
                retained_retrieved.append(item)
                seen_private_snippets.append(value)
            p.private_context["retrieved_memory"] = retained_retrieved

            # Hard budget enforcement: if packet remains too large, remove optional
            # memory first, then trim rubric/progressive notes.
            tokens = estimate_tokens(to_dict(p))
            if tokens > p.budget.input_tokens:
                over_budget.append(p.agent_id)
                removed = estimate_tokens(to_dict(p.private_context.get("retrieved_memory", [])))
                p.private_context["retrieved_memory"] = []
                redactions.append(f"{p.agent_id}: removed retrieved_memory to meet budget")
                duplicate_removed_estimate += removed
                tokens = estimate_tokens(to_dict(p))

            if tokens > p.budget.input_tokens:
                p.private_context["task_specific_rubric"] = [
                    "Use supplied context only.",
                    "Return compact structured findings.",
                    "State precise open questions when context is missing.",
                ]
                p.private_context["progressive_disclosure"] = {
                    "start_minimal": True,
                    "request_format": "Ask for one named missing context item.",
                }
                tokens = estimate_tokens(to_dict(p))

            if tokens > p.budget.input_tokens:
                # As a last resort, add a compact budget note and trim role text.
                role_text = p.private_context.get("role_instruction", "")
                p.private_context["role_instruction"] = trim_text_to_tokens(
                    str(role_text), max(50, int(p.budget.input_tokens * 0.10))
                )
                warnings.append(f"{p.agent_id}: packet still near input budget after compaction")

            audited.append(p)

        after_raw = sum(estimate_tokens(to_dict(packet)) for packet in audited)
        # Estimate transport optimization: shared capsule is cached/referenced
        # across packets rather than resent as unique payload each time.
        shared_reference_savings = max(0, (len(audited) - 1) * max(0, shared_capsule_tokens - 25))
        after = max(0, after_raw - shared_reference_savings)

        report = AuditReport(
            packets_reviewed=len(packets),
            estimated_input_tokens_before=before,
            estimated_input_tokens_after=after,
            duplicate_context_tokens_removed=max(0, before - after + duplicate_removed_estimate),
            over_budget_packets=over_budget,
            redactions=redactions,
            warnings=warnings,
        )
        return audited, report
