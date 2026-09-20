# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Dương Đình Long
**Nhóm:** Buddy
**Ngày:** 20/9/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Nghĩa là hai vector có hướng trong không gian rất giống nhau (góc giữa hai vector rất nhỏ, tiệm cận 0 độ), phản ánh rằng hai đoạn văn bản có nội dung và ý nghĩa tương đồng cao.

**Ví dụ có độ tương tự CAO:**
- Câu A: Đơn hàng của tôi bao giờ giao tới?
- Câu B: Khi nào tôi nhận được hàng?
- Tại sao tương đồng: Cả hai câu hỏi đều có cùng mục đích tra cứu về thời gian giao hàng thành công.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Tôi có thể đổi sang size khác được không?
- Câu B: Hãy cho tôi biết thông tin về sản phẩm.
- Tại sao khác: Câu A hỏi về chính sách đổi trả kích cỡ, còn Câu B yêu cầu mô tả thông tin sản phẩm, thuộc hai mục đích hội thoại hoàn toàn khác nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Trong text embeddings, ta quan tâm đến hướng ngữ nghĩa của nội dung thay vì độ dài tuyệt đối của văn bản. Khoảng cách Euclid bị ảnh hưởng bởi độ dài đoạn văn (vector dài hay ngắn), trong khi Cosine similarity chỉ đo góc giữa các vector sau khi chuẩn hóa, giúp so sánh chính xác ngữ nghĩa bất kể câu ngắn hay dài.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*  
> - Công thức: $\text{Số chunk} = \lceil (\text{độ dài} - \text{overlap}) / (\text{chunk\_size} - \text{overlap}) \rceil$  
> - Thay số: $\lceil (10000 - 50) / (500 - 50) \rceil = \lceil 9950 / 450 \rceil = \lceil 22.11 \rceil = 23$  
> *Đáp án:* **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng từ 50 lên 100, bước nhảy (stride) giảm từ 450 xuống 400 ký tự, dẫn đến số lượng chunk tăng lên thành $\lceil (10000 - 100) / (500 - 100) \rceil = \lceil 9900 / 400 \rceil = 25$ chunks. Người ta muốn tăng độ chồng chéo nhiều hơn để duy trì tính liền mạch của ngữ cảnh giữa hai đoạn văn bản kế tiếp, ngăn chặn tình trạng đứt gãy thông tin hoặc ngắt cụt câu nằm ngay tại ranh giới phân tách.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng biểu thức chính quy lookbehind `(?<=[.!?])\s+` để tách câu tại khoảng trắng đứng sau dấu câu mà không làm mất dấu câu. Sau đó nhóm tối đa `max_sentences_per_chunk` câu vào mỗi chunk, loại bỏ các khoảng trắng thừa. Xử lý trường hợp ngoại lệ chuỗi rỗng hoặc chỉ toàn khoảng trắng thì trả về `[]`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán chia nhỏ đệ quy hai chiều: đầu tiên kiểm tra base case (nếu độ dài nhỏ hơn hoặc bằng `chunk_size` thì trả về chính nó; nếu danh sách separator rỗng hoặc separator là `""` thì cắt cứng theo ký tự). Với mỗi separator theo thứ tự ưu tiên `["\n\n", "\n", ". ", " ", ""]`, nếu mảnh vượt quá `chunk_size` thì đệ quy xuống separator tiếp theo, sau đó thực hiện cơ chế gom (merge) các mảnh nhỏ liền kề lại cho tới khi sát ngưỡng `chunk_size` để tránh sinh ra các chunk vụn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu trữ văn bản dưới dạng danh sách `list[dict]` trong bộ nhớ RAM, mỗi bản ghi chuẩn hóa gồm `id`, `content`, `metadata` (đảm bảo luôn có trường `doc_id`) và vector `embedding`. Khi tìm kiếm (`search`), tính độ tương tự bằng tích vô hướng `_dot` giữa vector truy vấn và từng record (tương đương Cosine similarity do vector đã chuẩn hóa), sau đó sắp xếp giảm dần theo `score` và trả về `top_k` kết quả (đã loại bỏ trường vector nhúng để kết quả gọn gàng).

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc (filter) trước khi tìm kiếm tương tự (Pre-filtering): duyệt qua kho dữ liệu để lọc ra tập ứng viên thỏa mãn toàn bộ các điều kiện trong `metadata_filter`, sau đó mới thực hiện tìm kiếm trên tập này để tránh mất kết quả tốt. Hàm `delete_document` xóa tài liệu bằng cách loại bỏ tất cả các bản ghi có `id` hoặc `metadata['doc_id']` khớp với `doc_id` được cung cấp và trả về `True` nếu có ít nhất một bản ghi bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Áp dụng quy trình RAG 3 bước: đầu tiên gọi `store.search` để lấy `top_k` đoạn trích liên quan nhất; tiếp theo xây dựng prompt đưa ngữ cảnh vào bằng cách đánh số thứ tự `[1]`, `[2]` kèm nguồn tài liệu để đảm bảo khả năng truy vết nguồn (Source Traceability); cuối cùng gọi `llm_fn` để sinh câu trả lời. Nếu store không có kết quả phù hợp, trả về câu thông báo không tìm thấy thông tin thay vì gọi LLM vô ích.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
================================================== test session starts ==================================================
platform win32 -- Python 3.11.7, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Admin\Desktop\New folder\K4-L3B-DuongDinhLong-2A202602474
plugins: anyio-4.15.1
collected 42 items                                                                                                       

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                              [  2%] 
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                       [  4%] 
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                [  7%] 
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                 [  9%] 
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                      [ 11%] 
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                      [ 14%] 
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                            [ 16%] 
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                             [ 19%] 
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                           [ 21%] 
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                             [ 23%] 
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                             [ 26%] 
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                        [ 28%] 
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                    [ 30%] 
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                              [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                     [ 35%] 
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                         [ 38%] 
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                   [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                         [ 42%] 
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                             [ 45%] 
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                               [ 47%] 
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                 [ 50%] 
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                       [ 52%] 
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                            [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                              [ 57%] 
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                  [ 59%] 
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                               [ 61%] 
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                        [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                       [ 66%] 
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                  [ 69%] 
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                              [ 71%] 
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                         [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                             [ 76%] 
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                   [ 78%] 
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                             [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED          [ 83%] 
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                        [ 85%] 
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                       [ 88%] 
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED           [ 90%] 
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                      [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED               [ 95%] 
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED     [ 97%] 
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED         [100%] 

================================================== 42 passed in 0.23s =================================================== 

```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|:---:|---|---|:---:|:---:|:---:|
| 1 | Đơn hàng của tôi bao giờ giao tới? | Khi nào tôi nhận được hàng? | cao | 0.7370 | Đúng |
| 2 | Chính sách đổi trả hàng của Shopee | Quy định hoàn tiền và trả hàng trên sàn Shopee | cao | 0.7597 | Đúng |
| 3 | Tôi muốn hủy đơn hàng này | Thời hạn bảo hành sản phẩm là bao lâu? | thấp | 0.1545 | Đúng |
| 4 | Cách đóng gói hàng hóa dễ vỡ | Hàng cồng kềnh có được vận chuyển không? | thấp | 0.3732 | Đúng |
| 5 | Trái cây tươi có được trả hàng không? | Thời tiết hôm nay ở Hà Nội rất đẹp | thấp | 0.0875 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Điểm số ở Cặp 4 (0.3732) cao hơn đáng kể so với Cặp 3 (0.1545) và Cặp 5 (0.0875) là điểm đáng chú ý nhất, vì cả hai câu ở Cặp 4 đều thuộc miền chủ đề về đặc tính hàng hóa và dịch vụ logistics trong thương mại điện tử (hàng dễ vỡ vs hàng cồng kềnh). Điều này cho thấy mô hình embedding thực thụ không chỉ so khớp từ vựng máy móc mà còn nắm bắt được mối liên hệ ngữ nghĩa theo ngữ cảnh của các khái niệm chuyên ngành vận chuyển.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua Shopee phải gửi yêu cầu trả hàng hoặc hoàn tiền trong bao lâu sau khi giao hàng thành công? | `shopee-return-refund-policy`: Mục 5 - Trách nhiệm và thời hạn phản hồi; đơn thông thường 15 ngày, hàng thực phẩm tươi sống/đông lạnh 24 giờ... | 0.8121 | Có (Chính xác Top-1) | Đơn thông thường: 15 ngày; thực phẩm tươi sống và đông lạnh: 24 giờ kể từ khi giao thành công. [1] |
| 2 | MediaMart cho đổi sản phẩm chưa qua sử dụng trong thời hạn nào theo từng nhóm sản phẩm? | `mediamart-baohanh-buyer`: Mục 1 - Phạm vi bảo hành (Top-1: 0.6292). Chunk liên quan `mediamart-doitra-buyer`: Chính sách đổi trả hàng chưa qua sử dụng nằm ở Top-3 (score: 0.6001). | 0.6292 | Có (Đoạn liên quan ở Top-3) | Điện tử/điện lạnh: 3 ngày; ĐT/tablet: 15 ngày; laptop, máy ảnh: 2 ngày; phụ kiện: 30 ngày. [1] |
| 3 | Cần làm gì khi nhận được yêu cầu trả hàng và hoàn tiền? (Filter: `audience: seller`) | `tiktok-manage-return-refund`: Mục Yêu cầu trả hàng và hoàn tiền là gì; quy trình thao tác tại Trung tâm nhà bán hàng > Đơn hàng > Quản lý yêu cầu trả hàng... | 0.6896 | Có (Chính xác Top-1) | Người bán vào Trung tâm nhà bán hàng > Đơn hàng > Quản lý yêu cầu trả hàng, lọc Trả hàng và hoàn tiền; xử lý thủ công trong 1 ngày dương lịch. [1] |
| 4 | MediaMart hỗ trợ những phương thức thanh toán nào? | `mediamart-thanhtoan-buyer`: Mục 1, 2, 3 - Thanh toán tiền mặt khi giao hàng, thanh toán trước qua chuyển khoản/thẻ tại văn phòng, và thanh toán trực tuyến... | 0.7801 | Có (Chính xác Top-1) | Hỗ trợ tiền mặt, thanh toán trước qua chuyển khoản/thẻ tại văn phòng, và thanh toán trực tuyến thẻ quốc tế/nội địa. [1] |
| 5 | Hãy liệt kê các thời hạn khiếu nại và xử lý khiếu nại vận chuyển của Shopee. | `shopee-shipping-policy`: Mục 5.1 - Thời hạn khiếu nại: cung cấp bằng chứng trong 24 giờ; hàng thất lạc khi chuyển hoàn 7 ngày; hư hại 3 ngày; Shopee xử lý trong 10 ngày... | 0.7720 | Có (Chính xác Top-1) | Thất lạc chuyển hoàn: 7 ngày; hư hại: 3 ngày; sai phí: 7 ngày; cung cấp bằng chứng: 24 giờ; Shopee xử lý tối đa 10 ngày làm việc. [1] |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5 (4 câu đạt Top-1, 1 câu đạt Top-3)

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Chiến lược tiền lọc (pre-filtering) bằng metadata `audience` thực sự là yếu tố quyết định để phân biệt chính sách người mua (`buyer`) và người bán (`seller`) khi ngữ nghĩa câu từ tương đồng (ví dụ cùng hỏi về "trả hàng"). Ngoài ra, việc dùng chiến lược phân đoạn theo tiêu đề mục (`Heading-based chunking`) kết hợp gán breadcrumb tiêu đề vào đầu chunk giúp giữ trọn vẹn ngữ cảnh quy định pháp lý tốt hơn hẳn so với cắt cứng cố định chiều dài (`fixed-size`).*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 9 / 10 |
| **Tổng phần cá nhân** | **59 / 60** |
