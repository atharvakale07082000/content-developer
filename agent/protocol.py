"""
A2A message protocol — shared dataclasses for inter-agent communication.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentTask:
    task_id: str
    task_type: str      # e.g. "fetch_content", "analyse", "suggest", "draft_linkedin"
    payload: dict
    metadata: dict = field(default_factory=dict)


@dataclass
class AgentResult:
    task_id: str
    agent_id: str
    success: bool
    output: Any
    error: str | None = None
    metadata: dict = field(default_factory=dict)
