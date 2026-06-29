"""models — the LLM provider layer / Model Router.

Agents never call a provider SDK directly (ADR-0003). They call a
``ModelRouter`` which maps an ``AgentRole`` to a configured model on a
``LLMProvider``. Swapping Ollama for OpenAI/Claude/Gemini later means adding a
provider class — no agent code changes.
"""

from models.base import CompletionRequest, CompletionResponse, LLMProvider, Message
from models.echo import EchoProvider
from models.ollama import OllamaProvider
from models.openai_provider import OpenAIProvider
from models.router import ModelRouter

__all__ = [
    "CompletionRequest",
    "CompletionResponse",
    "EchoProvider",
    "LLMProvider",
    "Message",
    "ModelRouter",
    "OllamaProvider",
    "OpenAIProvider",
]
