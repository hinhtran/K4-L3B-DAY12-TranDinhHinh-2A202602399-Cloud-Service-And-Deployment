# CP5 — Triển khai Railway

Đây là phương án đang chọn cho bài. Cấu hình đã chuẩn bị, chưa có URL cloud
hoặc bằng chứng deploy thành công.

## 1. Tài khoản và repository

1. Đăng ký/đăng nhập https://railway.com bằng tài khoản của bạn.
2. Kết nối GitHub và cấp quyền đọc repository bài lab.
3. Review, commit và push code đã bổ sung lên GitHub. Railway build từ commit
   đã push, không đọc thay đổi chỉ có trên máy.
4. Kiểm tra `git ls-files .env` trả về rỗng. Không push secret.

Theo tài liệu Railway, trial có $5 credit tối đa 30 ngày, sau đó chuyển sang
Free với $1 credit/tháng. Kiểm tra quyền trial và Usage/Billing của tài khoản;
credit không bảo đảm chạy app và Redis liên tục miễn phí.

## 2. Tạo project, Redis và app

1. Tạo project rỗng (**New Project → Empty Project**, hoặc lựa chọn tương đương).
2. Trong project, chọn **New → Database → Redis**. Đợi Redis triển khai.
3. Thêm service từ **GitHub Repo**, chọn repository bài lab và nhánh đã push.
4. Mở service ứng dụng, cấu hình Variables theo bảng bên dưới. Nếu lần deploy
   đầu lỗi vì thiếu key, bổ sung Variables rồi deploy lại.
5. Để Root Directory là gốc repo. Railway dùng Dockerfile và `railway.toml`.
   Không cần Start Command riêng: CMD của Dockerfile đã đọc PORT và chạy Uvicorn.

`railway.toml` chỉ cấu hình service app; nó không tự tạo Redis. Hai service
phải ở cùng project/environment để dùng tham chiếu và mạng nội bộ.

## 3. Variables của service app

| Biến | Giá trị/nguồn |
|---|---|
| `AGENT_API_KEY` | Khóa riêng do bạn sinh và nhập trên dashboard |
| `REDIS_URL` | Reference tới `REDIS_URL` của service Redis |
| `RATE_LIMIT_PER_MINUTE` | `10` |
| `MONTHLY_BUDGET_USD` | `10.0` |
| `LOG_LEVEL` | `INFO` |

Sinh key trên máy:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Nếu service database tên chính xác là `Redis`, reference có dạng:

```text
${{Redis.REDIS_URL}}
```

Dùng gợi ý Reference Variable trong dashboard để chọn đúng tên service và biến.
Không dùng `localhost`, `fake://` hoặc URL Redis từ Compose. Không cần công khai
Redis ra Internet để app kết nối. Để platform cung cấp PORT; CMD có mặc định
8000 nếu PORT không được cung cấp.

## 4. Deploy và mở domain

1. Apply/deploy các thay đổi Variables nếu dashboard yêu cầu.
2. Xem Build Logs và Deploy Logs. Chờ service app hoạt động.
3. Vào **Settings → Networking → Public Networking → Generate Domain**.
4. Kiểm tra target port của domain khớp cổng Uvicorn ghi trong log.
5. Sao chép URL HTTPS Railway cấp, thử `/health` rồi `/ready`.

`/health` phải 200; `/ready` phải 200 với `redis=true`. Healthcheck Railway dùng
`/health` theo cấu hình bài lab; endpoint đó không chứng minh Redis hoạt động.

## 5. Kiểm tra và nộp CP5

```bash
source .venv/bin/activate
python scripts/check_deployment.py https://TEN-THAT.up.railway.app --rate-limit 10 --output screenshots/cp5-check.json
```

Thay bằng URL thật. Script hỏi key bằng đầu vào ẩn hoặc đọc `DEPLOY_API_KEY`
trong `.env`. Đây là AGENT_API_KEY trên service app, không phải Railway token.
Script kiểm tra health, readiness, 401 khi thiếu key, hỏi có key, lịch sử và 429.

Sau khi kiểm tra:

1. Điền `DEPLOYMENT.md`: thông tin học viên, repo, Public URL, platform Railway,
   ngày deploy, các biến đã xác nhận và output thực tế.
2. Xóa thông báo chưa deploy và các placeholder sau khi có thông tin thật.
3. Chụp `screenshots/dashboard.png` và `screenshots/health.png`, tránh lộ secret.
4. Đặt `DEPLOY_API_KEY` trong `.env` local để bật test có xác thực rồi chạy:

   ```bash
   python -m pytest tests/test_cp5.py -v
   python grade.py --no-bonus
   ```

## Chẩn đoán nhanh

| Lỗi | Cần kiểm tra |
|---|---|
| Startup báo thiếu key | AGENT_API_KEY phải đặt ở service app |
| Health 200, ready 503 | Reference REDIS_URL, database đã chạy, cùng environment |
| Domain trả 502 | Target port khớp PORT và bind `0.0.0.0` |
| Ask trả 401 dù có key | Key nhập có khớp key trên Railway không |
| Deploy hết tài nguyên/credit | Usage, trạng thái trial và giới hạn tài khoản |

## Nguồn chính thức

- https://docs.railway.com/config-as-code/reference
- https://docs.railway.com/databases/redis
- https://docs.railway.com/variables
- https://docs.railway.com/networking/domains/working-with-domains
- https://docs.railway.com/pricing/free-trial
