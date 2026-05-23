import unittest

from context_optimized_agents.orchestrator import OrchestrationAgent


class OrchestratorTests(unittest.TestCase):
    def test_mock_workflow_completes(self):
        objective = "Create a context optimized multi-agent workflow with budgets and security review."
        result = OrchestrationAgent(max_parallel_agents=8).run(objective)
        self.assertEqual(len(result.agent_results), 35)
        self.assertGreaterEqual(len(result.parent_results), 6)
        self.assertIn("scoped-context", result.final_synthesis.final_answer)
        self.assertGreater(result.final_synthesis.quality_score, 0.8)
        self.assertTrue(result.decision_memory_record["id"].startswith("decision-"))

    def test_metrics_include_cost(self):
        result = OrchestrationAgent(max_parallel_agents=8).run("Evaluate metrics for context routing")
        metric_names = [row.metric for row in result.metrics.rows]
        self.assertIn("Estimated GPT-5.5 token cost", metric_names)


if __name__ == "__main__":
    unittest.main()
