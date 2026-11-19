"""Local embedding model factory based on Hugging Face / Sentence Transformers."""

from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import Settings


def create_embeddings(settings: Settings) -> Embeddings:
    """Create the local embedding model named in the settings.

    The model runs locally via Sentence Transformers and needs no API key.
    The first call may download the model weights from Hugging Face.

    :param settings: Application settings containing the embedding model name.
    :type settings: Settings
    :returns: A LangChain embeddings instance.
    :rtype: Embeddings
    """
    return HuggingFaceEmbeddings(model_name=settings.embedding_model)
