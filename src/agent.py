from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy thông tin phù hợp trong cơ sở tri thức."

        context_items = []
        for i, r in enumerate(results, start=1):
            source = r.get("metadata", {}).get("source", r.get("metadata", {}).get("doc_id", r.get("id", "Unknown")))
            context_items.append(f"[{i}] (Nguồn: {source})\n{r['content']}")

        context_str = "\n\n".join(context_items)
        prompt = (
            f"Bạn là một trợ lý thông minh. Dưới đây là ngữ cảnh từ cơ sở tri thức:\n\n"
            f"{context_str}\n\n"
            f"Dựa trên các thông tin được đánh số ở trên, hãy trả lời câu hỏi sau và trích dẫn rõ nguồn:\n"
            f"Câu hỏi: {question}\n"
            f"Trả lời:"
        )
        return self.llm_fn(prompt)
