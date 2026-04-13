---
source_hash: dabb4c6cf0c9b231
status: partially_digested
updated_at: 1776054844.6630266
---

# 文献大纲: memory-bank/schema/conventions.md

- Conventions
  - 文档目的
  - 适用范围
  - 不适用范围
  - Step 3 的核心边界（本步必须拍板）
    - 本步必须确定什么
    - 本步明确不处理什么
  - 命名约定
  - 目录约定
  - 文档规则层与运行时数据结构是两层概念（新增）
  - Frontmatter 总体约定（Step 3 定稿）
    - 1. 唯一标准格式
    - 2. 哪些页面必须带 frontmatter
    - 3. 当前阶段可豁免的页面
  - 时间与列表字段格式约定
  - 通用字段定义（统一元数据契约）
    - A. 基础身份字段
    - B. 来源与追踪字段
    - C. 关系字段
    - D. 任务类字段
  - 字段取值约束（本步定稿）
    - 1. `type` 允许值
    - 2. `status` 允许值
    - 3. `domain` 建议值
    - 4. `confidence` 允许值
    - 5. v2.0 新增字段说明
  - 必填 / 选填规则（Step 3 定稿）
    - 1. 所有“受管理正式页面”的最小必填字段
    - 2. 所有“进入核心状态机的知识页面”必须额外具备
    - 3. 来源驱动页面的条件必填字段
    - 4. 高置信度知识页面的建议字段
    - 5. TaskPack 页面最小必填字段
    - 6. Archive 页面最小必填字段
    - 7. Lint Report 页面最小必填字段
  - 不同页面类型的最小 frontmatter 要求
    - A. Entity 页面
    - B. Concept 页面
    - C. Report 页面
    - D. TaskPack 页面
  - 页面状态约定（初版）
  - 页面结构约定（初版）
  - 更新约定
  - 质量约定