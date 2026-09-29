# Chạy bản đã bổ sung

## Chạy Python

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Điền khóa vừa sinh vào `AGENT_API_KEY` trong `.env`. Nếu chưa có Redis,
đặt `REDIS_URL=fake://` để thử trên một process. Không commit `.env`.

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Mở `http://localhost:8000/docs` để thử `/health`, `/ready` và `/ask`.
Với `/ask`, nhập `X-API-Key` khớp `.env` và `X-User-Id` bạn muốn thử.

## Chạy Docker

```bash
docker compose up --build -d
docker compose logs -f agent
```

Compose dùng Redis thật, cổng API là `8000`. Cấu hình này chạy một agent;
để scale nhiều replica cần bỏ mapping host `8000:8000` khỏi agent và đặt
load balancer phía trước, tránh tranh chấp cổng.

Bản Dockerfile ban đầu được giữ ở `Dockerfile.single-stage` để đo dung lượng
cho câu 3 trong `exercises.md`:

```bash
docker build -f Dockerfile.single-stage -t agent:single .
docker build -t agent:multi .
docker images --filter reference='agent:*'
```

## Kiểm thử

CP5 đang chọn Railway: xem [CP5_RAILWAY.md](CP5_RAILWAY.md) để tạo tài khoản,
thêm Redis, deploy app và chạy `scripts/check_deployment.py` với URL thật.

```bash
python -m pytest tests/test_cp1.py tests/test_cp2.py tests/test_cp3.py tests/test_cp4.py -v
```

Test Docker sẽ skip nếu Docker chưa chạy. CP5 cần URL triển khai thật trong
`DEPLOYMENT.md`; bonus cần workflow riêng. Chưa có hai phần này thì chạy toàn
bộ `tests/` vẫn có lỗi tương ứng.

## Giới hạn của bản lab

- `X-User-Id` do client gửi; API key chung chưa phải hệ thống định danh từng user.
- Rate limiter theo các bước của lab chưa bảo đảm atomic khi nhiều request đồng thời.
- Cost guard kiểm tra số đã tiêu trước khi gọi LLM, chưa dự toán/giữ ngân sách cho
  request đang chạy, nên chưa bảo đảm trần chi phí tuyệt đối.
- `fake://` không chia sẻ state giữa process và mất dữ liệu khi restart.
- Điền bài phản ánh, URL cloud và ảnh bằng kết quả thực tế sau khi chạy.
