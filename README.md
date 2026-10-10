# CDT_Engineer — Engineering OS for Agents

> Documentation class: PUBLIC_ENTRYPOINT

CDT_Engineer tổ chức công việc kỹ thuật cho Agent: Design Basis, domain/skill,
tiêu chuẩn, workflow, kiểm tra độc lập và bằng chứng bàn giao.
Native CAD/DCC execution do các CDT-* providers đảm nhiệm.

Provider `0.1.1` · Contract `cdt-engineer-v1-alpha7` · 19 MCP tools.

## Bắt đầu

```bash
python -m pip install .
cdt-engineer
```

Thiết lập transport/auth theo [Provider Standard](MCP_PROVIDER_STANDARD.md).
Gọi `help`, `system_status` và `system_capabilities` để xác minh contract/runtime.
[MCP Tool Guide](docs/TOOL_GUIDE.md) mô tả inputs và giới hạn.

## Quy trình

1. Agent chọn host, thu thập observations và giải quyết prerequisites.
2. Xác lập Design Basis, release class, nguồn và tiêu chuẩn áp dụng.
3. Chọn domain/role/skill, giải quyết dependency trước native primitives.
4. Discover executor capabilities; thực hiện từng semantic feature chunk.
5. Read-after-write, recovery, Checker độc lập và artifact identity trước bàn giao.

`execution_environment_assess` chỉ đánh giá snapshot do caller cung cấp.
Provider không SSH/start/stop ứng dụng, proxy native calls hoặc tự orchestration
các executor. Xem [environment contract](docs/EXECUTION_ENVIRONMENT_CONTRACT.md)
và [lifecycle ownership](docs/EXECUTION_LIFECYCLE_CONTRACT.md).

## Tài liệu và packages

- [Kiến trúc chuẩn](docs/ARCHITECTURE.md).
- [Bản đồ contract và package](docs/README.md).
- [Chính sách tài liệu](docs/DOCUMENTATION_POLICY.md).
- [Quy tắc version phát hành nhóm CDT](docs/CDT_GROUP_VERSIONING_POLICY.md).
- [Cài đặt, phát hành và rollback](docs/RELEASE_AND_DEPLOYMENT.md).
- [Contributor validation](docs/FOUNDATION_VALIDATION.md).

Domains, skills, catalogs và software guides là thành phần sản phẩm.
Scope/lifecycle của từng package quyết định mức sử dụng; sự tồn tại của package
không chứng minh native production acceptance.

## Giới hạn

Giữ `unknown` là unknown; thiếu nguồn, skill, tiêu chuẩn, capability hoặc bằng
chứng phải BLOCK hoặc giảm scope rõ ràng. Tool/runtime PASS và render đẹp không
thay domain correctness, completeness hoặc independent QA.
Kết quả cao nhất của hệ thống là `ready_for_professional_review`;
phê duyệt pháp lý/chuyên môn thuộc người có thẩm quyền.
