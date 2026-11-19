"""Integration test: retrieval over the indexed knowledge base in the RAG graph.

Uses deterministic local embeddings and a fake chat model, so no API keys,
external services, or model downloads are needed.
"""

from pathlib import Path

from langchain_core.embeddings.fake import DeterministicFakeEmbedding
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from app.core.config import Settings
from app.rag.graph import build_rag_graph
from app.services.knowledge_base import build_knowledge_base


def test_question_is_answered_from_indexed_nested_document(tmp_path: Path) -> None:
    (tmp_path / "overview.md").write_text("RAGdoll uses FastAPI.", encoding="utf-8")
    (tmp_path / "guides").mkdir()
    (tmp_path / "guides" / "formats.md").write_text(
        "Solver output is written to .pos files.", encoding="utf-8"
    )
    settings = Settings(_env_file=None, documents_dir=tmp_path, chunk_size=1000)
    store = build_knowledge_base(settings, DeterministicFakeEmbedding(size=32))
    chat_model = GenericFakeChatModel(messages=iter([AIMessage(".pos files.")]))
    graph = build_rag_graph(store.as_retriever(search_kwargs={"k": 1}), chat_model)

    result = graph.invoke({"question": "Solver output is written to .pos files."})

    assert result["answer"] == ".pos files."
    assert [doc.metadata["relative_path"] for doc in result["documents"]] == [
        "guides/formats.md"
    ]
