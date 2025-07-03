# Chatbot Bảo Mẫu trên Facebook Messenger

## Giới thiệu

**Chatbot Bảo Mẫu** là hệ thống tư vấn chuyên sâu về chăm sóc trẻ em, hoạt động trực tiếp trên nền tảng Facebook Messenger. Chatbot được thiết kế như một chuyên gia bảo mẫu, có khả năng lắng nghe, phân tích bối cảnh hội thoại, truy xuất tài liệu chuyên ngành và đưa ra lời khuyên thấu cảm, chính xác cho phụ huynh.

---

## Tính năng nổi bật
- **Hiểu bối cảnh hội thoại:** Lưu trữ và phân tích lịch sử trò chuyện để tư vấn cá nhân hóa.
- **Phân loại thông minh:** Tự động nhận biết câu hỏi xã giao và thắc mắc chuyên sâu.
- **Hỏi bổ sung thông tin:** Chủ động hỏi thêm các yếu tố quan trọng (như độ tuổi trẻ) nếu cần thiết.
- **Tối ưu hóa truy vấn:** Chuyển đổi ngôn ngữ đời thường thành câu hỏi nghiên cứu chuyên sâu.
- **Tìm kiếm tài liệu chuyên ngành:** Truy xuất tài liệu phù hợp nhất từ cơ sở dữ liệu vector.
- **Soạn thảo câu trả lời chuyên nghiệp:** Kết hợp tài liệu, bối cảnh và giọng văn thấu cảm.

---

## Kiến trúc hệ thống

- **Backend:** FastAPI phục vụ webhook tích hợp với Facebook Messenger.
- **Luồng hội thoại:** Xây dựng bằng LangGraph (StateGraph) và LangChain, tích hợp LLM (Google Gemini).
- **Tìm kiếm tài liệu:** Vector Database với mô hình nhúng tiếng Việt.
- **Bảo mật:** Hỗ trợ SSL cho triển khai thực tế.

### Sơ đồ luồng hoạt động

1. **Tiếp nhận & Lắng nghe:** Nhận tin nhắn, tải lịch sử hội thoại.
2. **Phân loại Sơ bộ:** Xác định ý định tin nhắn (xã giao hay chuyên sâu).
3. **Xác định Đối tượng:** Kiểm tra thông tin tuổi trẻ, hỏi bổ sung nếu thiếu.
4. **Chắt lọc Vấn đề:** Tối ưu hóa truy vấn dựa trên bối cảnh.
5. **Nghiên cứu Tài liệu:** Tìm kiếm tài liệu tham khảo phù hợp nhất.
6. **Đưa ra Lời khuyên:** Soạn câu trả lời hoàn chỉnh, thấu cảm, có trách nhiệm.

---

## Chi tiết cấu trúc chatbot (`chatbot.py`)

File `chatbot.py` hiện thực hóa toàn bộ luồng tư vấn thông minh thông qua một đồ thị trạng thái (StateGraph) gồm các node chính:

### Định nghĩa trạng thái hội thoại
```python
class State(TypedDict):
    messages: Annotated[list, add_messages]
    age_group_children: str
    decision: str
    query: str
    info: list
    parent_name: str
    vector_db: VectorDatabase 
```
- Lưu trữ lịch sử tin nhắn, nhóm tuổi trẻ, quyết định phân luồng, truy vấn tối ưu, tài liệu tham khảo, tên phụ huynh, và kết nối tới vector database.

### Các node xử lý chính
- **llm_router:** Phân loại ý định tin nhắn (xã giao hay cần tư vấn chuyên sâu).
- **normal_answer:** Trả lời các câu hỏi xã giao, thông tin chung.
- **get_age_group_children_router:** Kiểm tra đã biết nhóm tuổi trẻ chưa, nếu chưa sẽ hỏi thêm.
- **ask_age_group_children:** Soạn câu hỏi lịch sự để xin thông tin tuổi trẻ.
- **optimize_query:** Tổng hợp thông tin, tối ưu hóa truy vấn cho tìm kiếm tài liệu.
- **retrieve_info:** Tìm kiếm tài liệu phù hợp nhất trong vector database.
- **answer_with_info:** Soạn câu trả lời hoàn chỉnh, kết hợp tài liệu và bối cảnh hội thoại.

### Đồ thị luồng hội thoại
- Đồ thị được xây dựng với các node và điều kiện chuyển tiếp:
    - Bắt đầu từ `llm_router` → nếu xã giao thì sang `normal_answer`, nếu chuyên sâu thì sang `get_age_group_children_router`.
    - Nếu chưa biết tuổi trẻ, chuyển sang `ask_age_group_children`, nếu đã biết thì tối ưu truy vấn.
    - Sau khi tối ưu truy vấn, tìm kiếm tài liệu và trả lời chuyên sâu.
    - Các node kết thúc sẽ trả về tin nhắn cho phụ huynh.

### Tích hợp LLM và Vector Database
- Sử dụng Google Gemini (qua LangChain) để phân tích, tối ưu truy vấn và soạn thảo câu trả lời.
- VectorDatabase dùng để lưu trữ và truy xuất tài liệu chuyên ngành, đảm bảo câu trả lời có cơ sở.

---

## Hướng dẫn triển khai

1. **Cài đặt thư viện:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Cấu hình môi trường:**
   - Tạo file `.env` từ `.env_example` và điền các thông tin cấu hình Facebook API, Google API Key.
3. **Khởi động server FastAPI:**
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```
4. **Kết nối webhook với Facebook Developer Console.**

---

## Thư mục & file quan trọng
- `app.py`: Tích hợp webhook, xử lý kết nối Messenger, quản lý hội thoại.
- `chatbot.py`: Định nghĩa luồng tư vấn thông minh, tích hợp LLM và vector database.
- `vector_storage/`: Lưu trữ dữ liệu vector cho tìm kiếm tài liệu.
- `raw_data/`: Dữ liệu thô về các nhóm tuổi trẻ em.
- `prompt_guide/`: Prompt template cho LLM.
- `utils/`: Tiện ích hỗ trợ (đọc biến môi trường, ...).
- `SSL/`: Chứng chỉ bảo mật cho triển khai thực tế.
