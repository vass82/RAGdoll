"""Chat model factory for the configured LLM provider."""

from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.core.config import LLMProvider, Settings


def create_chat_model(settings: Settings) -> BaseChatModel:
    """Create the chat model selected by ``settings.llm_provider``.

    :param settings: Application settings describing the provider and its options.
    :type settings: Settings
    :returns: A LangChain chat model ready to be injected into the RAG graph.
    :rtype: BaseChatModel
    :raises ValueError: If the provider is OpenAI and no API key is configured,
        or if the provider is not supported.
    """
    if settings.llm_provider is LLMProvider.OPENAI:
        return _create_openai_chat_model(settings)
    if settings.llm_provider is LLMProvider.OLLAMA:
        return _create_ollama_chat_model(settings)
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider!r}.")


def _create_openai_chat_model(settings: Settings) -> ChatOpenAI:
    """Create an OpenAI chat model.

    :param settings: Application settings containing the OpenAI API key and model.
    :type settings: Settings
    :returns: A configured ``ChatOpenAI`` instance.
    :rtype: ChatOpenAI
    :raises ValueError: If ``OPENAI_API_KEY`` is not set.
    """
    if (
        settings.openai_api_key is None
        or not settings.openai_api_key.get_secret_value()
    ):
        raise ValueError(
            "LLM_PROVIDER is 'openai' but OPENAI_API_KEY is not set. "
            "Set OPENAI_API_KEY or use LLM_PROVIDER=ollama."
        )
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
    )


def _create_ollama_chat_model(settings: Settings) -> ChatOllama:
    """Create a chat model served by a local Ollama instance.

    :param settings: Application settings containing the Ollama URL and model.
    :type settings: Settings
    :returns: A configured ``ChatOllama`` instance.
    :rtype: ChatOllama
    """
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
    )
