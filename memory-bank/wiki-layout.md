# Wiki Directory Layout

## Purpose

本文件定义 CC-MINI 项目的 Wiki 目录结构规范，规定不同类型知识的存储位置，确保内容组织的一致性。

## Directory Structure

```
wiki/
├── index.md                    # Wiki 首页，全局导航入口
├── log.md                      # 运行日志，时间线记录
├── 00-site-info.md            # 站点元信息（若需）
│
├── entities/                  # 实体知识目录
│   ├── file.md                # 文件实体页面
│   ├── function.md           # 函数实体页面
│   ├── module.md             # 模块实体页面
│   └── ...                    # 其他实体页面
│
├── concepts/                  # 概念知识目录
│   ├── concept_name.md       # 概念页面
│   └── ...                    # 其他概念页面
│
├── comparisons/              # 对比知识目录
│   ├── comparison_name.md   # 对比页面
│   └── ...                    # 其他对比页面
│
├── reports/                   # 报告知识目录
│   ├── report_name.md       # 报告页面
│   └── ...                    # 其他报告页面
│
├── source_notes/             # 来源笔记目录
│   ├── source_note_name.md  # 来源笔记页面
│   └── ...                    # 其他来源笔记页面
│
├── taskpacks/                # 任务包目录
│   ├── taskpack_name.md     # 任务包页面
│   └── ...                    # 其他任务包页面
│
├── lint_reports/             # 质量检查报告目录
│   ├── lint_report_name.md  # Lint 报告页面
│   └── ...                    # 其他 lint 报告页面
│
└── archive/                   # 归档目录
    └── archive_name.md       # 归档页面
```

## Directory Responsibilities

### Root Level

| File | Responsibility |
|------|----------------|
| `index.md` | Wiki 首页，提供全局导航和入口概览 |
| `log.md` | 系统运行日志，按时间顺序记录所有重要事件 |
| `00-site-info.md` | 站点元信息（可选） |

### Entities

存放实体类知识页面，包括：

- 文件、函数、模块等代码实体
- 独立的知识点实体

每个实体页面代表一个独立的代码实体或概念实体。

### Concepts

存放概念类知识页面：

- 对某个技术概念的解释和说明
- 概念的背景、定义、应用场景

### Comparisons

存放对比类知识页面：

- 两个或多个实体/概念的对比分析
- 不同技术方案、设计模式的对比

### Reports

存放报告类知识页面：

- 项目分析报告
- 质量检查报告
- 进度报告等

### Source Notes

存放来源笔记：

- 原始的阅读笔记、思考笔记
- 待进一步处理的知识片段

### TaskPacks

存放任务包页面：

- 待完成的任务集合
- 任务依赖关系和执行计划

### Lint Reports

存放代码质量检查报告：

- Lint 检查结果汇总
- 问题列表和修复建议

### Archive

归档目录：

- 已失效、已过时的知识页面
- 历史版本记录

## Naming Convention

文件名格式遵循 `conventions.md` 定义：

```
[页面类型]_ [标识名称]- [状态]_ [时间戳].md
```

例如：

- `entity_ login_view-raw_ast_20240101.md`
- `concept_react-vs-vue-digested_20240101.md`

## Entry Points

| Directory | Entry Page | Description |
|-----------|------------|-------------|
| Root | `index.md` | Wiki 主入口 |
| entities | `index.md` | 实体目录索引 |
| concepts | `index.md` | 概念目录索引 |
| comparisons | `index.md` | 对比目录索引 |
| reports | `index.md` | 报告目录索引 |
| source_notes | `index.md` | 来源笔记索引 |
| taskpacks | `index.md` | 任务包索引 |
| lint_reports | `index.md` | Lint 报告索引 |
| archive | `index.md` | 归档目录索引 |

## Related Files

此目录结构对应运行时目录：`.cc-mini/wiki/`

## Version

- Created: [Step 4 completion date]
- Maintained by: AI Development Agent
