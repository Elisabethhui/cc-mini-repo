# Phase 6-A 测试留痕策略 v2.1

## 1. 模块完成 = 测试留痕 + 文档留痕
除了测试留痕外，必须同时完成文档留痕。

### 测试留痕
每次测试必须写入：
- `validation-runs/<timestamp>-.../env.snapshot`
- `validation-runs/<timestamp>-.../command.log`
- `validation-runs/<timestamp>-.../summary.txt`

### 文档留痕
模块完成后必须更新：
- `memory-bank/findings.md`
- `memory-bank/progress.md`
- `README` 的 Phase 6-A 状态段落

## 2. 禁止的情况
以下情况一律视为“模块未完成”：
1. 代码改好了，但没跑测试
2. 测试跑了，但没有 `summary.txt`
3. 测试通过了，但 findings 没更新
4. findings 更新了，但 progress / README 没更新
