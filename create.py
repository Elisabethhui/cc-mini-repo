import os

# 定义要创建的目录结构
base_path = ".cc-mini/skills/code-analysis"

# 需要创建的文件列表（含路径）
files = [
    os.path.join(base_path, "SKILL.md"),
    os.path.join(base_path, "manifest_fields.md")
]

# 1. 创建目录（递归创建，不存在才创建）
os.makedirs(base_path, exist_ok=True)
print(f"✅ 目录已创建：{base_path}")

# 2. 创建空文件（文件不存在才创建，避免覆盖）
for file_path in files:
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            # 可写入默认内容，也可以留空
            f.write("")
        print(f"✅ 文件已创建：{file_path}")
    else:
        print(f"ℹ️ 文件已存在，跳过：{file_path}")

print("\n🎉 整个文件夹结构构建完成！")