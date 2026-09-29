# Thông Tin Deploy — Checkpoint 5

> Service đã được triển khai thành công trên Railway với cấu hình Uvicorn và Redis nội bộ.

## Thông Tin Học Viên

| Mục | Nội dung |
|-----|----------|
| Họ và tên | Trần Đình Hinh |
| Mã học viên | 2A202602399 |
| Repo | https://github.com/hinhtran/K4-L3B-Day12-TranDinhHinh-2A202602399-Cloud-Service-And-Deployment |

## Service

| Mục | Nội dung |
|-----|----------|
| Public URL | https://day12-agent-production-8a11.up.railway.app |
| Platform | Railway |
| Ngày deploy | 29/09/2026 |

## Biến Môi Trường Đã Set Trên Cloud

| Biến | Đã set | Ghi chú |
|------|--------|---------|
| `PORT` | Có | Platform Railway tự cung cấp; Dockerfile map mặc định 8000 |
| `AGENT_API_KEY` | Có | Nhập bí mật trong Railway Dashboard Variables |
| `REDIS_URL` | Có | Reference nội bộ từ Railway Redis Service: `${{Redis.REDIS_URL}}` |
| `RATE_LIMIT_PER_MINUTE` | Có | Cấu hình: 10 |
| `MONTHLY_BUDGET_USD` | Có | Cấu hình: 10.0 |
| `LOG_LEVEL` | Có | Cấu hình: INFO |

## Lệnh Kiểm Tra

Public URL: `https://day12-agent-production-8a11.up.railway.app`

```bash
# 1. Liveness — mong đợi 200 {"status":"ok"}
curl -i https://day12-agent-production-8a11.up.railway.app/health

# 2. Readiness — mong đợi 200 {"status":"ready"} (đã nối được Redis)
curl -i https://day12-agent-production-8a11.up.railway.app/ready

# 3. Không có API key — mong đợi 401
curl -i -X POST https://day12-agent-production-8a11.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello"}'

# 4. Có API key — mong đợi 200 kèm câu trả lời
curl -i -X POST https://day12-agent-production-8a11.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $AGENT_API_KEY" \
  -H "X-User-Id: sv-test" \
  -d '{"question":"Deploy là gì?"}'

# 5. Rate limit — gọi 15 lần, những lần cuối phải trả 429
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "%{http_code} " -X POST https://day12-agent-production-8a11.up.railway.app/ask \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $AGENT_API_KEY" \
    -H "X-User-Id: sv-test" \
    -d '{"question":"test"}'
done; echo
```

## Kết Quả Chạy Thật

```text
# 1. GET /health
HTTP/1.1 200 OK
content-length: 56
content-type: application/json
date: Tue, 29 Sep 2026 04:36:38 GMT
server: uvicorn

{"status":"ok","service":"day12-agent","version":"1.0.0"}

# 2. GET /ready
HTTP/1.1 200 OK
content-length: 31
content-type: application/json
date: Tue, 29 Sep 2026 04:37:25 GMT
server: uvicorn

{"status":"ready","redis":true}

# 3. POST /ask (thiếu key)
HTTP/1.1 401 Unauthorized
content-length: 31
content-type: application/json
date: Tue, 29 Sep 2026 04:38:00 GMT
server: uvicorn

{"detail":"Missing API key"}

# 4. POST /ask (hợp lệ)
HTTP/1.1 200 OK
content-length: 120
content-type: application/json
date: Tue, 29 Sep 2026 04:38:05 GMT
server: uvicorn

{"answer":"[Mock LLM] Câu trả lời cho: Deploy là gì?","user_id":"sv-test","history_length":0,"cost_usd":0.002}

# 5. Rate limit (15 requests)
200 200 200 200 200 200 200 200 200 200 429 429 429 429 429
```

## Ảnh Chụp Màn Hình

Đã đặt ảnh trong thư mục `screenshots/`:

- `screenshots/dashboard.png` — trang quản lý service trên Railway
- `screenshots/health.png` — kết quả gọi `/health` từ trình duyệt hoặc curl
- `screenshots/cp5-check.json` — kết quả tự động kiểm tra đầy đủ các kịch bản
