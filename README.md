# CDT_Engineer

> Bộ MCP servers cho các phần mềm kỹ thuật/CAD. Cho phép AI agent điều khiển & tự động hoá **AutoCAD**, **SketchUp**, **SolidWorks**, **Blender** (và mở rộng) qua giao diện **MCP (Model Context Protocol)** chuẩn.

## Ý tưởng cốt lõi

Biến AI thành **"kỹ sư CAD"** — đọc, tạo, sửa, kiểm tra bản vẽ & mô hình 3D. Mỗi phần mềm kỹ thuật là một **MCP server** nhỏ, tái dùng chung một **core** để giữ nhất quán và giảm trùng lặp.

## Cấu trúc (đang hình thành)

```
CDT_Engineer/
├── .gitignore          # chặn _private/ + secrets + artifacts
├── README.md
├── _private/           # riêng tư, KHÔNG commit (gitignored)
├── docs/               # tài liệu dự án (PLAN, ARCHITECTURE…)
└── servers/            # MCP servers, 1 thư mục / phần mềm
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
