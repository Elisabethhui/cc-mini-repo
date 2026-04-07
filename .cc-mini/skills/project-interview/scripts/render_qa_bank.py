#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a default Q&A bank skeleton for interview notes")
    parser.add_argument("--output", default="./code-reading-notes/40_interview_notes/qa_bank.md", help="Output markdown path")
    parser.add_argument("--project-name", default="当前项目", help="Project name shown in the template")
    args = parser.parse_args()

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    content = f"""# {args.project_name} Q&A Bank

## Q1：这个项目是做什么的？
A：请基于 `project_interview_full.md` 和 `project_architecture.md` 补充简明回答。

## Q2：项目的整体架构怎么划分？
A：请基于模块划分、主执行链路和上下游关系补充回答。

## Q3：项目最核心的技术亮点是什么？
A：请从 runtime、状态管理、配置、模块解耦、性能或工程可维护性角度整理回答。

## Q4：如果让你继续优化，你会怎么做？
A：请从可扩展性、可维护性、性能、观测性、测试性角度补充回答。

## Q5：这个项目里最难理解的部分是什么？
A：请结合最复杂模块与主调用链说明原因，并给出拆解方式。

## Q6：你阅读这个项目时的顺序是什么？
A：请说明先看 repo scan、再看 file notes、再看 module notes、最后看 project summary 的思路。

## Q7：如果面试官追问某个模块实现细节怎么办？
A：请把模块级 summary 中的职责、接口、数据流、关键设计点转成回答。
"""

    output_path.write_text(content, encoding="utf-8")
    print(str(output_path))


if __name__ == "__main__":
    main()
