# 缺失文件补齐后的精确度校验报告

## 校验目标
确认新增的：
- `phases/phase-0-exec.md`
- `phases/phase-1-exec.md`
- `phases/phase-2-exec.md`
- `phases/phase-3-exec.md`
- `phases/phase-4-exec.md`
- `exec-packs/README.md`

是否满足以下三点：
1. 与 v2.0 总设计一致
2. 与“当前已回退到 Step 3，旧 Step 4 失效”的状态一致
3. 不会误导 Claude/Codex 跨阶段执行

## 校验结论
### 1. 与 v2.0 总设计的一致性
结论：**一致**

体现为：
- Phase 0 只做规则与契约升级
- Phase 1 只做模式接入与结构骨架
- Phase 2 才进入 digest / dehydration 最小版
- Phase 3 才进入 TaskPack / EditSpec / Goal Stack / plan
- Phase 4 才进入 ASTRead / strict patch / debug / retry

没有出现以下错误：
- 在 Phase 1 提前实现 patch/debug
- 在 Phase 2 提前实现 TaskPack / plan
- 在 Phase 3 提前实现 patch

### 2. 与当前项目状态的一致性
结论：**一致**

体现为：
- Phase 0 明确声明“项目已回退到 Step 3，旧 Step 4 失效”
- 所有 Phase 文件都不再引用旧 Step 4 作为当前依据
- `exec-packs/README.md` 明确说明旧 Step 4 只能留在 deprecated

### 3. 跨阶段风险校验
结论：**已做显式隔离**

每个 Phase 文件都包含：
- In Scope
- Out of Scope
- Stop Conditions
- Direct Runner Prompt

这样 Claude/Codex 在读取时，更难把后续阶段问题拉进当前阶段。

## 与 memory-bank-v2-full.zip 中原精简版的差异
原 zip 中的阶段文件：
- 更像“阶段索引 / 提纲”
- 信息量偏少
- 对新手直接驱动执行不够稳

本次增强版：
- 增加了前置条件
- 增加了允许/不允许修改的文件范围
- 增加了 Stop Conditions
- 增加了 Direct Runner Prompt
- 更适合直接给 Claude Code / Codex 使用

## 仍然保留的注意事项
### 1. 这些 Phase 文件仍然不是业务代码
它们是执行边界文件，不会替代真实实现。

### 2. 当前只适合做阶段驱动
如果你要做更小动作，仍建议从这些 Phase 文件再拆一层 `exec-pack`。

### 3. 不建议让 32K 模型自行再改写这些 Phase 文件
这些文件属于上位治理层，后续若要改，应优先由 ChatGPT 修改后再落盘。
