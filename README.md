# CDT_Engineer — Engineering OS for Agents

CDT_Engineer là **Engineering Operating System / Virtual Engineering Office cho AI Agents**: một đầu mối nghiệp vụ để Agent hiểu mục đích dự án, chọn đúng chuyên ngành/role, áp dụng skill và quy chuẩn kỹ thuật, dùng đúng phần mềm, kiểm tra độc lập và bàn giao hồ sơ có thể truy vết.

Mục tiêu không phải chỉ làm ra geometry hoặc hình ảnh đẹp. CDT_Engineer phải giúp Agent tạo đúng loại sản phẩm cho mục đích thực tế: concept, thiết kế kỹ thuật, chế tạo, thi công, shop drawing, hồ sơ hạ tầng, mô hình 3D hay render — với mức kiểm chứng phù hợp cho từng release class.

## Mô hình

```text
Yêu cầu / nguồn đầu vào
→ Step 0: Execution Environment Discovery
→ Design Basis
→ Engineering Roles + Skills + Standards
→ Workflow đa ngành
→ Capability preflight
→ CDT-AutoCAD / CDT-SketchUp / CDT-Blender / CDT-SolidWorks
→ QA / Checker độc lập
→ Artifact seal + handoff
→ ready_for_professional_review
```

CDT_Engineer không chứa native COM/Ruby/bpy/SolidWorks backend. Các repository engine vẫn là Generic Execution Engines; CDT_Engineer chứa **chuyên môn kỹ sư và phương pháp làm việc**.

## Golden verticals đầu tiên

| Vertical | Vai trò trong roadmap |
| --- | --- |
| [Site / Landscape / Architectural Base Reconstruction](domains/site-reconstruction/benchmark-pack.md) | BeachSquare chứng minh source/elevation/registration/2D→3D/SketchUp và QA workflow |
| [Mechanical Part Reconstruction](domains/mechanical-reconstruction/benchmark-pack.md) | Chứng minh đọc bản vẽ, feature/dimension/tolerance, manufacturability và shop/neutral outputs |

Hai vertical này là bằng chứng đầu tiên để xây OS; không giới hạn sản phẩm ở hai ngành đó.

Roadmap đích mở rộng tới Architecture, Interior, Landscape, Civil/Infrastructure, Structural, Mechanical/Manufacturing, Electrical, Electronics, Embedded và Visualization/Rendering.

## Contract nền

- [Execution Environment Contract](docs/EXECUTION_ENVIRONMENT_CONTRACT.md)
- [Agent Operational Profile Contract](docs/AGENT_PROFILE_CONTRACT.md)
- [Design Basis Contract](docs/DESIGN_BASIS_CONTRACT.md)
- [Engineering Skill Contract](docs/ENGINEERING_SKILL_CONTRACT.md)
- [Engineering Role Contract](docs/ROLE_CONTRACT.md)
- [Workflow Contract](docs/WORKFLOW_CONTRACT.md)
- [Feature-based Chunk Streaming Contract](docs/FEATURE_CHUNK_STREAMING_CONTRACT.md)
- [Software Operating Guide Contract](docs/SOFTWARE_OPERATING_GUIDE_CONTRACT.md)
  - [AutoCAD Operating Guide](software/autocad/OPERATING_GUIDE.md)
  - [SketchUp Operating Guide](software/sketchup/OPERATING_GUIDE.md)
  - [SolidWorks Operating Guide](software/solidworks/OPERATING_GUIDE.md)
- [QA / Checker Model](docs/QA_CHECKER_MODEL.md)
- [Foundation Validation](docs/FOUNDATION_VALIDATION.md)
- [Production Domain Contract](docs/PRODUCTION_DOMAIN_CONTRACT.md)
- [Standards Governance & Registry](docs/STANDARDS_GOVERNANCE.md)

## Ranh giới sản phẩm

- **CDT_Engineer:** Design Basis, domain interpretation, roles, Engineering Skills, deterministic engineering algorithms, standards/rules, professional software guidance, workflows, QA/QC và engineering handoff.
- **CDT-AutoCAD / CDT-SketchUp / CDT-Blender / CDT-SolidWorks:** native execution, query/mutation, geometry/topology, document lifecycle, transaction/recovery, import/export và capability declaration.
- **SlncTrZ-MCP:** authority, routing, namespace và connection surface; không sở hữu engineering business logic.
- **Domain SDK** khác **CDT-Provider-Kit** và đều phải qua Rule of Two riêng.

## Nguyên tắc nghề nghiệp

- Step 0 phải discover software/version/path và provider/runtime capability trước mọi hướng dẫn version-specific hoặc native execution; không giả định môi trường.
- Purpose và Design Basis phải có trước software choice.
- `unknown` phải được giữ là unknown; không bịa kích thước, tolerance, cao độ, tải, vật liệu hay compliance.
- Tool chạy thành công không đồng nghĩa thiết kế đúng.
- Mutation-heavy work phải dùng **Feature-based Chunk Streaming**: không bắn cả dự án trong một call, cũng không stream từng LINE/ARC/primitive qua từng Agent turn; chia theo semantic feature, commit/verify từng chunk, rồi mới mở dependency tiếp theo.
- `ui_yield`/redraw/cursor-visible progress chỉ tạo presentation effect tại safe committed boundary; không được làm yếu transaction, recovery hay QA.
- Render đẹp không đồng nghĩa chế tạo/thi công được.
- Bản vẽ dành cho con người phải được kiểm view/section/dimension/note/revision/readability, không chỉ dữ liệu máy.
- Compliance cần exact standard edition + applicability + derived rule + evidence.
- QA độc lập và artifact identity là hard requirement cho release mạnh.
- CDT_Engineer chuẩn bị hồ sơ `ready_for_professional_review`; quyền ký/phát hành chuyên môn vẫn là hành động chịu trách nhiệm bên ngoài hệ thống.

## Trạng thái

Ngày 2026-09-12: Engineering OS offline foundation đã có Step-0, Agent Profiles, deterministic Site/Mechanical guards, Rule-of-Two primitives, Stage Runner, QA/artifact identity và Software Operating Guides. AutoCAD integration đã được đồng bộ với public contract `0.4.0rc1 / autocad-generic-v1-rc1 / 86 tools`; SketchUp integration đồng bộ với provider `0.1.0`, contract `0.21`, 64 tools và native save/open/export hiện hành. Stage Runner giữ capability facts theo software, chọn một software candidate cho toàn bộ software-bound requirements của stage, không trộn capability giữa nhiều engine và không cho global fact bypass blocker của engine. Release-critical source/artifact hash, reopen và round-trip evidence đã được đưa thành machine-required profile gates thay vì chỉ nằm trong prose. Public test suite đứng độc lập, không đọc customer/raw fixture trong `_private/`. Native/runtime acceptance vẫn phải qua Step-0 và evidence thực tế.

Public repository chỉ giữ product-facing contracts, rules, skills/guides/workflows và benchmark definitions đã sanitize. Mọi tài liệu nghiên cứu, phát triển, roadmap, ADR/định hướng dự án, handoff nội bộ, customer/source CAD, raw evidence, protected references và run workspaces nằm trong `_private/`; không force-add dữ liệu private.
