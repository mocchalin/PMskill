# Product Skills Bundle

> 8 个 Skill 技能，覆盖从 PRD 撰写到开发完工归档的完整产品工作流。

## 包含技能

| 技能名 | 功能说明 |
|--------|---------|
| **prd-writer** | PRD 文档撰写 — 输入产品思路，输出完整 PRD |
| **prd-reviewer** | PRD 评审与质量检查 — 自动检查逻辑漏洞、遗漏场景、模糊描述 |
| **doc-update-from-feedback** | 根据反馈更新文档 — 自动 diff 修改点，一键更新 PRD |
| **prd-to-ui-prompt** | 从 PRD 生成 UI 提示词 — 将 PRD 转为给设计师的 UI 需求提示词 |
| **prd-test-validator** | PRD 测试用例验证 — 根据 PRD 自动生成测试用例 |
| **ui-alignment-checker** | UI 一致性检查 — 自动对比设计规范，检查间距、颜色、字体一致性 |
| **prd-pipeline** | PRD 全流程 Pipeline — 7 阶段串联自动衔接，从需求到开发完工归档一条龙 |
| **prd-reverse-writer** | PRD 反写与完工归档 — 从代码仓库提取实际实现，生成开发完工报告 |

## 完整工作流

### 单技能独立使用

```
prd-writer 写 PRD
    → prd-reviewer 审 PRD
    → doc-update-from-feedback 根据反馈迭代
    → prd-to-ui-prompt 转 UI 需求
    → prd-test-validator 输出测试用例
    → ui-alignment-checker 验证 UI 一致性
    → prd-reverse-writer 开发完工归档
```

### Pipeline 一条龙模式

```
prd-pipeline
  ├─ Stage 1: prd-writer              需求 → PRD 文档
  ├─ Stage 2: prd-reviewer            PRD → 红字批注审核
  ├─ Stage 3: doc-update-from-feedback 审核意见 → 修改标注版 PRD
  ├─ Stage 4: prd-to-ui-prompt        PRD → UI 生成 Prompt
  ├─ Stage 5: prd-test-validator      PRD → 测试用例 + 代码审查指令
  ├─ Stage Dev: AI 辅助开发           PRD + UI Prompt → 代码
  ├─ Stage 6: ui-alignment-checker    设计稿 vs 开发截图 → 还原度报告
  └─ Stage 7: prd-reverse-writer      代码仓库 → 开发完工报告
```

## 安装方式

每个 `.skill` 文件都是标准 ZIP 归档，可直接安装到 QoderWork：

1. 下载所需技能的 `.skill` 文件
2. 在 QoderWork 中导入安装
3. 按各技能的 `SKILL.md` 指引使用

## 适用人群

- 产品经理 — 提升 PRD 撰写与评审效率
- 设计师 — 减少 UI 还原返工
- 开发/测试 — 快速对齐需求与测试用例

## License

各技能遵循其原始 LICENSE，详见每个技能目录内的 LICENSE.txt。
