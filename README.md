# PMskill
6 个Skill技能，覆盖从 PRD 撰写到 UI 验证的完整产品工作流。
包含技能
技能名	功能说明
prd-writer	PRD 文档撰写 — 输入产品思路，输出完整 PRD
prd-reviewer	PRD 评审与质量检查 — 自动检查逻辑漏洞、遗漏场景、模糊描述
doc-update-from-feedback	根据反馈更新文档 — 自动 diff 修改点，一键更新 PRD
prd-to-ui-prompt	从 PRD 生成 UI 提示词 — 将 PRD 转为给设计师的 UI 需求提示词
prd-test-validator	PRD 测试用例验证 — 根据 PRD 自动生成测试用例
ui-alignment-checker	UI 一致性检查 — 自动对比设计规范，检查间距、颜色、字体一致性
完整工作流

prd-writer 写 PRD
    → prd-reviewer 审 PRD
    → doc-update-from-feedback 根据反馈迭代
    → prd-to-ui-prompt 转 UI 需求
    → prd-test-validator 输出测试用例
    → ui-alignment-checker 验证 UI 一致性
安装方式
每个 .skill 文件都是标准 ZIP 归档，可直接安装到 QoderWork：

下载所需技能的 .skill 文件
在 QoderWork 中导入安装
按各技能的 SKILL.md 指引使用
适用人群
产品经理 — 提升 PRD 撰写与评审效率
设计师 — 减少 UI 还原返工
开发/测试 — 快速对齐需求与测试用例
License
各技能遵循其原始 LICENSE，详见每个技能目录内的 LICENSE.txt。
