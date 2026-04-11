# Game Design Document（兼容命名保留）

说明：本文件名沿用旧流程命名，但当前项目实际是 cc-mini wiki_strict 升级项目，而不是传统游戏项目。

## 一句话核心
在不破坏 `standard` 的前提下，为本地 32K 小模型构建受控的 `wiki_strict` 工作流。

## 当前目标
- 避免 OOM
- 避免偏航
- 支持任务级熟知识
- 支持局部 patch 和局部 debug
- 形成可恢复、可沉淀的 Wiki 中间层
