# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. API Key được hardcode thẳng vào trong source code. Điều này nghĩa là nếu source code bị lộ (hoặc để open source trên github), key sẽ bị leak ra ngoài -> đồng nghĩa với bad actor được dùng thoải mái

`OPENAI_API_KEY = "sk-hardcoded-fake-key-never-do-this"`\
`DATABASE_URL = "postgresql://admin:password123@localhost:5432/mydb"`

2. Các config cũng là hard code thẳng vào trong file app, thay vì có file config riêng. Điều này dẫn tới 
  - Lúc cần tìm để đổi config khó
  - Config nhiều lúc không persist qua các file khác nhau.
  - Lúc đổi config lại phải chỉnh trong source code -> khó chuyển đổi giữa prod và dev env.
`DEBUG = True`\
`MAX_TOKENS = 500`
` 

3. Debug sử dụng print thay vì proper logging, các log sẽ hiện lên terminal và không persist. Key API cũng bị log ra -> không bảo mật Key
`print(f"[DEBUG] Got question: {question}")`\
`print(f"[DEBUG] Using key: {OPENAI_API_KEY}")`

4. Không có healthcheck endpoint -> nếu server hogrn, sập, agent không chạy, sẽ không biết kịp để xử lý.

5. fix cứng uvicorn config: chạy trên local, port fix, và reload = True (nên dùng cho dev environments)  

6. Shutdown đột ngột: không có xử lý shutdown, khi tắt server, mọi thứ đổ sụp và không có gì làm cả, không để grace period cho cập nhật
...

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config | Hardcoded trong source code | Load từ Environment Variables | Giúp cấu hình linh hoạt không cần sửa source code, không làm lộ secret info. |
| HealthCheck | Không có | Liveness probe `/health` | Cloud platform biết container có còn sống không để tự động restart nếu bị treo. |
| Readiness Probe | Không có | Readiness probe `/ready` | Load balancer biết ứng dụng khởi động xong hay chưa để bắt đầu chuyển traffic tới. |
| Logging | `print()` thường, log ra terminal | JSON Structured Logging | Logs chuẩn JSON dễ dàng được parse/search ở các công cụ quản lý log tập trung, và không log secrets. |
| Shutdown | Đột ngột, cắt kết nối luôn | Graceful Shutdown (SIGTERM) | Đóng ứng dụng an toàn: từ chối request mới, chờ xử lý nốt các request dở dang, không làm mất request. |
| Port binding | Hardcode host và cố định port | Bind `0.0.0.0` và cổng lấy từ env `PORT` | Yêu cầu bắt buộc để chạy trong container và dễ dàng map với port động mà Cloud provider cấp. |

...

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. **Base image:** `python:3.11` (Full Python distribution, khá nặng ~1GB).
2. **Working directory:** `/app` (thư mục làm việc mặc định bên trong container).
3. **Tại sao COPY requirements.txt trước?** Để tận dụng tối đa Docker layer cache. Nếu file requirements không đổi, Docker không phải tốn thời gian tải lại packages ở các lần build sau.
4. **CMD vs ENTRYPOINT khác nhau thế nào?** `CMD` định nghĩa lệnh khởi chạy mặc định nhưng dễ bị ghi đè trực tiếp khi chạy `docker run`. `ENTRYPOINT` quy định process chính, khó bị ghi đè hơn, ta thường kết hợp cả hai để `CMD` đóng vai trò là tham số mặc định của `ENTRYPOINT`.

### Exercise 2.3: Multi-stage build & Image size comparison
- **Stage 1 (Builder stage):** Dùng `python:3.11-slim` cài các công cụ build (gcc, compiler) và tải/cài các Python dependencies vào một thư mục (--user).
- **Stage 2 (Runtime stage):** Dùng `python:3.11-slim` mới, thiết lập non-root user và CHỈ copy các dependencies đã cài sẵn từ Stage 1 sang cùng mã nguồn. Không mang theo các công cụ build.
- **Tại sao image nhỏ hơn?** Vì Stage 2 hoàn toàn sạch bóng các công cụ compile code (gcc, C headers) và cache file của trình quản lý gói (pip), chỉ chứa đúng môi trường runtime.
- **Image size comparison (Ước lượng):**
  - Develop: ~1.66 GB (1GB do dùng image gốc python 3.11)
  - Production: ~369 MB (python-slim base + chỉ mang theo app dependencies)
  - Difference: Giảm >85% dung lượng.

### Exercise 2.4: Docker Compose stack
- **Services nào được start?** `agent` (chạy các container backend FastAPI) và `nginx` (chạy Reverse Proxy/Load Balancer).
- **Chúng communicate thế nào?** Client gửi request qua Nginx. Nginx làm Load Balancer phân tán các request đó tới các `agent` container đằng sau thông qua Docker internal network (cùng chung một network).

## Part 3: Cloud Deployment

### Exercise 3.2: Render deployment
- URL: https://your-app.railway.app
- Screenshot: [Link to screenshot in repo]

## Part 4: API Security

### Exercise 4.1-4.3: Test results
[Paste your test outputs]

### Exercise 4.4: Cost guard implementation
[Explain your approach]

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
[Your explanations and test results]
```