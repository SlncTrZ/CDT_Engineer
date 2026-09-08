# CDT_Engineer

> Bộ MCP servers cho các phần mềm kỹ thuật/CAD. Cho phép AI agent điều khiển & tự động hoá **AutoCAD**, **SketchUp**, **SolidWorks**, **Blender** (và mở rộng) qua giao diện **MCP (Model Context Protocol)** chuẩn.

## Ý tưởng cốt lõi

Biến AI thành **"kỹ sư CAD"** — đọc, tạo, sửa, kiểm tra bản vẽ & mô hình 3D. Mỗi phần mềm kỹ thuật là một **MCP server** (1 provider riêng), tái dùng chung một **core** để giữ nhất quán và giảm trùng lặp.

## Chuẩn tuân thủ (bắt buộc)

Mọi MCP server trong CDT_Engineer **PHẢI** tuân thủ [`MCP_PROVIDER_STANDARD.md`](MCP_PROVIDER_STANDARD.md) — SlncTrZ-MCP Provider Standard. Tóm tắt:

- MCP qua **Streamable HTTP** tại `/mcp`
- Auth: `Authorization: Bearer <token>` (primary) + tuỳ chọn `X-API-Key`
- **Tool `help` bắt buộc** — read-only, self-describing (provider first-class)
- Provider ID / namespace chuẩn: `<provider>.<tool>`
- Lỗi cấu trúc · versioning tách biệt (software vs contract) · security baseline · không lộ secret

## Cấu trúc (đang hình thành)

```
CDT_Engineer/
├── .gitignore          # chặn _private/ + secrets + artifacts
├── README.md
├── MCP_PROVIDER_STANDARD.md  # SlncTrZ-MCP Provider Standard (BẮT BUỘC tuân thủ)
├── _private/           # riêng tư, KHÔNG commit (gitignored)
├── docs/               # tài liệu dự án (PLAN, ARCHITECTURE…)
└── servers/            # MCP providers, 1 thư mục / phần mềm
    ├── core/           # scaffolding chung
    ├── autocad/
    ├── sketchup/
    ├── solidworks/
    └── blender/
```

## Trạng thái

🚧 **Mới khởi tạo.** Đang ở Phase 0 — khung core + target đầu tiên (Blender). Xem [`docs/PLAN.md`](docs/PLAN.md) cho lộ trình.

---
*Wing: ops | Topic: CDT_Engineer | Updated: 2026-09-08*
