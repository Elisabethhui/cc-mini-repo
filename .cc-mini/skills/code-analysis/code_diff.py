#!/usr/bin/env python3
import subprocess
import json

def get_git_diff():
    """获取有变更的文件列表供 Agent 消化"""
    try:
        # 1. 首先尝试获取 Working Tree 中未提交的变更 (Modified & Added)
        cmd = ['git', 'diff', '--name-only', 'HEAD']
        diff_output = subprocess.check_output(cmd).decode('utf-8').strip().splitlines()
        
        # 2. 如果工作区是干净的，则获取上一次 commit 的变更
        if not diff_output:
            cmd = ['git', 'diff', '--name-only', 'HEAD~1', 'HEAD']
            diff_output = subprocess.check_output(cmd).decode('utf-8').strip().splitlines()
            
        # 过滤：我们目前只关心 python 源码文件的变更
        py_files = [f for f in diff_output if f.endswith('.py') and "test" not in f]
        
        result = {
            "status": "success",
            "changed_files": py_files,
            "message": f"Found {len(py_files)} changed python files to ingest." if py_files else "No changes detected."
        }
    except Exception as e:
        result = {
            "status": "error",
            "message": f"Git diff execution failed: {str(e)}"
        }

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    get_git_diff()