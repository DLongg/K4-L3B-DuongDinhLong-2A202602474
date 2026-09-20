# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Buddy
**Thành viên:** Nguyễn Đình Thái, Vũ Tiến Linh, Dương Đình Long
**Ngày:** 20/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách bảo hành, thanh toán, vận chuyển, trả hàng và hoàn tiền trên các nền tảng thương mại điện tử tại Việt Nam.

**Tại sao nhóm chọn chủ đề này?**
> Bộ tài liệu có nhiều điều kiện, thời hạn và quy trình khác nhau giữa TikTok Shop, MediaMart và Shopee, phù hợp để đánh giá chất lượng chunking và truy xuất. Việc phân loại theo `audience` và `category` giúp nhóm kiểm chứng tác dụng của metadata filter khi cần tìm đúng nền tảng, đối tượng hoặc loại chính sách.

### Phân công thu thập dữ liệu

| Thành viên | Vai điều phối | Ba tài liệu phụ trách |
|---|---|---|
| Nguyễn Đình Thái | R1 · Data | `tiktok-change-of-mind-return`, `tiktok-manage-return-refund`, `tiktok-seller-return-to-buyer` |
| Vũ Tiến Linh | R2 · Benchmark | `mediamart-baohanh-buyer`, `mediamart-doitra-buyer`, `mediamart-thanhtoan-buyer` |
| Dương Đình Long | R3 · Strategy | `shopee-return-refund-policy`, `shopee-shipping-policy`, `tiktok-return-refund-policy` |

Mỗi người chịu trách nhiệm đối chiếu nguồn, làm sạch nội dung và kiểm tra metadata của ba file được giao. Sau khi ghép corpus, cả ba cùng dùng đủ chín tài liệu và cùng năm câu hỏi benchmark; chỉ chiến lược chunking là khác nhau.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Trả hàng do Đổi ý | [TikTok Shop](https://seller-vn.tiktok.com/university/essay?knowledge_id=6988871880738576) | 20/09/2026 / không nêu | 8.704 | `buyer`, `change-of-mind`, `vi` |
| 2 | Quản lý yêu cầu trả hàng và hoàn tiền | [TikTok Shop](https://seller-vn.tiktok.com/university/essay?knowledge_id=6819122768905985) | 20/09/2026 / không nêu | 4.741 | `seller`, `seller-return-management`, `vi` |
| 3 | Trả hàng từ người bán đến khách hàng | [TikTok Shop](https://seller-vn.tiktok.com/university/essay?knowledge_id=4041059496167184&lang=vi-VN) | 20/09/2026 / không nêu | 5.058 | `seller`, `dispute-return`, `vi` |
| 4 | Chính sách bảo hành tại MediaMart | [MediaMart](https://mediamart.vn/chinh-sach-chung/chinh-sach-bao-hanh) | 20/09/2026 / không nêu | 2.122 | `buyer`, `warranty-policy`, `vi` |
| 5 | Chính sách đổi trả hàng tại MediaMart | [MediaMart](https://mediamart.vn/chinh-sach-chung/chinh-sach-doi-tra-hang-old) | 20/09/2026 / không nêu | 1.863 | `buyer`, `return-policy`, `vi` |
| 6 | Quy định thanh toán tại MediaMart | [MediaMart](https://mediamart.vn/chinh-sach-chung/quy-dinh-thanh-toan) | 20/09/2026 / không nêu | 1.176 | `buyer`, `payment-policy`, `vi` |
| 7 | Chính sách trả hàng và hoàn tiền Shopee | [Shopee](https://help.shopee.vn/portal/article/77491) | 20/09/2026 / không nêu | 3.887 | `buyer`, `return-refund-policy`, `vi` |
| 8 | Chính sách vận chuyển Shopee | [Shopee](https://help.shopee.vn/portal/4/article/206477) | 20/09/2026 / không nêu | 5.026 | `buyer`, `shipping-policy`, `vi` |
| 9 | Chính sách hủy đơn trả hàng và hoàn tiền TikTok Shop | [TikTok Shop](https://seller-vn.tiktok.com/university/essay?identity=1&role=1&knowledge_id=1766935302801169) | 20/09/2026 / không nêu | 5.384 | `both`, `return-refund-policy`, `vi` |

> Số ký tự được tính trên phần nội dung đã làm sạch, không bao gồm YAML frontmatter.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.
- [x] `sources.csv` khớp một-một với 9 file và mỗi `doc_id` là duy nhất.
- [x] Corpus có đủ `audience`: `buyer`, `seller`, `both` để thử nghiệm metadata filter.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `mediamart-doitra-buyer` | Định danh ổn định tài liệu gốc và liên kết các chunk cùng nguồn. |
| `title` | string | `Chính sách đổi trả hàng tại MediaMart` | Hiển thị nguồn dễ hiểu và bổ sung ngữ cảnh chủ đề. |
| `source_url` | URL | `https://mediamart.vn/...` | Truy vết và kiểm chứng câu trả lời với nguồn công khai. |
| `retrieved_at` | date | `2026-09-20` | Xác định thời điểm nhóm thu thập dữ liệu. |
| `document_version` | date/string | `not-stated` | Ghi nhận nguồn không nêu phiên bản; dùng ngày cụ thể khi nguồn công bố rõ. |
| `audience` | enum | `buyer`, `seller`, `both` | Lọc chính sách theo đúng đối tượng sử dụng. |
| `category` | string | `return-policy` | Thu hẹp truy xuất theo loại quy trình hoặc chính sách. |
| `language` | string | `vi` | Bảo đảm truy vấn và tài liệu sử dụng cùng ngôn ngữ. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `mediamart-doitra-buyer` | FixedSizeChunker (`fixed_size`) | 5 | 412,6 | Một số danh sách có thể bị cắt giữa ý. |
| `mediamart-doitra-buyer` | SentenceChunker (`by_sentences`) | 6 | 309,2 | Giữ câu tốt, nhưng cấu trúc bullet chưa luôn trọn vẹn. |
| `mediamart-doitra-buyer` | RecursiveChunker (`recursive`) | 6 | 309,2 | Giữ được ranh giới đoạn và danh sách tốt hơn. |
| `shopee-return-refund-policy` | FixedSizeChunker (`fixed_size`) | 9 | 476,3 | Kích thước đều nhưng có thể cắt ngang heading hoặc mục. |
| `shopee-return-refund-policy` | SentenceChunker (`by_sentences`) | 13 | 297,2 | Giữ câu nhưng tạo nhiều chunk nhỏ. |
| `shopee-return-refund-policy` | RecursiveChunker (`recursive`) | 12 | 322,2 | Phần lớn giữ được đoạn chính sách liên quan. |
| `tiktok-change-of-mind-return` | FixedSizeChunker (`fixed_size`) | 20 | 482,7 | Dễ cắt ngang danh sách ngành hàng dài. |
| `tiktok-change-of-mind-return` | SentenceChunker (`by_sentences`) | 16 | 541,5 | Có chunk vượt ngưỡng do danh sách dài ít dấu kết câu. |
| `tiktok-change-of-mind-return` | RecursiveChunker (`recursive`) | 22 | 393,8 | Bám ranh giới đoạn tốt và kiểm soát kích thước ổn định hơn. |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Nguyễn Đình Thái**
- **Loại chiến lược:** `FixedSizeChunker(chunk_size=500, overlap=100)`
- **Mô tả & lý do chọn cho chủ đề này:** Kích thước cố định giúp kiểm soát số ký tự đưa vào embedding và dễ so sánh với baseline. Overlap 100 ký tự được dùng để giảm nguy cơ mất điều kiện hoặc thời hạn nằm đúng tại ranh giới hai chunk, đổi lại số chunk và chi phí embedding tăng.
- **Code snippet (nếu custom):**
```python
CHUNKER = FixedSizeChunker(chunk_size=500, overlap=100)
```

**Thành viên 2 — Vũ Tiến Linh**
- **Loại chiến lược:** `RecursiveChunker(chunk_size=500)`
- **Mô tả & lý do chọn:** Ưu tiên chia theo đoạn, dòng và câu trước khi phải cắt cứng, phù hợp với văn bản chính sách có nhiều đoạn và danh sách. Chiến lược này hạn chế cắt ngang một ý nhưng không dựa trực tiếp vào cấu trúc heading.
- **Code snippet (nếu custom):**
```python
CHUNKER = RecursiveChunker(chunk_size=500)
```

**Thành viên 3 — Dương Đình Long**
- **Loại chiến lược:** `HeadingChunker(chunk_size=500)` — custom, bắt buộc theo vai R3.
- **Mô tả & lý do chọn:** Mỗi mục Markdown được xem là một đơn vị ngữ nghĩa. Khi section dài hơn 500 ký tự, nội dung được chia tiếp bằng recursive và tiêu đề được gắn lại vào mọi mảnh con để các chunk sau vẫn giữ được chủ đề.
- **Code snippet (nếu custom):**
```python
body_chunks = RecursiveChunker(chunk_size=body_size).chunk(body)
chunks.extend(f"{heading}\n\n{part}" for part in body_chunks)
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Đình Thái | FixedSizeChunker (`chunk_size=500`, `overlap=100`) | 4 / 10 | Kích thước ổn định; overlap giúp các chunk thanh toán MediaMart ở top-1/top-2 bổ sung được cho nhau. | Danh sách thời hạn bị cắt qua ranh giới; chunk đúng có thể không vào top-3 dù cùng tài liệu gold. |
| Vũ Tiến Linh | RecursiveChunker (`chunk_size=500`) | 3 / 10 | Tách rõ ba mục thanh toán MediaMart; cả ba chunk cần thiết cho câu 4 đều nằm trong top-3. | Các chunk đích cho câu 1, 2, 3 và 5 không vào top-3 hoặc chỉ chứa phần thông tin, nên không trả lời gold đầy đủ. |
| Dương Đình Long | CustomHeadingChunker | 6 / 10 | Giữ heading cùng nội dung, trả về các section thanh toán và khiếu nại Shopee sát chủ đề; A/B filter loại được một kết quả buyer ở vị trí top-3. | Câu 1 không có gold 15 ngày/24 giờ trong top-3; câu 2 và 3 chỉ có một phần ngữ cảnh. File này cũng chạy 11 tài liệu/157 chunks, khác corpus 9 tài liệu của hai kết quả còn lại. |

### Ma trận chấm theo nội dung top-3

> Quy ước: 2 = ngữ cảnh top-3 có đủ dữ kiện gold để trả lời; 1 = chỉ có một phần hoặc chunk liên quan nằm ở top-2/top-3; 0 = không có dữ kiện trả lời. Các file benchmark chưa in câu trả lời của agent, vì vậy đây là điểm retrieval-context thận trọng.

| Chiến lược | Câu 1 | Câu 2 | Câu 3 | Câu 4 | Câu 5 | Tổng |
|---|---:|---:|---:|---:|---:|---:|
| FixedSizeChunker | 0 | 1 | 0 | 2 | 1 | **4 / 10** |
| RecursiveChunker | 0 | 0 | 0 | 2 | 1 | **3 / 10** |
| CustomHeadingChunker | 0 | 1 | 1 | 2 | 2 | **6 / 10** |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Chưa thể xếp hạng tuyệt đối cả ba chiến lược vì HeadingChunker được đo trên corpus 11 tài liệu, còn FixedSize và Recursive cùng dùng corpus 9 tài liệu. Chấm lại theo nội dung top-3 cho kết quả FixedSize 4/10, Recursive 3/10 và Heading 6/10; Heading bị trừ điểm vì top-3 ở câu 1 không có gold answer, dù `doc_id` đúng. Heading là hướng hứa hẹn cho văn bản chính sách vì giữ được tiêu đề, nhưng cần chạy lại trên đúng 9 tài liệu và cùng embedding để kết luận công bằng.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Người mua Shopee phải gửi yêu cầu trả hàng hoặc hoàn tiền trong bao lâu sau khi giao hàng thành công? | Đơn thông thường: 15 ngày; thực phẩm tươi sống và đông lạnh: 24 giờ kể từ khi giao thành công. | `shopee-return-refund-policy` — `## 3. Thời hạn gửi yêu cầu trả hàng / hoàn tiền` |
| 2 | MediaMart cho đổi sản phẩm chưa qua sử dụng trong thời hạn nào theo từng nhóm sản phẩm? | Điện tử/điện lạnh/gia dụng: 3 ngày; điện thoại và máy tính bảng: 15 ngày; laptop, máy ảnh, máy quay: 2 ngày; phụ kiện đủ điều kiện: 30 ngày, kèm các ngoại lệ nêu trong chính sách. | `mediamart-doitra-buyer` — `## 1. Đối với sản phẩm chưa qua sử dụng` |
| 3 | Cần làm gì khi nhận được yêu cầu trả hàng và hoàn tiền? | Người bán vào Trung tâm nhà bán hàng → Đơn hàng → Quản lý yêu cầu trả hàng, mở tab Đang chờ hành động và lọc Trả hàng và hoàn tiền; yêu cầu thủ công phải được duyệt hoặc từ chối trong 1 ngày dương lịch, và hàng trả phải được kiểm tra trong 2 ngày dương lịch. Câu này dùng `metadata_filter={"audience": "seller"}`. | `tiktok-manage-return-refund` — `## Cách quản lý yêu cầu trả hàng và hoàn tiền` |
| 4 | MediaMart hỗ trợ những phương thức thanh toán nào? | Thanh toán tiền mặt; thanh toán trước bằng chuyển tiền/chuyển khoản, tiền mặt hoặc thẻ tại văn phòng; và thanh toán trực tuyến bằng thẻ quốc tế, thẻ nội địa hoặc dịch vụ thanh toán điện tử. | `mediamart-thanhtoan-buyer` — các mục `## 1` đến `## 3` |
| 5 | Hãy liệt kê các thời hạn khiếu nại và xử lý khiếu nại vận chuyển của Shopee. | Thất lạc khi chuyển hoàn: 7 ngày; hàng hư hại/không nguyên vẹn: 3 ngày; khiếu nại sai phí: 7 ngày; cung cấp bằng chứng: 24 giờ; Shopee xử lý tối đa 10 ngày làm việc sau khi nhận đủ bằng chứng hợp lệ. | `shopee-shipping-policy` — `### 5.1. Thời hạn khiếu nại` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn gửi yêu cầu Shopee | Chưa có kết quả đủ điều kiện để kết luận | Không, với FixedSize và Recursive | Cả hai trả về chunk cùng chủ đề/thời hạn nhưng không có đồng thời 15 ngày và 24 giờ. |
| 2 | Đổi sản phẩm chưa dùng MediaMart | FixedSize hoặc Heading (một phần) | Có một phần | FixedSize có 3/15 ngày; Heading đưa đúng tài liệu ở top-3; cả hai chưa chứng minh đủ đồng thời các mốc 2/30 ngày. |
| 3 | Quy trình xử lý trả hàng/hoàn tiền | Heading (một phần) | Có một phần | Heading đưa đúng tài liệu seller và chunk về xử lý hàng trả; vẫn thiếu một phần đường dẫn thao tác và các mốc 1/2 ngày. |
| 4 | Phương thức thanh toán MediaMart | Cả ba chiến lược | Có | FixedSize có ngữ cảnh đủ ở top-1/top-2; Recursive và Heading có đủ ba section tiền mặt, thanh toán trước và trực tuyến trong top-3. |
| 5 | Thời hạn khiếu nại vận chuyển Shopee | Heading (kết quả riêng, chưa so trực tiếp) | Có theo file Heading | Hai section 5.1 của Heading bổ sung các mốc khiếu nại; Fixed/Recursive thiếu ít nhất một mốc trong top-3. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có. Thử nghiệm A/B của HeadingChunker ở câu 3 giữ nguyên hai kết quả seller ở top-1/top-2, đồng thời thay kết quả top-3 `shopee-return-refund-policy` có `audience=buyer` bằng `tiktok-seller-return-to-buyer` có `audience=seller`. Filter vì vậy tăng độ đúng đối tượng, dù riêng top-3 vẫn chưa bảo đảm đủ mọi chi tiết của gold answer.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> Chấm lại HeadingChunker từ 9/10 tự báo xuống 6/10 cho thấy `doc_id` đúng chưa đủ để kết luận retrieval đúng: ở câu 1, các chunk Shopee trả về nói về thời hạn phản hồi 2 ngày, không chứa đáp án 15 ngày và 24 giờ. Khi đáp án là danh sách dài, overlap hoặc heading chỉ giảm rủi ro mất ngữ cảnh chứ không bảo đảm các mảnh chứa toàn bộ số liệu cùng lọt top-3. Kết quả A/B của HeadingChunker cũng cho thấy metadata filter cải thiện đúng đối tượng, không tự động bảo đảm đủ chi tiết câu trả lời.

**Bài học rút ra khi so sánh trong nhóm:**
> FixedSize và Recursive cùng chạy 9 tài liệu, lần lượt tạo 98 và 106 chunks; khác biệt ranh giới chunk làm thay đổi mạnh các section có mặt trong top-3. Heading giữ được cấu trúc mục tốt hơn cho văn bản chính sách, nhưng kết quả đang dùng 11 tài liệu nên nhóm không so sánh điểm trực tiếp. Lần đo tiếp theo phải giữ cố định corpus, năm query, embedding và cách chấm theo nội dung.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Với các mục chính sách có danh sách nhiều mốc thời gian, nhóm sẽ ưu tiên chunk theo heading hoặc recursive và gắn heading cho các mảnh con. Nhóm cũng sẽ kiểm chứng gold answer bằng các chuỗi đặc trưng thay vì chỉ kiểm `doc_id` của top-3, đồng thời buộc mọi thành viên chạy trên cùng một corpus trước khi tổng hợp điểm.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 13 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 6 / 10 |
| Thuyết trình (Demo) | 4 / 5 |
| **Tổng phần nhóm** | **33 / 40** |

> Lý do tự đánh giá: corpus có 9 tài liệu cùng chủ đề, provenance và metadata đã được kiểm tra tự động. Nhóm có ba hướng chunking, query/gold answer và A/B metadata filter; tuy nhiên kết quả Heading hiện đo trên corpus 11 tài liệu nên chưa thể so sánh trực tiếp với FixedSize và Recursive. Điểm retrieval được chấm lại theo nội dung top-3 là FixedSize 4/10, Recursive 3/10 và Heading 6/10, không dùng `doc_id` hoặc score tự báo làm tiêu chí duy nhất. Phần demo đã có kịch bản và bằng chứng benchmark, nhưng điểm cuối cùng phụ thuộc phần trình bày trực tiếp.
