# Step 4 Review Checklist

## Scope Check
- [ ] 是否只做了目录规范与模板文件
- [ ] 是否没有进入 ingest / digest / lint / archive 的实现
- [ ] 是否没有进入 Step 5

## File Check
- [ ] 是否创建了 `memory-bank/wiki-layout.md`
- [ ] 是否创建了 `memory-bank/templates/`
- [ ] 是否至少创建了 8 个模板文件

## Frontmatter Check
- [ ] 模板是否全部使用 YAML frontmatter
- [ ] 字段名是否与 Step 3 一致
- [ ] 是否没有私自增加新的关键字段

## Template Quality Check
- [ ] Entity 模板是否覆盖 Role / Symbols / Flow / Dependencies / Edge Cases / Hotspots / Edit Entry Points / Source Trace
- [ ] TaskPack 模板是否覆盖 Task Summary / Target Files / Primary Symbols / Related Symbols / Hotspots / Constraints / Verify Checklist
- [ ] 其他模板是否有清晰最小结构

## Boundary Check
- [ ] 是否没有修改 `taskpack_policy.md`
- [ ] 是否没有修改 `conflict_policy.md`
- [ ] 是否没有修改 `watchdog_policy.md`
- [ ] 是否把 policy 边界问题留到了后续步骤

## Documentation Check
- [ ] `progress.md` 是否记录 Step 4 完成情况
- [ ] `architecture.md` 是否记录新增 layout 文件与模板文件职责

## Final Decision
- [ ] Step 4 可以判定为完成
- [ ] 可以进入 Step 5（若以上全部通过）
