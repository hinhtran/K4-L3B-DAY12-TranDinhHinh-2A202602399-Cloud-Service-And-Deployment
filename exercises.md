# Phiếu Phản Ánh — K4 Level 3B, Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Cách trả lời: thay thế bằng câu trả lời của bạn.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Trần Đình Hinh  Mã học viên: 2A202602399

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

> Tình huống thực tế: Khi deploy ứng dụng lên môi trường Production (như Railway hoặc Render), người phụ trách cấu hình quên điền biến môi trường `AGENT_API_KEY` trong dashboard.
> - Nếu để giá trị mặc định `"changeme"`: Ứng dụng vẫn khởi động thành công và báo trạng thái "Healthy". Tuy nhiên, hệ thống lúc này đã mở toang cho bất kỳ ai trên Internet biết hoặc dò được key mặc định `"changeme"` đều có thể gửi request vào endpoint `/ask`, bòn rút token LLM và làm cạn kiệt ngân sách API của dự án. Lỗ hổng này có thể âm thầm tồn tại nhiều tuần mà không ai hay biết.
> - Khi không có giá trị mặc định (Fail Fast): Pydantic sẽ ném ngoại lệ `ValidationError` ngay lúc nạp cấu hình khi tiến trình vừa bật lên, khiến container crash lập tức. Nền tảng điều phối (Railway/K8s) sẽ báo deploy failed hoặc restart liên tục và gửi thông báo lỗi đến lập trình viên. Nhờ đó, ta phát hiện và bổ sung secret ngay lập tức trước khi bất kỳ traffic công khai nào có thể tiếp cận được hệ thống.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

> Dòng log JSON thu được:
> `{"timestamp":"2026-09-29T04:19:12.450123Z","level":"info","event":"request_finished","endpoint":"/ask","method":"POST","status_code":200,"user_id":"cp5-user-1","cost_usd":0.002,"duration_ms":42.5}`
>
> Hai việc làm được với log có cấu trúc (JSON structured logging):
> 1. **Truy vấn, lọc và gom nhóm tự động (Structured Querying & Filtering):** Các hệ thống thu thập log tập trung (như Elasticsearch, Loki, Datadog, CloudWatch) có thể tự động parse các trường JSON để lọc ra ngay lập tức: ví dụ "tất cả request có `user_id = cp5-user-1`", hoặc "các request có `duration_ms > 1000`", hoặc tính tổng `cost_usd` đã tiêu thụ theo từng user. Với `print("đã trả lời xong")`, ta chỉ có một dòng chữ vô nghĩa, không thể phân biệt ai gọi, chi phí bao nhiêu hay tốn bao nhiêu thời gian trừ khi phải viết regex chắp vá rất dễ gãy.
> 2. **Cảnh báo và trực quan hóa Dashboard theo thời gian thực (Alerting & Metrics Dashboard):** Có thể trích xuất trực tiếp trường số liệu `duration_ms` để vẽ biểu đồ p95/p99 latency theo thời gian thực, hoặc tạo rule cảnh báo tự động (alert trigger) gửi tin nhắn Slack/PagerDuty khi `status_code >= 500` hoặc khi `cost_usd` trong 5 phút vượt ngưỡng cho phép. Chuỗi text in ra từ `print` không hỗ trợ phân tích định lượng tự động này.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t agent:single .
docker build -t agent:multi .
docker images | grep agent
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | 485 MB |
| Multi-stage | 168 MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

> Phần dung lượng chênh lệch (~317 MB) bao gồm:
> 1. **Trình biên dịch và công cụ build hệ thống:** Các gói như `gcc`, `g++`, `build-essential`, `python3-dev`, thư viện C headers... cần thiết để biên dịch các thư viện Python (wheels) trong quá trình `pip install`.
> 2. **File cache của trình quản lý gói:** Cache của `pip` nằm trong `~/.cache/pip`, cùng với metadata và cache index của `apt-get` trong `/var/lib/apt/lists/*`.
> 3. **Các file tài liệu và header không dùng ở runtime:** Tài liệu manpages, static libraries (.a), header files (.h) đi kèm các package hệ điều hành.
> 
> Trong mô hình Multi-stage build, stage `builder` thực hiện toàn bộ việc biên dịch và cài đặt vào một virtualenv (`/opt/venv`). Stage thứ hai (`runner`) chỉ sao chép thư mục `/opt/venv` đã hoàn thiện sang một base image `python:3.11-slim` hoàn toàn sạch, loại bỏ toàn bộ chuỗi công cụ build và cache thừa thãi, giúp image nhỏ gọn, kéo image nhanh hơn và giảm thiểu diện tích bề mặt tấn công (attack surface).

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

> - **Với thứ tự chuẩn hiện tại:**
>   1. `COPY requirements.txt .`
>   2. `RUN pip install -r requirements.txt`
>   3. `COPY app/ app/`
>   Khi chỉ sửa một ký tự trong `app/main.py`, file `requirements.txt` hoàn toàn không thay đổi. Do đó, Docker tận dụng cache (CACHE HIT) cho toàn bộ các layer phía trước, bao gồm cả layer cài đặt package `RUN pip install`. Chỉ có layer `COPY app/ app/` và các layer phía sau nó mới bị vô hiệu hóa cache và phải chạy lại. Nhờ đó, thời gian build lại chỉ mất 1-2 giây.
>
> - **Nếu đặt `COPY . .` lên trước `RUN pip install`:**
>   Bất cứ khi nào bạn thay đổi dù chỉ một ký tự trong bất kỳ file mã nguồn nào (`main.py`), checksum của toàn bộ thư mục bị thay đổi, làm layer `COPY . .` bị cache miss. Kéo theo đó, Docker buộc phải chạy lại TẤT CẢ các lệnh tiếp theo sau nó, bao gồm cả lệnh `RUN pip install -r requirements.txt`. Hệ thống sẽ phải tải lại và cài đặt lại toàn bộ thư viện qua mạng từ đầu trong mỗi lần build, khiến thời gian build kéo dài thêm vài phút một cách vô ích.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

> Chuỗi sự kiện tấn công (Container Breakout):
> 1. **Khai thác ứng dụng:** Kẻ tấn công tìm ra một lỗ hổng trong code Python (ví dụ: Unsafe Deserialization qua `pickle`, Command Injection qua `subprocess.Popen(..., shell=True)`, hoặc Remote Code Execution từ thư viện bên thứ ba).
> 2. **Chiếm shell container:** Mã độc thực thi và mở một reverse shell. Vì container mặc định chạy user `root`, tiến trình của kẻ tấn công có UID 0 (root) bên trong container, cho phép đọc/ghi/sửa mọi file trong container.
> 3. **Leo thang và thoát container (Escape to Host):** Vì Linux kernel được chia sẻ chung giữa container và máy host, nếu kernel có lỗ hổng (như Dirty COW, cgroup release agent escape) hoặc container bị gắn quyền lỏng lẻo (`--privileged`, mount nhầm `/var/run/docker.sock` hoặc socket hệ thống), kẻ tấn công với UID 0 bên trong container sẽ tương tác với kernel host dưới tư cách là UID 0 (root của máy host), từ đó chiếm quyền kiểm soát hoàn toàn hệ điều hành host và các container khác.
>
> **Lệnh `USER` cắt đứt chuỗi ở đâu:**
> Lệnh `USER nonroot` (chuyển sang tài khoản thường với UID không đặc quyền như 10001) cắt đứt chuỗi ngay tại **Bước 2**. Khi kẻ tấn công thực thi được mã, chúng chỉ có quyền của user thường trong container: không thể ghi đè file hệ thống, không thể tương tác với các socket quản trị, và không thể kích hoạt hầu hết các lỗ hổng leo thang đặc quyền hay container breakout của kernel để chạm tới root máy host.

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

> - Người dùng có thể gửi tối đa **20 request** trong 2 giây liên tiếp.
> - **Giải thích cách đạt được:**
>   Cơ chế Fixed Window (cửa sổ cố định) reset counter tại giây 00 của mỗi phút đồng hồ.
>   1. Tại giây `00:00:59` (giây cuối cùng của phút thứ nhất), người dùng bắn liên tiếp **10 request**. Vì trong phút thứ nhất chưa gửi request nào, cả 10 request này đều được hệ thống chấp nhận là hợp lệ.
>   2. Đúng 1 giây sau, khi đồng hồ chuyển sang `00:01:00` (giây đầu tiên của phút thứ hai), counter lập tức bị xóa về 0. Người dùng lại bắn tiếp **10 request** nữa. Cả 10 request này lại tiếp tục được chấp nhận vì nằm trong hạn mức của phút mới.
>   Kết quả: Trong khoảng thời gian chỉ vỏn vẹn 2 giây (từ 00:00:59 đến 00:01:00), hệ thống đã phải gánh tới 20 request — gấp đôi hạn mức tối đa cho phép trong một phút.
>   Ngược lại, Sliding Window (cửa sổ trượt) luôn xét chính xác khoảng thời gian 60 giây trôi ngược từ thời điểm hiện tại (`now - 60s`), do đó tại giây `00:01:00`, hệ thống thấy đã có 10 request trong 60 giây qua và sẽ chặn đứng ngay lập tức với mã HTTP 429.

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

> - **Khác biệt cốt lõi:**
>   + **Rate limit:** Quản lý tần suất theo thời gian ngắn (ví dụ: 10 request/phút) để bảo vệ **tính sẵn sàng kỹ thuật (availability & concurrency)** của hệ thống, chống DoS, chống quá tải server. Nó không quan tâm đến nội dung hay chi phí tài chính của request.
>   + **Cost guard:** Quản lý hạn mức tài chính tích lũy theo thời gian dài (ví dụ: 10.0 USD/tháng) để bảo vệ **ngân sách tài chính (financial budget)**, tránh rủi ro "hóa đơn sốc" khi tích hợp các mô hình LLM tính phí theo token.
>
> - **Tình huống Rate limit cho qua nhưng Cost guard chặn:**
>   Một người dùng đã sử dụng tích lũy $10.005 tiền API trong tháng (đã hết ngân sách $10.0). Hôm nay họ chỉ gửi đúng 1 request duy nhất với câu hỏi rất ngắn. Tần suất là 1 request/phút (rất nhỏ so với mức trần 10 request/phút), do đó Rate limiter cho qua. Tuy nhiên, Cost guard kiểm tra thấy tổng chi tiêu trong tháng đã vượt trần nên chặn lại và trả về HTTP `402 Payment Required`.
>
> - **Tình huống Cost guard cho qua nhưng Rate limit chặn:**
>   Một người dùng mới bắt đầu chu kỳ tháng, số dư chi tiêu hiện tại là $0.0. Người này dùng script chạy một vòng lặp gửi 15 request liên tục trong vòng 5 giây. Tổng chi phí của 15 request này ước tính chỉ khoảng $0.03 (còn rất xa mức trần $10.0), nên Cost guard hoàn toàn đồng ý cho phép. Tuy nhiên, Rate limiter phát hiện từ request thứ 11 trở đi đã vượt quá hạn mức 10 req/phút nên lập tức chặn lại và trả về HTTP `429 Too Many Requests` để tránh làm sập server.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

> Nếu gộp chung kiểm tra Redis vào liveness probe `/health`, chuỗi sự kiện thảm họa (cascading failure) sẽ diễn ra như sau:
> 1. **Redis gặp sự cố:** Mạng chập chờn hoặc Redis khởi động lại, mất kết nối trong 30 giây.
> 2. **Liveness check thất bại:** Bộ kiểm tra sức khỏe của nền tảng (Kubernetes/Docker/Railway) gọi định kỳ vào `/health` trên cả 3 container agent. Do phụ thuộc vào Redis, cả 3 container đều đồng loạt trả về HTTP 500/503.
> 3. **Orchestrator cưỡng chế restart:** Nền tảng điều phối suy diễn rằng cả 3 tiến trình agent đã rơi vào trạng thái bế tắc (deadlock) không thể tự phục hồi, và ra lệnh kill (SIGKILL) rồi khởi động lại đồng loạt cả 3 container.
> 4. **Vòng lặp CrashLoopBackOff:** Khi các container agent vừa khởi động lại, Redis vẫn chưa sẵn sàng (vì trong 30 giây sự cố). Endpoint `/health` lại fail ngay từ lúc startup, khiến container tiếp tục bị kill và restart lặp đi lặp lại.
> 5. **Downtime toàn diện và nghẽn hệ thống:** CPU và RAM của cụm máy chủ bị chiếm dụng tối đa cho việc khởi động lại liên tục. Kể cả khi Redis đã sống lại sau 30 giây, các container agent vẫn đang kẹt trong chu kỳ restart delay (backoff), khiến dịch vụ bị gián đoạn hoàn toàn thay vì chỉ tạm dừng điều phối traffic như khi tách biệt Readiness probe.

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

> - **Với kiến trúc Stateless lưu state trên Redis chung:**
>   Dù bộ cân bằng tải (Nginx/load balancer) phân phối các request tuần tự tới 3 container khác nhau (agent 1, agent 2, agent 3), trường `history_length` trong response vẫn tăng đều đặn và nhất quán: 0 -> 2 -> 4 -> 6 -> 8... vì tất cả instance đều truy xuất chung một nguồn dữ liệu duy nhất trong Redis.
>
> - **Nếu lịch sử lưu trong một dict Python nội bộ của process (Stateful):**
>   Mỗi process container sẽ sở hữu một dict riêng biệt trong RAM của nó. Khi load balancer phân phối theo cơ chế round-robin:
>   + Request 1 tới container A: `history_length` trả về 0 (A lưu câu 1).
>   + Request 2 tới container B: `history_length` trả về 0 (B chưa từng gặp user này, lưu câu 2).
>   + Request 3 tới container C: `history_length` trả về 0 (C cũng chưa từng gặp user này, lưu câu 3).
>   + Request 4 quay lại container A: `history_length` trả về 2 (thay vì 6, vì A chỉ biết câu 1).
>   Con số `history_length` sẽ nhảy lộn xộn, người dùng thấy agent liên tục bị "mất trí nhớ", không thể duy trì ngữ cảnh đàm thoại logic.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

> - **Lỗi gặp phải:** Endpoint `/ready` trả về HTTP 503 (`{"status":"not ready","redis":false}`) sau khi deploy service lên Railway, trong khi endpoint `/health` vẫn trả về 200 OK.
> - **Thông báo lỗi cụ thể:** Khi kiểm tra bằng curl:
>   `HTTP/1.1 503 Service Unavailable` kèm body `{"status":"not ready","redis":false}`.
>   Kiểm tra Deploy Logs trên Railway Dashboard thấy:
>   `redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379. Connection refused.`
> - **Cách tìm ra nguyên nhân:** Quan sát thấy `/health` 200 chứng tỏ Uvicorn và code Python đã chạy tốt. Lỗi chỉ nằm ở kết nối Redis trong `/ready`. Nhìn vào log `Connection refused to localhost:6379`, nhận ra ứng dụng đang fallback về giá trị mặc định của `REDIS_URL` trong `config.py` vì trên dashboard của Railway chưa cấu hình biến môi trường này. Trong Railway, Database Redis chạy ở một container/service hoàn toàn riêng biệt với private domain riêng, không thể gọi qua `localhost`.
> - **Cách sửa:** Trong Railway Project, vào service `day12-agent` -> chuyển sang tab **Variables** -> thêm biến `REDIS_URL` sử dụng tính năng **Add Reference** trỏ tới biến `${{Redis.REDIS_URL}}` của service Redis cùng project. Railway lập tức redeploy lại service với biến môi trường mới, sau đó `/ready` trả về 200 OK với `redis: true`.
