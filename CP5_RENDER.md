# CP5 — Triển khai lên Render và kiểm chứng

> Hiện đã chọn Railway: làm theo [CP5_RAILWAY.md](CP5_RAILWAY.md).
> Tài liệu Render này được giữ làm phương án thay thế.

## Trạng thái

Repo đã có cấu hình và script kiểm tra. Chưa tạo tài nguyên Render, chưa có
Public URL và chưa có kết quả kiểm thử cloud. Không xem tài liệu này là bằng
chứng đã deploy thành công.

## 1. Chuẩn bị repo và tài khoản

1. Đăng ký/đăng nhập tại https://dashboard.render.com bằng tài khoản của bạn.
2. Kết nối GitHub và cấp quyền cho đúng repository bài lab.
3. Kiểm tra tên repo theo `SUBMISSION.md`; repo bài nộp cần public.
4. Commit và push những thay đổi đã review, đặc biệt `app/`, `utils/`,
   `requirements.txt`, `Dockerfile`, `.dockerignore`, `render.yaml`.
5. Không đưa `.env` lên GitHub. Kiểm tra bằng `git ls-files .env`: kết quả cần rỗng.

Render build từ commit trên GitHub, không đọc file chưa push trong máy bạn.
Nếu đổi tên repository trên GitHub, cập nhật remote local tương ứng; việc đổi
này không tự làm mất commit history.

## 2. Tạo Blueprint

1. Chọn **New → Blueprint** trong Render Dashboard.
2. Chọn repo và nhánh chứa code vừa push (thường là `main`).
3. Dùng file `render.yaml` ở thư mục gốc.
4. Xem lại hai tài nguyên: `day12-agent` (Docker web service) và
   `day12-redis` (Key Value), cùng khu vực Singapore và plan Free.
5. Khi được hỏi `AGENT_API_KEY`, nhập khóa riêng. Có thể sinh trên máy bằng:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

6. Bấm tạo/deploy Blueprint. Chờ cả Key Value và web service hoạt động.
7. Mở web service, lấy URL `.onrender.com` Render thực tế cấp.

Không dùng tên miền ví dụ làm Public URL. Nếu tài khoản đã có một Key Value
Free, cần dùng instance hiện có hoặc xử lý giới hạn đó trước khi tạo Blueprint;
không tự chuyển sang gói trả phí.

Nếu Blueprint báo trường không hợp lệ, xem thông báo cụ thể và đối chiếu
schema chính thức (link cuối tài liệu). Không xóa cấu hình bảo mật để né lỗi.

## 3. Cấu hình này làm gì?

| Trường | Ý nghĩa |
|---|---|
| `runtime: docker` | Build bằng Dockerfile của repo |
| `region: singapore` | App và Redis cùng khu vực để liên lạc nội bộ |
| `healthCheckPath: /health` | Kiểm tra tiến trình app, độc lập với Redis |
| `AGENT_API_KEY` / `sync: false` | Nhập secret trên dashboard khi tạo Blueprint |
| `REDIS_URL` / `fromService` | Render lấy connection string của Key Value |
| `type: keyvalue` | Tên loại dịch vụ hiện hành; giao thức tương thích Redis |
| `ipAllowList: []` | Redis không mở truy cập từ Internet |
| `maxmemoryPolicy: noeviction` | Đầy bộ nhớ thì không tự loại key ngân sách/limiter |

`noeviction` có nghĩa là khi đầy bộ nhớ, lệnh ghi có thể thất bại. Nó tránh việc
âm thầm xóa bộ đếm chi phí, nhưng không thay thế giám sát dung lượng.

Dockerfile chạy Uvicorn trên `0.0.0.0`, đọc `PORT` và dùng `exec` để nhận signal.
Không đặt Start Command riêng khi dùng Dockerfile này. Không đặt
`REDIS_URL=fake://` trên cloud.

`/health` 200 chưa chứng minh Redis hoạt động: luôn kiểm tra thêm `/ready`.
Render health check ở đây vẫn dùng `/health` theo bài lab; `/ready` không tự trở
thành probe của platform chỉ vì API có endpoint đó.

## 4. Kiểm tra và lưu kết quả

Từ terminal ở gốc repo, bật môi trường đã cài dependencies:

```bash
source .venv/bin/activate
python scripts/check_deployment.py https://TEN-DICH-VU-THAT.onrender.com --rate-limit 10 --output screenshots/cp5-check.json
```

Thay URL bằng URL thật. Script hỏi key bằng đầu vào ẩn; hoặc đọc `DEPLOY_API_KEY`
trong `.env`. Đây là key bảo vệ `/ask` bạn nhập ở bước tạo service, **không phải**
Render API token. Script không ghi key, header hoặc nội dung hội thoại vào báo cáo.

Các kiểm tra gồm:

- `/health`: HTTP 200 và `status=ok`.
- `/ready`: HTTP 200, `status=ready`, `redis=true`.
- `/ask` không key: HTTP 401.
- `/ask` có key: HTTP 200 và answer.
- Hai lượt cùng user: history_length lần lượt 0 và 2.
- Với `--rate-limit 10`: 10 lần cho qua, lần 11 trả 429, trên user mới.

Giá trị `--rate-limit` phải bằng cấu hình trên cloud. Kiểm tra rate limit chỉ có
ý nghĩa khi các lượt hoàn thành trong cửa sổ 60 giây. Script dùng user riêng
cho mỗi lần chạy để giảm ảnh hưởng từ dữ liệu kiểm thử trước đó.

Chỉ kiểm tra đường public, không nhập key:

```bash
python scripts/check_deployment.py https://TEN-DICH-VU-THAT.onrender.com --public-only
```

Chế độ này không xác nhận chức năng có xác thực, history hay rate limit.
Mã thoát 0 nghĩa là các kiểm tra đã chạy đều đạt, không phải tất cả yêu cầu nộp
bài đã hoàn thành. Báo cáo JSON cũng không thay thế hai ảnh chụp được yêu cầu.

## 5. Hoàn thiện bài nộp

1. Điền họ tên, mã học viên, repo, URL thật, platform Render và ngày deploy vào
   `DEPLOYMENT.md`.
2. Chỉ đánh dấu biến môi trường đã set sau khi kiểm tra dashboard.
3. Dán output thực tế của script/curl vào mục kết quả. Không dán secret.
4. Chụp dashboard vào `screenshots/dashboard.png`, che secret nếu có.
5. Chụp `/health` đang hoạt động vào `screenshots/health.png`.
6. Xóa phần fallback nếu không dùng. Hoàn thiện mọi placeholder còn lại.
7. Chạy:

   ```bash
   python -m pytest tests/test_cp5.py -v
   python grade.py --no-bonus
   ```

`DEPLOY_API_KEY` trong `.env` giúp test CP5 chính thức chạy thêm đường có xác
thực. `--no-bonus` chỉ bỏ bonus, vẫn gọi URL cloud của CP5.

## 6. Chẩn đoán lỗi

| Hiện tượng | Kiểm tra |
|---|---|
| Build fail | Build logs, đúng nhánh/commit, requirements và Dockerfile đã push |
| App dừng lúc startup | Runtime logs, đã nhập `AGENT_API_KEY` chưa |
| Healthcheck fail | Runtime logs, Uvicorn bind `0.0.0.0`, cổng khớp `PORT` |
| `/health` 200, `/ready` 503 | Key Value đã chạy chưa, REDIS_URL lấy đúng service/cùng region chưa |
| Có key nhưng `/ask` 401 | Key local có khớp AGENT_API_KEY trên Render không |
| `/ask` 429 | Hết hạn mức user; đợi cửa sổ trượt hoặc dùng user kiểm thử mới |
| Request đầu chậm | Free web service có thể đang khởi động lại sau thời gian không hoạt động |

Ghi lại lỗi thật và cách xử lý cho câu 10 của `exercises.md`.

## 7. Giới hạn Free và nguồn đối chiếu

Render Free phù hợp bài lab. Free Key Value chỉ có một instance mỗi workspace
và mất dữ liệu khi restart: history, rate limit và tổng chi phí có thể bị reset.
Ứng dụng stateless không đồng nghĩa kho dữ liệu Free đã bền vững.

Nguồn chính thức đã đối chiếu khi chuẩn bị cấu hình:

- https://render.com/docs/blueprint-spec
- https://render.com/docs/free
- https://render.com/docs/key-value
- https://render.com/docs/health-checks
