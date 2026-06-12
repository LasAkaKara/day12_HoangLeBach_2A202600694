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
- URL: https://ai-agent-ndg5.onrender.com/
- Screenshot:
    ![03-Deploy_Success](Screenshots/03-Deploy_Success.png)
    ![03-Web](Screenshots/03-Web.png)
## Part 4: API Security

### Exercise 4.1: API Key authentication
- **API key được check ở đâu?** Hàm `verify_api_key(api_key: str = Security(api_key_header))` được gọi qua dependency trong endpoint (`Depends(verify_api_key)`).
- **Điều gì xảy ra nếu sai key?** Server trả về mã lỗi HTTP 403 Forbidden với thông báo "Invalid API key."
- **Làm sao rotate key?** Chỉ cần thay đổi biến môi trường `AGENT_API_KEY` rồi restart lại ứng dụng mà không cần phải can thiệp trực tiếp vào mã nguồn.

### Exercise 4.2: JWT Authentication
- **Flow hoạt động:** Client gọi API `/auth/token` để đổi `username/password` lấy một `access_token` (chuỗi JWT). Khi truy cập các endpoint được bảo vệ (như `/ask`), Client đính kèm JWT này vào header `Authorization: Bearer <token>`. Middleware `verify_token` sẽ tự động parse token, xác thực và lấy ra role để phân quyền.

### Exercise 4.3: Rate limiting
- **Algorithm nào được dùng?** Thuật toán Sliding Window Counter (dùng `deque` để lưu danh sách timestamp của các request trong khoảng window).
- **Limit là bao nhiêu requests/minute?**
  - **User thường:** 10 requests / 60 seconds.
  - **Admin:** 100 requests / 60 seconds.
- **Làm sao bypass limit cho admin?** Backend đọc Role từ Payload của JWT. Nếu role là "admin", hệ thống sẽ tự động dùng object `rate_limiter_admin` (100 req/min) thay cho `rate_limiter_user` (10 req/min).

### Exercise 4.4: Cost guard implementation
- **Sử dụng Redis (Giải pháp Production-ready):**
  Trong code hiện tại `CostGuard` đang lưu in-memory (`self._records = {}`), điều này sẽ không hoạt động đúng nếu deploy nhiều instance/container. Cần sử dụng Redis để lưu trạng thái dùng chung.
  ```python
  import redis
  from datetime import datetime
  
  r = redis.Redis(host='localhost', port=6379, db=0)
  
  def check_budget(user_id: str, estimated_cost: float) -> bool:
      month_key = datetime.now().strftime("%Y-%m")
      key = f"budget:{user_id}:{month_key}"
      
      current = float(r.get(key) or 0)
      if current + estimated_cost > 10.0: # Giới hạn $10/tháng
          return False
      
      r.incrbyfloat(key, estimated_cost)
      r.expire(key, 32 * 24 * 3600)  # Tự xoá sau 32 ngày
      return True
  ```

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes

- **Exercise 5.1 (Health & Readiness checks):** 
  - **Liveness Probe (`/health`):** Báo cáo trạng thái sống của agent (có bị treo không) cho Cloud Platform/Docker. Nếu endpoint trả về lỗi hoặc timeout, container sẽ tự động bị restart.
  - **Readiness Probe (`/ready`):** Kiểm tra xem service đã load xong Model AI và có kết nối được Redis/DB chưa. Nếu trả về lỗi (503), Load Balancer (Nginx) sẽ biết và không điều hướng traffic vào instance này, tránh việc user nhận lỗi hệ thống.

- **Exercise 5.2 (Graceful shutdown):**
  - Sử dụng thư viện `signal` để bắt tín hiệu `SIGTERM` (tín hiệu yêu cầu tắt ứng dụng từ Docker/Kubernetes).
  - Thay vì tắt phụt ngay lập tức (Hard kill), ứng dụng sẽ từ chối nhận request mới và chờ (tối đa 30s) để xử lý hoàn tất nốt các request đang dang dở (in-flight requests), gửi xong response về cho client rồi mới thoát hoàn toàn.

- **Exercise 5.3 & 5.5 (Stateless design & Test):**
  - **Anti-pattern:** Lưu session chat trong dictionary trên RAM của biến toàn cục (Global variable). Khi scale ra 3 instances, user chat vào instance 1, nhưng request tiếp theo load balancer chuyển sang instance 2 thì instance 2 sẽ không có context đoạn chat trước.
  - **Stateless:** Refactor lưu toàn bộ lịch sử (history) và session vào Redis. Khi user chat tiếp, bất cứ instance nào nhận được request cũng có thể truy xuất ID lên Redis để lấy history và phản hồi một cách bình thường. `test_stateless.py` đã chứng minh cuộc hội thoại tiếp diễn bình thường kể cả khi kill bất ngờ một vài instances ở giữa.

- **Exercise 5.4 (Load balancing):**
  - Khi start nhiều instance (`--scale agent=3`), Nginx đóng vai trò làm Load Balancer. Client gọi tới port 80 của Nginx, Nginx sẽ luân phiên phân phát request đều đặn đến 3 container backend đằng sau. Giúp hệ thống phân tải (Scale out) và nếu 1 node chết, các node còn lại vẫn hứng traffic.

## Part 6: Final Full-Stack Application

### Project Overview
The final project integrates a robust FastAPI backend with a modern React + Vite frontend, maintaining stateless memory persistence via Redis. The entire stack has been containerized and successfully deployed to the cloud, demonstrating a complete end-to-end production-ready AI application with a beautiful Glassmorphism user interface.

Check out the web at: https://frontend-production-e8fd.up.railway.app/
### Screenshots
- **Deployment Success:**
  ![Final Deployment Success](Screenshots/Final-Deploy_Success.png)
  
- **Web Interface:**
  ![Final Web Interface](Screenshots/Final-Web.png)