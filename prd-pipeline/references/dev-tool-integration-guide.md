# AI 开发工具集成指南

> 本文件由 prd-pipeline 技能在执行 Stage Dev（AI 辅助开发）时加载。
> 提供工具检测、CLI 调用、prompt 组装和回退策略的完整规范。

---

## 支持的工具清单

| 工具 | 命令名 | 非交互模式标志 | 跳过确认标志 | 系统上下文文件 |
|------|--------|--------------|-------------|-------------|
| Claude Code | `claude` | `-p "prompt"` | `--dangerously-skip-permissions` | `CLAUDE.md` |
| Codex | `codex` | `codex exec "prompt"` | `--yolo` | `AGENTS.md` |
| Cursor | `cursor-agent` / `agent` | `-p "prompt"` | `--force --trust` | `.cursor/rules/*.mdc` |
| Qoder | `qodercli` | `-p "prompt"` | （无独立标志） | `AGENTS.md` |
| Kiro | `kiro` / `kiro-cli` | `--no-interactive "prompt"` | `--trust-all-tools` | `.kiro/steering/*.md` |

---

## 第一步：环境检测

Pipeline 进入 Stage Dev 时，先自动检测用户系统中安装了哪些 AI 开发工具。

### 检测脚本

```bash
# 逐一检测，记录可用工具
available_tools=()

command -v claude &>/dev/null && available_tools+=("claude-code")
command -v codex &>/dev/null && available_tools+=("codex")
command -v cursor-agent &>/dev/null && available_tools+=("cursor") || \
  command -v agent &>/dev/null && available_tools+=("cursor")
command -v qodercli &>/dev/null && available_tools+=("qoder")
command -v kiro-cli &>/dev/null && available_tools+=("kiro") || \
  command -v kiro &>/dev/null && available_tools+=("kiro")

# 输出检测结果
echo "检测到的工具: ${available_tools[*]}"
```

### 检测结果处理

| 检测结果 | 处理方式 |
|---------|---------|
| 检测到 1+ 个工具 | 进入全自动模式，询问用户用哪个工具 |
| 未检测到任何工具 | 进入半自动模式，生成 prompt 文件供手动复制 |

使用 AskUserQuestion 让用户选择：

> 检测到你系统中安装了以下 AI 开发工具：{列表}
>
> 想用哪个工具来开发？
> - {工具名}（全自动执行）
> - 生成 prompt 文件（手动复制到工具中）
> - 跳过开发阶段，直接进入后续阶段

---

## 第二步：确认技术栈

在选择 AI 工具之前，**必须和用户确认技术栈**。技术栈决定了项目脚手架、依赖安装和代码生成方式。

### 确认策略

1. **先从 PRD 推断**：如果 PRD 的 UI Prompt 或技术架构章节已指定技术栈，作为推荐选项
2. **检查用户历史偏好**：如果 CLAUDE.md 中有已记录的工具偏好（参考 RULE-20260528-02），直接使用，不再询问
3. **否则主动询问**

### 询问模板

使用 AskUserQuestion 收集以下信息：

**前端框架**（从 PRD 推断默认选项）：
- React + Tailwind CSS
- Vue 3 + Element Plus
- Next.js (App Router)
- 用户自定义

**后端框架**（从 PRD 推断默认选项）：
- Node.js + Express
- Python + FastAPI
- Java + Spring Boot
- Go + Gin
- 不需要后端（纯前端项目）

**数据库**（从 PRD 数据模型推断）：
- PostgreSQL
- MySQL
- MongoDB
- SQLite（轻量原型）

**部署目标**：
- Docker + 云平台
- Serverless（Vercel / AWS Lambda）
- 本地运行即可
- 暂不考虑部署

### 确认后动作

技术栈确认后，将其写入 `DEV_CONTEXT.md` 的头部，作为 AI 工具的强约束指令：

```markdown
# 技术栈约束（严格遵守）

- 前端：React 18 + TypeScript + Tailwind CSS
- 后端：Node.js 20 + Express
- 数据库：PostgreSQL 16 + Prisma ORM
- 部署：Docker Compose

## 禁止事项
- 不要引入上述栈以外的大型框架（如不要用 Next.js 替代 React + Express）
- 不要使用 class 组件，统一使用函数组件 + Hooks
- 样式只用 Tailwind 工具类，不写自定义 CSS
```

这些约束会被注入到每个 AI 工具的上下文文件中（CLAUDE.md / AGENTS.md / .cursor/rules 等），确保生成的代码符合用户期望。

---

## 第三步：准备项目上下文

不管用哪个工具，都需要先准备一个标准化的项目上下文。这些文件会被写入项目目录。

### 3.1 系统上下文文件

根据目标工具生成对应的上下文文件：

**Claude Code → `CLAUDE.md`**

```markdown
# 项目指令

## 技术栈
- 前端：{从 PRD/技术栈选择推断}
- 后端：{从 PRD/技术栈选择推断}
- 数据库：{从 PRD 推断}

## 开发规范
- 遵循 PRD 中的功能需求编号（F-xxx-xx）
- 每个功能模块对应独立的目录/文件
- 必须实现 PRD 中定义的 UI 四态（正常/加载/空/错误）
- 使用 PRD 文案清单中的确切文案
- 实现 PRD 数据埋点设计中定义的所有埋点

## 测试要求
- 为每个 P0 需求编写单元测试
- 边界条件必须覆盖 PRD 中定义的极值
```

**Codex → `AGENTS.md`**（同上格式）

**Cursor → `.cursor/rules/prd-context.mdc`**

```markdown
---
description: "PRD 开发上下文 - 始终应用"
globs: []
alwaysApply: true
---

{同上内容}
```

**Qoder → `AGENTS.md`**（同 Codex 格式）

**Kiro → `.kiro/steering/prd-context.md`**（同 Claude Code 格式）

### 3.2 PRD 摘要文件

将 PRD 中的关键信息提取为一份精简的开发参考文件 `DEV_CONTEXT.md`，放在项目根目录：

```markdown
# 开发上下文摘要

## 功能需求清单
{从 PRD 提取所有 F-xxx 编号和需求描述}

## UI 交互状态规范
{从 PRD 提取四态规范}

## 文案清单
{从 PRD 提取所有文案}

## 数据埋点设计
{从 PRD 提取埋点规范}

## 非功能需求
{性能、安全、兼容性指标}
```

### 3.3 UI Prompt 文件

如果 pipeline 中已有 Stage 4 的 UI Prompt 产出（`XXX_UI_Prompt.md`），直接复制到项目目录。没有则跳过。

---

## 第四步：组装 Prompt

根据目标工具的特性，组装不同风格的 prompt。

### 通用 prompt 核心内容

所有工具共享的核心指令部分：

```
你是一个全栈开发工程师。请根据以下需求文档，在 {项目目录} 中实现完整的功能代码。

## 你的任务

1. 阅读 DEV_CONTEXT.md 了解功能需求和 UI 规范
2. 按照需求编号（F-001 到 F-{NNN}）逐一实现
3. 每个功能必须覆盖：正常态、加载态、空态、错误态
4. 使用文案清单中的确切文案，不要自行编造
5. 实现数据埋点设计中的所有埋点
6. 为 P0 需求编写单元测试

## 技术栈
- {具体技术栈}

## 完成标准
- 所有 F-xxx 功能已实现
- 单元测试通过
- 无 TypeScript/lint 错误
```

### 工具特定的 prompt 组装

**Claude Code（擅长复杂架构和多文件编辑）**

```bash
claude -p \
  --dangerously-skip-permissions \
  --system-prompt-file CLAUDE.md \
  --max-turns 50 \
  "阅读 DEV_CONTEXT.md，按照 F-001 到 F-{N} 的顺序逐一实现所有功能需求。
   每实现一个功能模块，运行对应的单元测试确认通过。
   实现完成后，运行全量测试并输出测试报告。"
```

**Codex（擅长标准化代码生成）**

```bash
codex exec \
  --sandbox workspace-write \
  --ask-for-approval never \
  "阅读 DEV_CONTEXT.md 和 AGENTS.md，实现所有功能需求（F-001 到 F-{N}）。
   技术栈：{tech_stack}。
   完成后运行 npm test 并输出结果。"
```

**Cursor（擅长 UI/前端代码）**

```bash
cursor-agent -p \
  --force --trust \
  --model auto \
  "阅读 DEV_CONTEXT.md 和 .cursor/rules/ 中的规则文件。
   按照 PRD 中的页面结构逐一实现前端页面，
   然后实现后端 API 和数据层。
   技术栈：{tech_stack}。
   实现完成后运行 npm run build && npm test。"
```

**Qoder（通用能力）**

```bash
qodercli -p \
  "阅读 DEV_CONTEXT.md 和 AGENTS.md，
   实现 {产品名} 的所有功能需求。
   技术栈：{tech_stack}。
   按需求编号 F-001 到 F-{N} 逐一实现，
   每个模块完成后运行对应测试。"
```

**Kiro（擅长 AWS 生态和基础设施）**

```bash
kiro-cli chat --no-interactive --trust-all-tools \
  "阅读 DEV_CONTEXT.md 和 .kiro/steering/ 中的指引文件。
   实现所有功能需求，技术栈：{tech_stack}。
   完成后运行测试并输出结果。"
```

---

## 第五步：执行与监控

### 全自动模式

1. 在项目目录中执行对应的 CLI 命令
2. 使用 Bash 工具的 `run_in_background` 模式运行（开发可能耗时较长）
3. 定期检查输出，向用户汇报进度

```bash
# 示例：Claude Code 全自动执行
cd {project_dir} && claude -p --dangerously-skip-permissions --max-turns 50 "..." 
```

### 超时与重试

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 超时时间 | 30 分钟 | AI 工具的最大执行时间 |
| 重试次数 | 1 次 | 失败后自动重试一次 |
| max-turns | 50 | Claude Code 的最大对话轮次 |

如果超时或失败：
1. 检查已生成的代码（可能部分完成）
2. 向用户报告状态：已完成 F-001 ~ F-{N}，未完成 F-{M} ~ F-{K}
3. 询问用户：重试未完成的部分 / 手动接管 / 跳过

---

## 第六步：验证产出

AI 工具执行完成后，自动执行以下验证：

### 6.1 代码完整性检查

```bash
# 检查关键文件是否存在
ls {project_dir}/src/
ls {project_dir}/tests/

# 检查 package.json 依赖是否安装
cd {project_dir} && npm install

# 运行 lint
npm run lint 2>&1 | head -20

# 运行测试
npm test 2>&1
```

### 6.2 需求覆盖检查

将 PRD 中的 F-xxx 编号与代码中的注释/文件/路由做交叉比对：
- 搜索代码中包含 F-xxx 的注释或变量名
- 检查路由配置是否覆盖了 PRD 中的所有页面
- 检查组件是否覆盖了 PRD 中的所有功能模块

### 6.3 向用户汇报

> **AI 开发完成** ✅
>
> 使用工具：{工具名}
> 执行时间：{N} 分钟
>
> 需求覆盖：
> - 已实现：{N}/{Total} ({%})
> - 未实现：{列表}
> - 测试通过：{N}/{Total}
>
> 项目目录：{路径}
>
> 是否继续进入 Stage 6（UI 还原度检测）？

---

## 半自动模式：生成 Prompt 文件

当用户系统中没有检测到 CLI 工具，或用户选择手动执行时，生成以下文件：

### 输出文件

| 文件 | 用途 |
|------|------|
| `{产品名}_dev_prompt_claude.md` | 粘贴到 Claude Code 的 prompt |
| `{产品名}_dev_prompt_codex.md` | 粘贴到 Codex 的 prompt |
| `{产品名}_dev_prompt_cursor.md` | 粘贴到 Cursor 的 prompt |
| `{产品名}_dev_prompt_qoder.md` | 粘贴到 Qoder 的 prompt |
| `{产品名}_dev_prompt_kiro.md` | 粘贴到 Kiro 的 prompt |
| `DEV_CONTEXT.md` | 所有工具共享的开发上下文 |

### Prompt 文件结构

每个 prompt 文件包含：
1. **工具特定的系统上下文**（如 .cursorrules 内容）
2. **核心开发指令**（针对该工具优化的 prompt）
3. **使用说明**（告诉用户怎么复制粘贴到对应工具中）

### 使用说明示例

```markdown
# {产品名} - Cursor 开发 Prompt

## 使用方法

1. 打开 Cursor IDE
2. 将 DEV_CONTEXT.md 复制到项目根目录
3. 打开 Cursor Chat（Cmd+L）
4. 将下方的 Prompt 全文粘贴到对话框
5. 按回车执行

---

## Prompt

{组装好的 prompt 内容}
```

---

## 与 Pipeline 其他阶段的衔接

### 上游输入

| 来源 | 传递内容 | 用途 |
|------|---------|------|
| Stage 1/3 | final_prd | 生成 DEV_CONTEXT.md |
| Stage 4 | UI_Prompt.md | 复制到项目目录作为 UI 参考 |
| Stage 5 | 测试用例 | 作为测试验证基准 |

### 下游输出

| 接收方 | 传递内容 | 用途 |
|--------|---------|------|
| Stage 6 | 代码目录 + 截图 | UI 还原度检测 |
| Stage 7 | 代码目录 | PRD 反写与完工归档 |

---

## 安全边界

1. **不自动提交代码**：AI 工具生成的代码留在工作目录，不自动 git commit/push
2. **不访问外部服务**：prompt 中明确指示不要调用外部 API 或部署服务
3. **隔离执行目录**：使用 pipeline 工作目录的子目录，不污染用户其他文件
4. **权限最小化**：全自动模式下使用 `--dangerously-skip-permissions` 等标志时，明确告知用户风险
