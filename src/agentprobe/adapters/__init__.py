"""Framework adapters for LangChain, CrewAI, AutoGen, MCP, and others."""

from agentprobe.adapters.base import BaseAdapter
from agentprobe.adapters.langchain import LangChainAdapter

__all__ = ["BaseAdapter", "LangChainAdapter"]
