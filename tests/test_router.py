import unittest

from context_optimized_agents.budgets import BudgetAllocator
from context_optimized_agents.memory import LayeredMemory
from context_optimized_agents.router import ContextRouter
from context_optimized_agents.utils import estimate_tokens
from context_optimized_agents.schemas import to_dict


class RouterTests(unittest.TestCase):
    def test_routes_35_subagents_with_scoped_packets(self):
        router = ContextRouter(default_model="gpt-5.5")
        plan = router.make_task_plan("Build a Python project for context optimized agents")
        packets = router.route(plan, LayeredMemory.seeded_defaults(), BudgetAllocator())
        self.assertEqual(len(packets), 35)
        self.assertTrue(all(packet.model == "gpt-5.5" for packet in packets))
        self.assertTrue(all(packet.forbidden_context for packet in packets))
        self.assertTrue(any(packet.parent_group == "security_review" for packet in packets))
        self.assertTrue(any(packet.parent_group == "deep_research" for packet in packets))

    def test_packets_are_within_reasonable_budget_before_audit(self):
        router = ContextRouter(default_model="gpt-5.5")
        plan = router.make_task_plan("Research security and implementation risks")
        packets = router.route(plan, LayeredMemory.seeded_defaults(), BudgetAllocator())
        # Router should produce packets near or below budgets before auditor runs.
        over = [p.agent_id for p in packets if estimate_tokens(to_dict(p)) > p.budget.input_tokens * 1.25]
        self.assertEqual(over, [])


if __name__ == "__main__":
    unittest.main()
