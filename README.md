# CDT_Engineer

> Bộ MCP providers cho phần mềm kỹ thuật/CAD, cho phép AI agent đọc, tạo, sửa, kiểm tra và tự động hoá mô hình/bản vẽ qua MCP chuẩn.

## Mục tiêu

Biến AI thành một **kỹ sư CAD đa nền tảng** nhưng không ép mọi phần mềm vào cùng một tập lệnh nghèo nàn. CDT_Engineer dùng kiến trúc phân tầng:

1. **SlncTrZ Provider Contract** — transport, auth, help, namespace, error, versioning, security.
2. **CDT Common CAD Contract** — semantics thật sự dùng chung giữa các phần mềm CAD/DCC.
3. **Provider Extension Contract** — khả năng riêng của AutoCAD, SketchUp, Blender, SolidWorks…
4. **Backend/Engine** — cách thực thi cụ thể: COM, ezdxf, Ruby API, bpy, SolidWorks COM…

Chi tiết: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) và [`docs/CONTRACTS.md`](docs/CONTRACTS.md).

## Thứ tự triển khai chính thức

| Thứ tự | Provider | Mục tiêu chính |
| ---: | --- | --- |
| 1 | **AutoCAD** | 2D/3D drafting, DWG/DXF, layout, block, dimension; dual-engine COM + ezdxf |
| 2 | **SketchUp** | Concept/modeling kiến trúc, groups/components, tags, materials, scenes |
| 3 | **Blender** | **Modeling + Sculpting** là capability hạng nhất; thêm scene/material/render |
| 4 | **SolidWorks** | Parametric mechanical CAD: sketches, features, parts, assemblies, mates, drawings |

AutoCAD là **reference provider đầu tiên** để chứng minh common contract và SlncTrZ compliance trước khi extract phần reusable vào `servers/core/`.

## Cấu trúc dự kiến

```text
CDT_Engineer/
├── README.md
├── MCP_PROVIDER_STANDARD.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CONTRACTS.md
│   ├── PLAN.md
│   ├── PLAN_AUTOCAD.md
│   ├── PLAN_SKETCHUP.md
│   ├── PLAN_BLENDER.md
│   └── PLAN_SOLIDWORKS.md
├── servers/
│   ├── core/          # chỉ extract sau khi có >=2 provider chứng minh reuse
│   ├── autocad/
│   ├── sketchup/
│   ├── blender/
│   └── solidworks/
└── _private/
    └── reference/     # repo tham khảo, gitignored
```

## Nguyên tắc bắt buộc

- Mọi provider first-class phải tuân thủ [`MCP_PROVIDER_STANDARD.md`](MCP_PROVIDER_STANDARD.md).
- Provider expose **bare MCP tool names**; SlncTrZ-MCP sở hữu namespace canonical `<provider>.<tool>`.
- Common contract chỉ chứa semantics thực sự chung; không tạo lowest-common-denominator giả tạo.
- Khả năng riêng phải được khai báo qua capability map và refusal có cấu trúc khi engine không hỗ trợ.
- Provider sở hữu business logic; gateway không chứa CAD logic.
- Mặc định fail closed, validate trước side effect, timeout bounded, không lộ secret.
- Không ghi đè file gốc mặc định; destructive operations phải tách riêng và có semantics rõ ràng.
- **Reuse-first:** học từ reference code, test và edge cases đã được chứng minh; chuẩn hoá lại theo CDT/SlncTrZ thay vì copy nguyên monolith.
- Code từ reference chỉ được tái sử dụng trực tiếp khi license cho phép và attribution được giữ đúng. Reference chưa xác minh license chỉ dùng để học pattern/behavior, không copy code.

## Trạng thái

✅ **AutoCAD A1 headless production baseline đã triển khai và kiểm chứng** (`cdt-autocad-provider 0.2.0`, contract `autocad-a1-v1`): 42 MCP tools, DXF lifecycle, object transforms/properties, blocks, layouts, linear/aligned dimensions, hatch, audit/purge, compressed transaction + undo/redo, optional PDF export, capability honesty, path containment, timeout quarantine và HTTP `/mcp` Bearer auth đều qua gate. SketchUp/Blender/SolidWorks chưa triển khai runtime. AutoCAD **A2 COM/live AutoCAD** là bước kế tiếp.

---
*Wing: ops | Topic: CDT_Engineer | Updated: 2026-09-09*
