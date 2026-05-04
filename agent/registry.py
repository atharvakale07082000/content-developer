"""
AgentRegistry — maps task types to agent instances.
"""
from agent.base_agent import BaseAgent


class AgentRegistry:
    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}
        self._capability_map: dict[str, str] = {}   # task_type -> agent_id

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.agent_id] = agent
        for cap in agent.capabilities:
            self._capability_map[cap] = agent.agent_id

    def get_for_task(self, task_type: str) -> BaseAgent | None:
        agent_id = self._capability_map.get(task_type)
        return self._agents.get(agent_id) if agent_id else None

    def get_by_id(self, agent_id: str) -> BaseAgent | None:
        return self._agents.get(agent_id)

    def list_agents(self) -> list[dict]:
        return [
            {"agent_id": a.agent_id, "capabilities": a.capabilities, "model": a.model}
            for a in self._agents.values()
        ]
