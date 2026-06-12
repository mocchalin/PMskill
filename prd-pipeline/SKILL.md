---
name: prd-pipeline
description: >
  产品需求全流程 Pipeline——从一句话需求到可交付的 PRD、评审批注、UI Prompt、测试用例、UI 还原度检测、
  开发完工归档，七阶段串联自动衔接。当用户提到"跑一下 PRD 流水线"、"从需求到测试一条龙"、"完整走一遍产品需求流程"、
  "PRD pipeline"、"需求全流程"、"端到端需求流程"时触发。即使用户只是说"帮我从需求开始走完全流程"，
  也应使用此技能。
---

# PRD 全流程 Pipeline

将 7 个独立技能 + 1 个 AI 开发阶段串联为一条端到端的产品需求交付与开发流水线。

## 流水线总览

```
Stage 1  prd-writer              需求 → PRD 文档
            │
            ▼
Stage 2  prd-reviewer            PRD → 红字批注审核
            │
            ▼
Stage 3  doc-update-from-feedback 审核意见 → 修改标注版 PRD
            │
            ▼
Stage 4  prd-to-ui-prompt        PRD → UI 生成 Prompt
            │
            ▼
Stage 5  prd-test-validator      PRD → 测试用例 + 代码审查指令
            │
            ▼
Stage Dev  AI 辅助开发            PRD + UI Prompt → 代码（自动/半自动）
            │
            ▼
Stage 6  ui-alignment-checker    设计稿 vs 开发截图 → 还原度报告
            │
            ▼
Stage 7  prd-reverse-writer      代码仓库 → 开发完工报告 + PRD 反写归档
```

Stage 4 和 Stage 5 无依赖关系，可以并行执行。
Stage Dev 支持全自动（调用 AI 开发工具 CLI）和半自动（生成 prompt 文件）两种模式。
Stage 7 在开发完成后执行，是 pipeline 的最终归档阶段。

## 核心原则

1. **每个 Stage 调用对应的独立 skill**，不重复实现 skill 内部逻辑
2. **每个 Stage 之间有明确的用户确认关卡**（checkpoint），不擅自跳过
3. **上一阶段的输出自动成为下一阶段的输入**，用户不需要手动传递文件
4. **维护 pipeline 状态对象**，跟踪每个阶段的输入/输出文件和完成状态

## Pipeline 状态管理

在 pipeline 启动时初始化一个状态对象，贯穿全流程：

```
pipeline_state = {
    product_name: "",          # 产品名称（Stage 1 确定后填入）
    started_at: "",            # 启动时间
    stages: {
        1:   { status: "pending", skill: "prd-writer",              input: null, output: null },
        2:   { status: "pending", skill: "prd-reviewer",            input: null, output: null },
        3:   { status: "pending", skill: "doc-update-from-feedback", input: null, output: null },
        4:   { status: "pending", skill: "prd-to-ui-prompt",        input: null, output: null },
        5:   { status: "pending", skill: "prd-test-validator",      input: null, output: null },
        dev: { status: "pending", skill: "ai-dev-tools",            input: null, output: null },
        6:   { status: "pending", skill: "ui-alignment-checker",    input: null, output: null },
        7:   { status: "pending", skill: "prd-reverse-writer",      input: null, output: null },
    },
    final_prd: null,           # 最终版 PRD 路径（Stage 3 完成后或 Stage 2 跳过时确认）
    artifacts: []              # 所有产出文件路径汇总
}
```

每完成一个 Stage，更新 status 为 "done"，记录 input/output 路径。

---

## 启动流程

### Step 0: 收集初始信息

使用 AskUserQuestion 收集以下信息：

1. **需求描述**：用一段话描述你要做的产品/功能（必填）
2. **PRD 模式偏好**：
   - A. 企业级 PRD（大型 B 端系统从 0 到 1）
   - B. 用户故事驱动型 PRD（敏捷迭代、功能增强）
   - C. 迭代延续 PRD（基于已有 PRD 写下一期）
3. **输出格式**：Markdown 还是 Word？
4. **流水线范围**：是否七个阶段全部跑？还是只跑其中几个？
   - 全流程（7 个阶段）
   - 仅 PRD + 评审（Stage 1-3）
   - 仅 PRD + 测试（Stage 1 + 5）
   - 仅开发后归档（Stage 7）
   - 自定义选择

收集完成后，用一句话确认：

> 收到！将为你生成「{产品名}」的 {模式} PRD，然后依次走完 {N} 个阶段。准备好了说一声就开始。

用户确认后启动 Stage 1。

---

## Stage 1: PRD 编写（prd-writer）

**触发**：用户确认启动
**输入**：用户提供的需求描述 + 模式选择
**调用**：`prd-writer` skill
**输出**：`{产品名}_PRD_v1.md` 或 `.docx`

### 执行步骤

1. 调用 `prd-writer` skill，将用户的需求描述和模式选择传入
2. `prd-writer` 内部完成路由判断、信息收集、模板加载、编写、自检全流程
3. 产出 PRD 文档后，更新 pipeline 状态

### 🔴 CHECKPOINT 1 · 🛑 STOP

> **Stage 1 完成** ✅
> 产出文件：`{文件名}`
>
> 下一阶段：PRD 评审（prd-reviewer 将对文档做四维度审核 + 五角色视角检查）
>
> 是否继续？或者你想先手动修改一下 PRD 再进入评审？

选项：
- **继续评审** → 进入 Stage 2
- **我要先改一下** → 暂停，等用户改完后说"好了"再继续
- **跳过评审，直接进 Stage 3/4/5** → 根据用户选择跳转

---

## Stage 2: PRD 评审（prd-reviewer）

**触发**：用户确认继续评审
**输入**：Stage 1 产出的 PRD 文件路径
**调用**：`prd-reviewer` skill
**输出**：`{产品名}_PRD_批注审核_{日期}.docx`

### 执行步骤

1. 将 Stage 1 的 PRD 文件作为输入，调用 `prd-reviewer` skill
2. `prd-reviewer` 内部完成四维度分析 + 红字批注 + 问题汇总索引页
3. 产出批注版文档后，汇报审核结论（通过/需修改/重大缺陷 + 问题分布）
4. 更新 pipeline 状态

### 🔴 CHECKPOINT 2 · 🛑 STOP

`prd-reviewer` 的 Step 7 会询问用户是否要应用修改到原文档。在 pipeline 模式下，这个询问由 pipeline 统一管理：

> **Stage 2 完成** ✅
> 审核结论：{结论}
> 问题分布：高 {N} / 中 {N} / 低 {N}
> 产出文件：`{批注审核文件名}`
>
> 是否根据审核建议修改 PRD？

选项：
- **是，生成修改版** → 进入 Stage 3（doc-update-from-feedback）
- **不需要，当前 PRD 已经够好了** → 跳过 Stage 3，当前 PRD 作为 final_prd
- **我想手动改完再继续** → 暂停，等用户说"好了"后以修改后的文件作为 final_prd

---

## Stage 3: 应用审核反馈（doc-update-from-feedback）

**触发**：用户选择"生成修改版"
**输入**：Stage 1 的原始 PRD + Stage 2 的审核问题列表
**调用**：`doc-update-from-feedback` skill
**输出**：`{产品名}_PRD_修改标注_{日期}.docx`

### 执行步骤

1. 将 Stage 2 的 issues 列表转换为 `doc-update-from-feedback` 所需的结构化反馈格式
2. 调用 `doc-update-from-feedback` skill，传入原始 PRD 和结构化反馈
3. 产出修改标注版文档（紫色 = 新增/修改，删除线 = 建议删除）
4. 修改标注版的最终确认版本作为 `final_prd`
5. 更新 pipeline 状态

### 🔴 CHECKPOINT 3 · 🛑 STOP

> **Stage 3 完成** ✅
> 产出文件：`{修改标注文件名}`
> 这份修改标注版将作为后续阶段的基准 PRD。
>
> 接下来 Stage 4（UI Prompt）和 Stage 5（测试用例）可以并行执行。继续？

选项：
- **并行执行 Stage 4 + 5** → 同时启动两个阶段
- **只跑 Stage 4**（UI Prompt）
- **只跑 Stage 5**（测试用例）
- **先 4 后 5**（串行执行）

---

## Stage 4: 生成 UI Prompt（prd-to-ui-prompt）

**触发**：用户确认执行 Stage 4
**输入**：`final_prd`（Stage 3 产出的修改标注版，或 Stage 1/2 确认的最终版）
**调用**：`prd-to-ui-prompt` skill
**输出**：`{产品名}_UI_Prompt.md`

### 执行步骤

1. 将 final_prd 作为输入，调用 `prd-to-ui-prompt` skill
2. `prd-to-ui-prompt` 会询问目标工具（UI 设计工具 vs Vibe Coding 工具），这个询问正常进行
3. 产出整体设计方向 + 逐页面 UI Prompt
4. 更新 pipeline 状态

### 🔴 CHECKPOINT 4 · 🛑 STOP

> **Stage 4 完成** ✅
> 产出文件：`{UI Prompt 文件名}`
> 包含：整体设计方向 + {N} 个页面的详细 Prompt
>
> {如果 Stage 5 还没跑}：是否继续 Stage 5（测试用例生成）？

---

## Stage 5: 测试用例生成（prd-test-validator）

**触发**：用户确认执行 Stage 5
**输入**：`final_prd`
**调用**：`prd-test-validator` skill
**输出**：
- 测试用例 Excel：`{产品名}_测试用例.xlsx`
- PRD 质量审查 Excel（Stage A0）：`{产品名}_PRD质量审查.xlsx`
- 代码审查指令（如果有代码输入）：`{产品名}_修复指令.md`

### 执行步骤

1. 将 final_prd 作为输入，调用 `prd-test-validator` skill
2. `prd-test-validator` 内部会执行：
   - Stage A0：PRD 质量审查（6 维度分析）
   - Stage A：测试用例生成（5 种设计方法 + 异常场景覆盖）
   - 如果用户后续提供代码，还会执行 Stage B + C
3. 产出测试用例 Excel 和 PRD 质量审查报告
4. 更新 pipeline 状态

### 🔴 CHECKPOINT 5 · 🛑 STOP

> **Stage 5 完成** ✅
> 产出文件：
> - 测试用例：`{测试用例文件名}`（{N} 条用例，P0: {N} / P1: {N} / P2: {N}）
> - PRD 质量审查：`{审查文件名}`
>
> Stage 6（UI 还原度检测）需要等开发完成、有截图后才能跑。
> 是否现在进入 Stage 6？还是等有开发截图后再来？

选项：
- **现在进入 Stage 6**（如果已有设计稿截图和开发截图）
- **进入 Stage Dev（AI 辅助开发）** → 连接 AI 开发工具自动写代码
- **跳过 Stage 6，直接进 Stage 7（完工归档）** → 需要提供代码仓库路径
- **先跳过，之后再来**
- **全流程到此结束，给我一份汇总报告**

---

## Stage Dev: AI 辅助开发

**触发**：Stage 5 完成后用户选择进入，或用户随时要求"用 AI 工具帮我开发"
**输入**：
- `final_prd`（必选）
- Stage 4 的 UI Prompt（可选，有则作为 UI 参考）
- Stage 5 的测试用例（可选，作为验收基准）
**调用**：内置的 AI 工具集成逻辑（参考 `references/dev-tool-integration-guide.md`）
**输出**：项目代码目录

### 执行步骤

#### Step 1: 环境检测

扫描用户系统中安装的 AI 开发工具 CLI：

| 工具 | 检测命令 | 全自动模式 |
|------|---------|-----------|
| Claude Code | `command -v claude` | ✅ `-p` + `--dangerously-skip-permissions` |
| Codex | `command -v codex` | ✅ `codex exec` + `--yolo` |
| Cursor | `command -v cursor-agent` 或 `command -v agent` | ✅ `-p` + `--force --trust` |
| Qoder | `command -v qodercli` | ✅ `-p` |
| Kiro | `command -v kiro-cli` 或 `command -v kiro` | ✅ `--no-interactive` + `--trust-all-tools` |

#### Step 2: 确认技术栈

在连接工具之前，**必须先和用户确认技术栈**。从 PRD 中推断可能的技术栈，但最终由用户拍板。

使用 AskUserQuestion：

> PRD 中涉及以下功能模块：{模块列表}
>
> 请确认开发技术栈：

**前端框架**（从 PRD 的 UI Prompt 或用户历史偏好推断默认选项）：
- React + Tailwind CSS（推荐）
- Vue 3 + Element Plus
- Next.js (App Router)
- 用户自定义

**后端框架**（从 PRD 的非功能需求或接口设计推断）：
- Node.js + Express
- Python + FastAPI
- Java + Spring Boot
- Go + Gin
- 不需要后端（纯前端项目）

**数据库**（从 PRD 的数据模型推断）：
- PostgreSQL
- MySQL
- MongoDB
- SQLite（轻量原型）

**部署目标**（影响项目脚手架和配置生成）：
- Docker + 云平台
- Serverless（Vercel / AWS Lambda）
- 本地运行即可
- 暂不考虑部署

如果用户在之前的对话中已明确过技术栈偏好（参考 CLAUDE.md 中的 RULE-20260528-02），直接使用已知偏好，不再重复询问。

#### Step 3: 询问用户选择工具

使用 AskUserQuestion：

> 检测到你系统中安装了以下 AI 开发工具：{列表}
>
> 想用哪个来开发？
> - {工具名 A}（全自动执行，AI 直接在项目目录中写代码）
> - {工具名 B}（全自动执行）
> - 生成 prompt 文件（手动复制到工具中执行）
> - 跳过开发阶段

#### Step 4: 准备项目上下文

根据选择，自动执行：

1. 创建项目目录（如用户未指定）
2. 从 `final_prd` 提取关键信息，结合确认的技术栈，生成 `DEV_CONTEXT.md`
3. 根据目标工具生成对应的上下文文件：
   - Claude Code → `CLAUDE.md`
   - Codex / Qoder → `AGENTS.md`
   - Cursor → `.cursor/rules/prd-context.mdc`
   - Kiro → `.kiro/steering/prd-context.md`
4. 如果 pipeline 中有 Stage 4 的 UI Prompt，复制到项目目录

#### Step 5: 执行开发

**全自动模式**：
1. 组装针对目标工具的 prompt（详见 `references/dev-tool-integration-guide.md`）
2. 在后台运行 CLI 命令
3. 定期检查进度，向用户汇报
4. 超时（30 分钟）或失败时自动重试一次

**半自动模式**：
1. 为每个支持的工具生成一份 prompt 文件
2. 输出文件：`{产品名}_dev_prompt_{工具名}.md`
3. 告知用户如何复制到对应工具中使用

#### Step 6: 验证产出

AI 工具执行完成后自动验证：
1. 检查关键文件是否生成
2. 运行 lint 检查
3. 运行测试（如有）
4. 交叉比对 PRD 需求编号与代码实现

### 🔴 CHECKPOINT Dev · 🛑 STOP

> **AI 开发完成** ✅
> 使用工具：{工具名}
> 执行时间：{N} 分钟
>
> 需求覆盖：已实现 {N}/{Total} ({%})
> 测试通过：{N}/{Total}
> 项目目录：{路径}
>
> 是否继续进入 Stage 6（UI 还原度检测）？
> Stage 6 需要开发截图，可以现在截取或稍后提供。

选项：
- **继续 Stage 6（UI 还原度检测）** → 需要先截取开发截图
- **跳过 Stage 6，进入 Stage 7（完工归档）** → 代码目录自动传给 Stage 7
- **我想手动调整一下代码再继续** → 暂停，等用户说"好了"
- **全流程到此结束** → 输出汇总报告

---

## Stage 6: UI 还原度检测（ui-alignment-checker）

**触发**：用户提供设计稿截图 + 开发截图（或仅有代码）
**输入**：
- 设计基线：Stage 4 产出的 UI Prompt 生成的设计稿截图
- 开发结果：用户提供的开发截图或代码
**调用**：`ui-alignment-checker` skill
**输出**：`{产品名}_UI还原度报告.md`

### 执行步骤

1. 确认用户有设计稿截图和开发截图（或使用 auto-screenshot 模式）
2. 调用 `ui-alignment-checker` skill
3. 产出 8 维度还原度评审报告 + 100 分制评分 + 修复优先级
4. 如果用户要求自动修复，`ui-alignment-checker` 可进入修复模式
5. 更新 pipeline 状态

### 🔴 CHECKPOINT 6 · 🛑 STOP

> **Stage 6 完成** ✅
> 产出文件：`{还原度报告文件名}`
> 还原度评分：{N}/100
>
> 开发已完成，是否进入 Stage 7（PRD 反写与完工归档）？
> Stage 7 会从代码仓库提取实际实现，与原 PRD 做差异比对，生成开发完工报告。

选项：
- **进入 Stage 7（PRD 反写归档）** → 需要提供代码仓库路径
- **跳过归档，全流程到此结束** → 输出汇总报告
- **之后再来跑 Stage 7** → 先暂停，后续可单独触发

---

## Stage 7: PRD 反写与完工归档（prd-reverse-writer）

**触发**：开发完成后，用户提供代码仓库路径
**输入**：
- 代码仓库路径（必选）
- `final_prd`（可选，有则做差异比对，无则纯补录）
- Pipeline 其他阶段产出（可选参考）
**调用**：`prd-reverse-writer` skill
**输出**：`{产品名}_开发完工报告_{YYYYMMDD}.md`

### 执行步骤

1. 确认代码仓库路径和扫描范围
2. 如果有 final_prd，调用 `prd-reverse-writer` 的模式 A（PRD 反写 + 差异比对）
3. 如果没有 PRD，调用模式 B（无 PRD 补录，从代码逆向生成需求实现文档）
4. 技能内部完成：代码扫描 → 信息提取 → 差异比对/需求建模 → 生成完工报告
5. 报告涵盖：功能覆盖矩阵、技术方案沉淀、设计资产归档、变更决策记录、技术债清单
6. 用户确认后交付最终版

### 🔴 CHECKPOINT 7 · 🛑 STOP · Pipeline 终点

> **全流程完成** 🎉
>
> 汇总产出：
> | 阶段 | 产出文件 | 状态 |
> |------|---------|------|
> | PRD 编写 | {文件名} | ✅ |
> | PRD 评审 | {文件名} | ✅ |
> | 反馈应用 | {文件名} | ✅ |
> | UI Prompt | {文件名} | ✅ |
> | 测试用例 | {文件名} | ✅ |
> | AI 开发 | {项目目录} | ✅ |
> | UI 还原度 | {文件名} | ✅ |
> | 完工归档 | {文件名} | ✅ |

---

## 阶段间衔接规则

### 文件传递规则

| 上游 | 下游 | 传递什么 | 怎么传 |
|------|------|---------|--------|
| Stage 1 → 2 | PRD 文档文件路径 | 直接传文件路径 |
| Stage 2 → 3 | 审核 issues 列表 + 原始 PRD 路径 | issues 转结构化反馈 |
| Stage 3 → 4/5 | final_prd 路径 | 直接传文件路径 |
| Stage 4 → 6 | UI Prompt 文件 + 设计稿截图 | Prompt 辅助理解设计意图 |
| Stage 5 → 6 | 测试用例作为还原度验证参考 | 可选参考 |
| Stage 3/4/5 → Dev | final_prd + UI Prompt + 测试用例 | 生成 DEV_CONTEXT.md 和项目上下文 |
| Dev → 6 | 代码目录 + 开发截图 | UI 还原度检测 |
| Dev → 7 | 代码目录 | PRD 反写与完工归档 |
| Stage 1-5 → 7 | final_prd + 代码仓库路径 | PRD 做差异比对基准，代码做提取源 |
| Stage 6 → 7 | UI 还原度报告 | 可选参考，辅助设计资产验证 |

### 跳过规则

- 如果用户选择跳过 Stage 2（评审），则 Stage 3 也自动跳过，Stage 1 产出直接作为 final_prd
- 如果用户选择跳过 Stage 3（应用反馈），Stage 2 的批注版作为参考，Stage 1 产出作为 final_prd
- Stage 4 和 Stage 5 互不依赖，可以任意组合执行
- Stage 6 可以在任何有设计稿和开发截图的时候独立执行
- Stage Dev 可以在 Stage 5 完成后的任何时间执行，需要 final_prd 作为输入
- Stage Dev 检测到 CLI 工具时自动进入全自动模式，否则退到半自动（生成 prompt 文件）
- Stage 7 可以在开发完成后的任何时间独立执行（不需要先跑 Stage 6）
- Stage 7 有 final_prd 时自动进入模式 A（差异比对），没有时自动进入模式 B（纯补录）

### 错误处理

Pipeline 执行中可能遇到以下异常，按三段式 Fallback 处理。

| 触发条件 | 一线修复 | 仍失败兜底 |
|---|---|---|
| Stage skill 执行失败（超时/报错） | 向用户报告错误，提供"重试/跳过/终止"三个选项 | 终止 pipeline，保留已完成的 Stage 产出 |
| 上游 Stage 产出文件格式损坏 | 尝试提取可用内容（纯文本），标注信息受限 | 请求用户手动修复或重新跑该 Stage |
| final_prd 路径不存在（Stage 3 跳过后） | 确认 Stage 1 产出作为 final_prd | 请用户手动指定 PRD 文件路径 |
| Stage Dev 的 AI 工具 CLI 不可用 | 列出已检测到的其他工具供选择 | 退到半自动模式（生成 prompt 文件），告知用户如何手动执行 |
| Stage 6 缺少设计稿/开发截图 | 告知用户需要截图，提供 auto-screenshot 模式 | 跳过 Stage 6，直接进入 Stage 7 或终止 |
| 用户从中间 Stage 恢复执行但缺少上游产出 | 检测缺失的产出文件，提示需要先补跑哪些 Stage | 让用户手动提供文件，或从该 Stage 重新开始 |
| Stage 4 和 5 并行执行时一个失败 | 成功的 Stage 产出保留，失败的提供重试选项 | 标记失败 Stage 为 skipped，继续后续流程 |

每个 Stage 的产出即使不完美，也由用户决定是否继续，不自动判断质量。

---

## 快速启动命令

用户可以通过以下方式快速触发：

| 用户说 | 触发动作 |
|--------|---------|
| "跑一下 PRD 流水线" | 进入 Step 0 收集信息 |
| "从需求到测试一条龙" | 进入 Step 0 收集信息 |
| "帮我走一遍完整流程" | 进入 Step 0 收集信息 |
| "PRD pipeline" | 进入 Step 0 收集信息 |
| "从 Stage 3 继续" | 从 Stage 3 恢复执行（需要之前有产出） |
| "只跑 Stage 1 和 5" | 仅执行 Stage 1 + Stage 5 |
| "用 AI 帮我开发这个功能" | 直接进入 Stage Dev |
| "连接到 Cursor 帮我写代码" | 直接进入 Stage Dev（指定工具） |
| "项目做完了，帮我反写 PRD" | 直接进入 Stage 7（需代码仓库路径） |
| "帮我补一份完工报告" | 直接进入 Stage 7 |

---

## 示例场景

> **用户**：跑一下 PRD 流水线，我要做一个电商 App 的智能推荐功能
>
> **AI**：（Step 0 收集信息）
> → 确认模式 B（用户故事驱动型）、Markdown 格式、全流程
>
> **Stage 1**：prd-writer 生成 `电商App智能推荐_PRD_v1.md`
> → 用户确认继续
>
> **Stage 2**：prd-reviewer 审核，发现 8 个问题（2 高 / 4 中 / 2 低）
> → 用户选择生成修改版
>
> **Stage 3**：doc-update-from-feedback 应用修改，产出修改标注版
> → 用户确认继续
>
> **Stage 4**：prd-to-ui-prompt 生成 UI Prompt（目标：Vibe Coding 工具）
> → 产出 6 个页面的详细 Prompt
>
> **Stage 5**：prd-test-validator 生成 45 条测试用例
> → P0: 12 条 / P1: 20 条 / P2: 13 条
>
> **Stage Dev**：检测到 Claude Code CLI，用户选择全自动模式
> → 生成 DEV_CONTEXT.md + CLAUDE.md
> → claude -p 执行 28 分钟，实现 6 个功能模块
> → 自动验证：5/6 模块测试通过，1 个模块有 lint 错误
>
> **Stage 6**：（截取开发截图后运行）
>
> **Stage 7**：开发完成后反写 PRD
> → prd-reverse-writer 扫描代码，与 PRD 做差异比对
> → 产出开发完工报告：功能覆盖率 87%、3 条需求砍掉、5 条新增、12 条技术债
>
> **Pipeline 汇总**：输出全流程 8 份产出清单

---

## 反例与黑名单

Pipeline 执行过程中必须避免以下反模式。

### 流程编排 · 禁止动作

| 反模式 | 为什么不要做 | 替代做法 |
|---|---|---|
| 自动跳过 Checkpoint 推进到下一阶段 | 用户失去决策权，可能产出非预期结果 | 每个 🔴 CHECKPOINT 必须暂停等用户确认 |
| 用"为了效率"跳过 Stage | 用户可能错过关键质量关卡 | 明确告知跳过的后果，让用户拍板 |
| 把上游 Stage 产出当 final_prd 而不确认 | 用户未审核过的 PRD 进入下游 | Stage 3 完成后（或跳过 Stage 2/3 时）必须确认 final_prd |
| 自动替用户选择 AI 开发工具 | 违反用户工具偏好（RULE-20260528-02） | 检测可用工具后列出，让用户选择 |
| 自动替用户选择技术栈 | 可能与用户已有偏好冲突 | 从 PRD 推断默认选项，让用户确认 |

### 状态管理 · 禁止动作

| 反模式 | 为什么不要做 | 替代做法 |
|---|---|---|
| 静默覆盖 pipeline 状态 | 丢失已执行阶段的信息，无法回溯 | 每个 Stage 完成后显式更新状态，向用户展示 |
| 不记录 artifacts 路径 | 用户找不到之前阶段的产出文件 | 每个 Stage 产出后立即追加到 artifacts 列表 |
| 在 Stage 之间丢失上下文 | 下游 Stage 拿不到上游产出 | 用文件路径传递，不依赖对话上下文 |

### Stage 串联 · 禁止动作

| 反模式 | 为什么不要做 | 替代做法 |
|---|---|---|
| Stage 失败后自动重试 | 可能陷入死循环或掩盖真实问题 | 向用户报告错误，提供重试/跳过/终止三个选项 |
| Stage 4 和 5 强制串行 | 浪费并行执行的时间 | 提供并行选项，用户可选择并行/串行 |
| 把 Stage Dev 的全自动模式强推给用户 | 部分用户偏好半自动（生成 prompt 文件） | 同时展示全自动和半自动选项 |
| 不告知 Stage 6 需要截图前置条件 | 用户执行到 Stage 6 才发现无法运行 | 在 Checkpoint 5 和 Checkpoint Dev 提前告知 |
