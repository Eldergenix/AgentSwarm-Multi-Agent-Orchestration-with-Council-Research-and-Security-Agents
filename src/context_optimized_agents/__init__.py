"""Context-optimized multi-agent orchestration package."""

from .orchestrator import OrchestrationAgent
from .schemas import WorkflowResult

__all__ = ["OrchestrationAgent", "WorkflowResult"]
__version__ = "0.1.0"
