"""
bench.py - Script chạy đánh giá truy xuất (Benchmark Retrieval) cho K4-L3B
Chủ đề: Chính sách Thương mại Điện tử (Shopee, TikTok Shop, MediaMart)

Thực hiện:
1. Đọc toàn bộ tài liệu Markdown trong data/ecommerce/
2. Tách metadata YAML frontmatter và phân đoạn nội dung (chunking)
3. Nạp các Document chunks vào EmbeddingStore
4. Chạy 5 câu hỏi đánh giá (Benchmark Queries), thực hiện kiểm thử A/B filter
5. Xuất kết quả chi tiết ra màn hình và lưu vào ket_qua_benchmark.txt
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

from src.agent import KnowledgeBaseAgent
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import LocalEmbedder, MockEmbedder, _mock_embed
from src.models import Document
from src.store import EmbeddingStore


class CustomHeadingChunker:
    """
    Chiến lược chia nhỏ theo tiêu đề/mục (Heading/Section-based Chunker).
    Được thiết kế riêng cho văn bản điều khoản chính sách TMĐT.
    Tách theo các tiêu đề (#, ##, Điều...) và gắn breadcrumb vào từng chunk.
    """

    def __init__(self, max_chunk_size: int = 400) -> None:
        self.max_chunk_size = max_chunk_size
        self.fallback = RecursiveChunker(chunk_size=max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        # Tách theo các dòng tiêu đề markdown (#, ##, ###)
        sections = re.split(r'(?m)(?=^#{1,3}\s+)', text.strip())
        chunks: list[str] = []

        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue

            # Nếu section vừa vặn
            if len(sec) <= self.max_chunk_size:
                chunks.append(sec)
            else:
                # Nếu section quá dài, lấy tiêu đề gắn prefix cho các mảnh nhỏ
                first_line = sec.splitlines()[0]
                sub_chunks = self.fallback.chunk(sec)
                for sub in sub_chunks:
                    if sub.startswith("#"):
                        chunks.append(sub)
                    else:
                        chunks.append(f"[{first_line}]\n{sub}")

        return chunks if chunks else [text]


# Định nghĩa 5 câu hỏi đánh giá chuẩn của nhóm K4-L3B
BENCHMARK_QUERIES = [
    {
        "query": "Người mua Shopee phải gửi yêu cầu trả hàng hoặc hoàn tiền trong bao lâu sau khi giao hàng thành công?",
        "gold": "Đơn thông thường: 15 ngày; thực phẩm tươi sống và đông lạnh: 24 giờ kể từ khi giao thành công.",
        "expected_doc_id": "shopee-return-refund-policy",
        "metadata_filter": None,
    },
    {
        "query": "MediaMart cho đổi sản phẩm chưa qua sử dụng trong thời hạn nào theo từng nhóm sản phẩm?",
        "gold": "Điện tử/điện lạnh/gia dụng: 3 ngày; điện thoại và máy tính bảng: 15 ngày; laptop, máy ảnh, máy quay: 2 ngày; phụ kiện đủ điều kiện: 30 ngày, kèm các ngoại lệ nêu trong chính sách.",
        "expected_doc_id": "mediamart-doitra-buyer",
        "metadata_filter": None,
    },
    {
        "query": "Cần làm gì khi nhận được yêu cầu trả hàng và hoàn tiền?",
        "gold": "Người bán vào Trung tâm nhà bán hàng > Đơn hàng > Quản lý yêu cầu trả hàng, mở tab Đang chờ hành động và lọc Trả hàng và hoàn tiền; yêu cầu thủ công phải được duyệt hoặc từ chối trong 1 ngày dương lịch, và hàng trả phải được kiểm tra trong 2 ngày dương lịch.",
        "expected_doc_id": "tiktok-manage-return-refund",
        "metadata_filter": {"audience": "seller"},
    },
    {
        "query": "MediaMart hỗ trợ những phương thức thanh toán nào?",
        "gold": "Thanh toán tiền mặt; thanh toán trước bằng chuyển tiền/chuyển khoản, tiền mặt hoặc thẻ tại văn phòng; và thanh toán trực tuyến bằng thẻ quốc tế, thẻ nội địa hoặc dịch vụ thanh toán điện tử.",
        "expected_doc_id": "mediamart-thanhtoan-buyer",
        "metadata_filter": None,
    },
    {
        "query": "Hãy liệt kê các thời hạn khiếu nại và xử lý khiếu nại vận chuyển của Shopee.",
        "gold": "Thất lạc khi chuyển hoàn: 7 ngày; hàng hư hại/không nguyên vẹn: 3 ngày; khiếu nại sai phí: 7 ngày; cung cấp bằng chứng: 24 giờ; Shopee xử lý tối đa 10 ngày làm việc sau khi nhận đủ bằng chứng hợp lệ.",
        "expected_doc_id": "shopee-shipping-policy",
        "metadata_filter": None,
    },
]


def parse_markdown_file(path: Path) -> tuple[dict, str]:
    """Tách YAML Frontmatter và phần thân nội dung của file .md."""
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2].strip()
            metadata = {}
            for line in fm_text.splitlines():
                m = re.match(r'^(\w+):\s*["\']?([^"\'\r\n#]+)["\']?', line.strip())
                if m:
                    metadata[m.group(1)] = m.group(2).strip()
            return metadata, body
    return {}, text.strip()


def get_chunker(strategy_name: str):
    """Lựa chọn chiến lược phân đoạn."""
    if strategy_name == "heading":
        return CustomHeadingChunker(max_chunk_size=350)
    elif strategy_name == "fixed":
        return FixedSizeChunker(chunk_size=350, overlap=50)
    elif strategy_name == "sentence":
        return SentenceChunker(max_sentences_per_chunk=3)
    else:  # default recursive
        return RecursiveChunker(chunk_size=350)


def get_embedder():
    """Khởi tạo embedding backend (ưu tiên LocalEmbedder nếu có)."""
    load_dotenv(override=False)
    try:
        embedder = LocalEmbedder()
        backend_name = getattr(embedder, "_backend_name", "LocalEmbedder")
        return embedder, backend_name
    except Exception as e:
        return _mock_embed, f"MockEmbedder (fallback: {e})"


def run_benchmark(strategy: str = "heading", output_file: str = "ket_qua_benchmark.txt") -> None:
    data_dir = Path("data/ecommerce")
    md_files = sorted(data_dir.glob("*.md"))

    if not md_files:
        print(f"Không tìm thấy file .md nào trong {data_dir}!")
        return

    chunker = get_chunker(strategy)
    embedder, backend_name = get_embedder()

    lines = []
    lines.append("================================================================================")
    lines.append("K4-L3B: KẾT QUẢ ĐÁNH GIÁ TRUY XUẤT (RETRIEVAL BENCHMARK REPORT)")
    lines.append(f"Chiến lược Chunking : {strategy.upper()} ({chunker.__class__.__name__})")
    lines.append(f"Mô hình Embedding   : {backend_name}")
    lines.append(f"Tập tài liệu        : {len(md_files)} văn bản trong data/ecommerce/")
    lines.append("================================================================================\n")

    # 1. Ingest Documents
    store = EmbeddingStore(collection_name="benchmark_store", embedding_fn=embedder)
    all_chunks: list[Document] = []

    for path in md_files:
        fm, body = parse_markdown_file(path)
        doc_id = fm.get("doc_id", path.stem)
        chunks_text = chunker.chunk(body)

        for idx, c_text in enumerate(chunks_text):
            chunk_doc = Document(
                id=f"{doc_id}#{idx}",
                content=c_text,
                metadata={
                    **fm,
                    "doc_id": doc_id,
                    "chunk_index": idx,
                    "source_file": path.name,
                }
            )
            all_chunks.append(chunk_doc)

    store.add_documents(all_chunks)
    lines.append(f"-> Đã tạo và nạp thành công {len(all_chunks)} chunks vào Vector Store.\n")

    # 2. Run Benchmark Queries
    lines.append("--------------------------------------------------------------------------------")
    lines.append("CHI TIẾT 5 CÂU HỎI BENCHMARK:")
    lines.append("--------------------------------------------------------------------------------")

    agent = KnowledgeBaseAgent(store=store, llm_fn=lambda prompt: "[LLM Answer Generated from Context]")

    for idx, q in enumerate(BENCHMARK_QUERIES, start=1):
        q_id = q.get("id", idx)
        query = q["query"]
        q_filter = q.get("metadata_filter", q.get("filter"))
        gold = q.get("gold", q.get("gold_answer", ""))
        target = q.get("expected_doc_id", q.get("target_doc", ""))

        results = store.search_with_filter(query, top_k=3, metadata_filter=q_filter)

        lines.append(f"\n[CÂU {q_id}] {query}")
        lines.append(f"  * Bộ lọc (Filter) : {q_filter}")
        lines.append(f"  * Đáp án chuẩn    : {gold}")
        lines.append(f"  * Tài liệu đích   : {target}")

        for rank, r in enumerate(results, start=1):
            r_doc_id = r["metadata"].get("doc_id")
            score = r["score"]
            preview = r["content"][:100].replace("\n", " ")
            lines.append(f"    - Top-{rank} [score={score:.4f}] doc_id={r_doc_id} | content: {preview}...")

    # 3. A/B Test Filter
    lines.append("\n--------------------------------------------------------------------------------")
    lines.append("THỬ NGHIỆM A/B FILTER (CÓ FILTER vs KHÔNG FILTER)")
    lines.append("--------------------------------------------------------------------------------")
    filtered_q = next((item for item in BENCHMARK_QUERIES if item.get("metadata_filter") or item.get("filter")), BENCHMARK_QUERIES[0])
    ab_query = filtered_q["query"]
    ab_filter = filtered_q.get("metadata_filter", filtered_q.get("filter", {"audience": "seller"}))
    res_filtered = store.search_with_filter(ab_query, top_k=3, metadata_filter=ab_filter)
    res_unfiltered = store.search_with_filter(ab_query, top_k=3, metadata_filter=None)

    lines.append(f"Query: \"{ab_query}\"")
    lines.append(f"1. Khi CÓ filter {ab_filter}:")
    for r in res_filtered:
        lines.append(f"   * [score={r['score']:.4f}] doc_id={r['metadata'].get('doc_id')} (audience={r['metadata'].get('audience')})")

    lines.append("2. Khi KHÔNG CÓ filter (None):")
    for r in res_unfiltered:
        lines.append(f"   * [score={r['score']:.4f}] doc_id={r['metadata'].get('doc_id')} (audience={r['metadata'].get('audience')})")

    output_text = "\n".join(lines)
    print(output_text)

    # Ghi ra file kết quả
    Path(output_file).write_text(output_text, encoding="utf-8")
    print(f"\n[OK] Đã lưu toàn bộ kết quả benchmark vào file: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Chạy benchmark retrieval K4-L3B")
    parser.add_argument(
        "--strategy",
        choices=["heading", "recursive", "fixed", "sentence"],
        default="heading",
        help="Chiến lược chunking (mặc định: heading)",
    )
    parser.add_argument(
        "--output",
        default="ket_qua_benchmark.txt",
        help="File lưu kết quả (mặc định: ket_qua_benchmark.txt)",
    )
    args = parser.parse_args()
    run_benchmark(strategy=args.strategy, output_file=args.output)


if __name__ == "__main__":
    main()
