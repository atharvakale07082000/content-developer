"""
BaseAgent — abstract contract every sub-agent must satisfy.
"""
from abc import ABC, abstractmethod
from agent.protocol import AgentTask, AgentResult


class BaseAgent(ABC):
    agent_id: str
    capabilities: list[str]
    model: str | None = None

    @abstractmethod
    def run(self, task: AgentTask) -> AgentResult: ...

    def can_handle(self, task_type: str) -> bool:
        return task_type in self.capabilities
