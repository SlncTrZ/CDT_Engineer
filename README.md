# CDT_Engineer — Engineering OS for Agents

> Documentation class: PUBLIC_ENTRYPOINT

CDT_Engineer là **Engineering Operating System / Virtual Engineering Office cho AI Agents**. Nó giúp Agent chuyển yêu cầu và nguồn đầu vào thành một quy trình kỹ thuật có trách nhiệm: xác lập Design Basis, chọn đúng chuyên ngành/role, áp dụng Engineering Skills và standards, giải quyết dependencies, dùng đúng phần mềm, kiểm tra độc lập và bàn giao artifact có thể truy vết.

Mục tiêu không phải chỉ tạo geometry hoặc hình ảnh đẹp. CDT_Engineer phải giúp Agent tạo **đúng loại sản phẩm kỹ thuật cho đúng mục đích và đúng release class**, đồng thời biết khi nào bằng chứng chưa đủ để tiếp tục.

## Mô hình sản phẩm

```text
Yêu cầu / nguồn đầu vào
→ Step 0: Execution Environment Discovery
→ Design Basis
→ Engineering Roles + Domains + Skills + Standards
→ semantic model + professional dependency resolution
→ Engineering Asset Catalog / bounded custom path khi cần
→ workflow + Feature-based Chunk Streaming
→ capability preflight
→ CDT-AutoCAD / CDT-SketchUp / CDT-Blender / CDT-SolidWorks
→ read-after-write + recovery
→ independent QA / Checker
→ drawing/document/artifact QA
→ traceable handoff
→ ready_for_professional_review
```

CDT_Engineer không chứa native COM/Ruby/bpy/SolidWorks backend. Các repository CDT-* engine là Generic Execution Engines; CDT_Engineer sở hữu **chuyên môn kỹ sư, quy tắc, semantic meaning, workflow và QA**.

## MCP provider surface

CDT_Engineer được expose như một first-class MCP provider theo SlncTrZ Provider Standard. Provider dùng bare tool names; SlncTrZ-MCP canonicalize thành `cdt-engineer.*`. Model/Agent nhìn thấy `cdt-engineer.*` song song với `cdt-autocad.*`, `cdt-sketchup.*`, `cdt-solidworks.*` và tự orchestration vòng **think → execute → observe → verify**.

Provider CDT_Engineer chỉ expose engineering semantics/checks/evidence; nó **không proxy native CAD calls** và không tự gọi CDT-* engines phía sau. SlncTrZ-MCP giữ vai trò gateway/authority/routing; model là orchestration layer; các CDT-* engine giữ native execution mechanics.

Xem [MCP Tool Guide](docs/TOOL_GUIDE.md) cho public tool contract hiện hành.

## Tài liệu chuẩn

- [Documentation Map](docs/README.md)
- [Canonical Product Architecture](docs/ARCHITECTURE.md)
- [Documentation Policy](docs/DOCUMENTATION_POLICY.md)
- [Contract Model](docs/CONTRACTS.md)
- [Design Basis Contract](docs/DESIGN_BASIS_CONTRACT.md)
- [Engineering Role Contract](docs/ROLE_CONTRACT.md)
- [Engineering Skill Contract](docs/ENGINEERING_SKILL_CONTRACT.md)
- [Workflow Contract](docs/WORKFLOW_CONTRACT.md)
- [Agent Operational Profile Contract](docs/AGENT_PROFILE_CONTRACT.md)
- [Production Domain Contract](docs/PRODUCTION_DOMAIN_CONTRACT.md)
- [Release Scope & Semantic Dependency Policy](docs/RELEASE_SCOPE_POLICY.md)
- [QA / Checker Model](docs/QA_CHECKER_MODEL.md)
- [Standards Governance](docs/STANDARDS_GOVERNANCE.md)
- [Engineering Asset Catalog Contract](catalogs/ENGINEERING_ASSET_CATALOG_CONTRACT.md)

## Public production packages

Public domain packages hiện có:

- [Site Reconstruction](domains/site-reconstruction/benchmark-pack.md)
- [Mechanical Reconstruction](domains/mechanical-reconstruction/benchmark-pack.md)
- [Building Architecture](domains/building-architecture/benchmark-pack.md)
- [Building Structural](domains/building-structural/benchmark-pack.md)

Mỗi domain công khai scope/lifecycle của chính nó qua schema, rule pack, template pack, benchmark pack và review rubric. Việc một package tồn tại trong repo **không tự động có nghĩa native production acceptance đã đạt**.

Public software guides hiện có:

- [AutoCAD Operating Guide](software/autocad/OPERATING_GUIDE.md)
- [SketchUp Operating Guide](software/sketchup/OPERATING_GUIDE.md)
- [SolidWorks Operating Guide](software/solidworks/OPERATING_GUIDE.md)

Source engine maps/guides là contract baselines; runtime proof vẫn phải được discover tại Step 0.

## Ranh giới sản phẩm

- **CDT_Engineer:** Design Basis, domain semantics, roles, Engineering Skills, deterministic engineering logic, standards/rules, Engineering Asset Catalog semantics, workflows, QA/QC và engineering handoff.
- **CDT-AutoCAD / CDT-SketchUp / CDT-Blender / CDT-SolidWorks:** native execution, document lifecycle, query/mutation, geometry/topology, transaction/recovery, import/export và capability declaration.
- **SlncTrZ-MCP:** authority, routing, namespace và connection surface; không sở hữu engineering business logic.

## Nguyên tắc nghề nghiệp

- Purpose và Design Basis có trước software choice.
- Semantic-first: professional meaning phải được resolve trước native primitives.
- `unknown` phải được giữ là unknown; không bịa kích thước, tolerance, cao độ, tải, vật liệu hay compliance.
- Thiếu skill/catalog/standard/interface/analysis/evidence phải BLOCK, explicit reduced scope hoặc proxy đúng release class.
- Tool/runtime PASS không thay domain correctness, relationship/interface QA hay completeness QA.
- Mutation-heavy work dùng semantic feature chunks với measurable postconditions và truthful recovery.
- Render/model đẹp không đồng nghĩa chế tạo/thi công/compliance được.
- Human-readable deliverables phải được kiểm views/sections/details/dimensions/notes/schedules/revision/readability theo scope.
- Compliance cần exact standard identity/edition/applicability và evidence.
- QA độc lập + artifact identity + stale-evidence detection là hard requirement cho release mạnh.
- CDT_Engineer chuẩn bị evidence tới `ready_for_professional_review`; legal/professional sign-off nằm ngoài authority của hệ thống.

## Public vs development documentation

Stable architecture, contracts, policies, domain/skill packages, catalogs, software guides và sanitized benchmark definitions là public product documentation. Roadmaps, ADR history, audits, closure reports, handoffs, provider backlogs, private fixtures, raw runtime evidence và reference snapshots là development material và không định nghĩa public product semantics. Xem [Documentation Policy](docs/DOCUMENTATION_POLICY.md).
