#!/usr/bin/env python3
import os
import ast
from pathlib import Path
from datetime import datetime

# 配置扫描路径和 Wiki 存放路径
PROJECT_ROOT = Path(os.getcwd())
SRC_DIR = PROJECT_ROOT / "src"  # 假设你的核心代码在 src 目录下
WIKI_DIR = PROJECT_ROOT / ".cc-mini" / "wiki"
INDEX_FILE = WIKI_DIR / "index.md"

def ensure_wiki_dirs():
    """确保 Wiki 的基础目录结构存在"""
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    (WIKI_DIR / "entities").mkdir(exist_ok=True)
    (WIKI_DIR / "concepts").mkdir(exist_ok=True)
    
    log_file = WIKI_DIR / "log.md"
    if not log_file.exists():
        log_file.write_text("# 📖 Wiki 演进日志\n\n", encoding="utf-8")

def extract_symbols(filepath):
    """使用 AST 提取 Python 文件中的类和函数，极速且不需要跑大模型"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
    except Exception as e:
        return [], []

    classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    # 只提取顶层函数，忽略以 _ 开头的私有函数
    functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and not node.name.startswith('_')]
    
    return classes, functions

def build_index():
    """扫描代码库并生成 index.md"""
    ensure_wiki_dirs()
    
    markdown_lines = [
        "# 🗺️ CC-MINI 代码库全局导航图 (LLM Wiki)",
        f"> 自动生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "> ⚠️ Agent 提示：在回答关于系统架构的问题时，请优先通过本文件寻找对应的 Entity 笔记。\n",
        "## 📦 核心实体模块 (Entities)"
    ]

    # 遍历源文件
    for py_file in SRC_DIR.rglob("*.py"):
        # 忽略测试文件和 __init__
        if py_file.name.startswith("__") or "test" in py_file.parts:
            continue
            
        rel_path = py_file.relative_to(PROJECT_ROOT)
        classes, functions = extract_symbols(py_file)
        
        if not classes and not functions:
            continue # 空文件或无重要符号跳过
            
        # 对应的实体笔记路径 (例如 src/core/engine.py -> entities/core_engine.md)
        entity_name = str(rel_path.with_suffix('')).replace(os.sep, '_')
        entity_link = f"entities/{entity_name}.md"
        
        markdown_lines.append(f"### `[{rel_path}]` -> [[{entity_link}]]")
        if classes:
            markdown_lines.append(f"- **Classes**: {', '.join(classes)}")
        if functions:
            markdown_lines.append(f"- **Functions**: {', '.join(functions[:5])}" + ("..." if len(functions) > 5 else ""))
        markdown_lines.append("") # 空行

    markdown_lines.append("## 🧠 系统概念 (Concepts)")
    markdown_lines.append("*(由 Agent 在分析过程中动态创建与维护)*\n")
    
    # 扫描现有的 concepts
    concepts_dir = WIKI_DIR / "concepts"
    for concept_file in concepts_dir.glob("*.md"):
        markdown_lines.append(f"- [[concepts/{concept_file.name}]]")

    # 写入 index.md
    INDEX_FILE.write_text("\n".join(markdown_lines), encoding="utf-8")
    print(f"✅ Wiki Index 已生成: {INDEX_FILE}")

if __name__ == "__main__":
    build_index()