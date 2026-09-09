# CDT_Engineer

> Architecture/specification hub cho họ MCP provider kỹ thuật/CAD, cho phép AI agent đọc, tạo, sửa, kiểm tra và tự động hoá mô hình/bản vẽ qua MCP chuẩn.

## Mục tiêu

Biến AI thành một **kỹ sư CAD đa nền tảng** nhưng không ép mọi phần mềm vào cùng một tập lệnh nghèo nàn. CDT_Engineer dùng kiến trúc phân tầng:

1. **SlncTrZ Provider Contract** — transport, auth, help, namespace, error, versioning, security.
2. **CDT Common CAD Contract** — semantics thật sự dùng chung giữa các phần mềm CAD/DCC.
3. **Provider Extension Contract** — khả năng riêng của AutoCAD, SketchUp, Blender, SolidWorks…
4. **Backend/Engine** — cách thực thi cụ thể: COM, ezdxf, Ruby API, bpy, SolidWorks COM…

Chi tiết: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) và [`docs/CONTRACTS.md`](docs/CONTRACTS.md).

## Triển khai chính thức — 4 lane song song

| Lane | Target repo | Mục tiêu chính |
| --- | --- | --- |
| A | **CDT-AutoCAD** | 2D/3D drafting, DWG/DXF, layout, block, dimension; dual-engine COM + ezdxf |
| S | **CDT-SketchUp** | Concept/modeling kiến trúc, groups/components, tags, materials, scenes |
| B | **CDT-Blender** | **Modeling + Sculpting** là capability hạng nhất; thêm scene/material/render |
| W | **CDT-SolidWorks** | Parametric mechanical CAD: sketches, features, parts, assemblies, mates, drawings |

Bốn provider phát triển độc lập và song song theo native capability. `CDT_Engineer` giữ architecture/contracts/roadmap/conformance. AutoCAD được migration trước vì runtime đã tồn tại; không phải dependency chặn ba lane còn lại. Xem [`docs/REPO_SPLIT_PLAN.md`](docs/REPO_SPLIT_PLAN.md).

## Repository topology

```text
CDT_Engineer/       # architecture / contracts / ADR / roadmap / conformance
CDT-AutoCAD/        # runtime product
CDT-SketchUp/       # runtime product
CDT-Blender/        # runtime product
CDT-SolidWorks/     # runtime product
CDT-Provider-Kit/   # CHƯA TẠO; chỉ sau Rule-of-Two evidence
```

Repository split đã hoàn tất: runtime AutoCAD ở `CDT-AutoCAD`; SketchUp/Blender/SolidWorks có skeleton độc lập và pinned spec baseline. `CDT_Engineer` không chứa provider runtime business logic. Không dùng Git submodule để ghép source provider. Repo map canonical: [`docs/PROVIDER_REPO_MAP.md`](docs/PROVIDER_REPO_MAP.md).

## Nguyên tắc bắt buộc

- Mọi provider first-class phải tuân thủ [`MCP_PROVIDER_STANDARD.md`](MCP_PROVIDER_STANDARD.md).
- Provider expose **bare MCP tool names**; SlncTrZ-MCP sở hữu namespace canonical `<provider>.<tool>`.
- Common contract chỉ chứa semantics thực sự chung; không tạo lowest-common-denominator giả tạo.
- Provider repositories version/release/CI độc lập; không provider nào import runtime code trực tiếp từ provider khác.
- Khả năng riêng phải được khai báo qua capability map và refusal có cấu trúc khi engine không hỗ trợ.
- Provider sở hữu business logic; gateway không chứa CAD logic.
- Mặc định fail closed, validate trước side effect, timeout bounded, không lộ secret.
- Không ghi đè file gốc mặc định; destructive operations phải tách riêng và có semantics rõ ràng.
- **Reuse-first:** học từ reference code, test và edge cases đã được chứng minh; chuẩn hoá lại theo CDT/SlncTrZ thay vì copy nguyên monolith.
- Code từ reference chỉ được tái sử dụng trực tiếp khi license cho phép và attribution được giữ đúng. Reference chưa xác minh license chỉ dùng để học pattern/behavior, không copy code.

## Trạng thái

✅ **Repository split hoàn tất và 4 lane đã agent-ready.** AutoCAD được tách history-preserving sang `CDT-AutoCAD` và giữ nguyên generic regression `54 passed, 2 skipped`; A2 COM/live vẫn là RC `0.3.0rc1 / autocad-a2-v1-rc1`, A3.1 ACIS vẫn staged cho tới khi có AutoCAD thật. `CDT-SketchUp`, `CDT-Blender`, `CDT-SolidWorks` đã có repo độc lập, ownership `AGENTS.md`, pinned specs và initial handoff; chưa claim runtime capability.

---
*Wing: ops | Topic: CDT_Engineer | Updated: 2026-09-09*
