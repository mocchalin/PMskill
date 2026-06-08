---
name: doc-update-from-feedback
description: "根据测试验证结果、研发反馈、评审意见等更新补充需求文档。当用户提供需求文档（.docx/.pdf/.md/.html）以及测试反馈、研发反馈、Bug报告、评审意见等内容时，自动识别文档中需要修改的位置，进行内容补充或调整。新增/修改的内容用紫色文字标记，删除的内容用删除线标记。特别支持从Excel（.xlsx/.xls/.csv）文件中自动识别和提取反馈内容，智能解析测试用例表、Bug清单、反馈汇总表等常见表格结构。触发场景包括：用户说'根据反馈更新需求文档'、'把测试结果补充到PRD'、'根据研发意见修改需求'、'更新文档'、'补充文档'、'需求变更'、'文档迭代'、'同步反馈到文档'、'根据Excel反馈更新文档'等。即使用户只说'帮我更新一下这个文档'并附带反馈信息（包括Excel附件），也应使用此skill。支持从Notion页面URL读取文档内容并更新。"
---

# 需求文档反馈更新 Skill

## 概述

本 Skill 用于根据测试验证、研发反馈、评审意见等信息，自动识别并更新需求文档中的对应内容。核心特性：

- **智能定位**：根据反馈内容自动匹配文档中需要修改的章节和段落
- **可视化标记**：新增/修改内容使用 **紫色文字**（#7B2D8E）标记，删除内容使用 **删除线** 标记
- **多格式支持**：支持 .docx、.pdf、.md、.html 格式的需求文档
- **Excel反馈识别**：自动识别 .xlsx/.xls/.csv 格式的反馈文件，智能解析测试用例表、Bug清单、评审意见表等多种表格结构
- **Notion集成**：支持从 Notion 页面URL读取并更新内容

---

## 工作流程

### 第一步：获取输入

需要两类输入，**必须同时满足**才能继续：

1. **需求文档**（以下任一方式）：
   - 用户上传的文件（.docx / .pdf / .md / .html）
   - Notion 页面 URL
   - 直接粘贴的文本内容

2. **反馈信息**（以下任一方式）：
   - 用户直接描述的测试结果、研发反馈、评审意见
   - 上传的反馈文档（Excel、Word、文本等）
   - Bug 报告、项目跟踪系统任务内容
   - Notion 页面中的评论或反馈

**输入缺失时的处理**：

| 缺失情况 | 处理动作 |
|---------|---------|
| 只有需求文档，没有反馈信息 | **停止执行**，向用户说明："请提供需要同步到文档的反馈内容（测试反馈、Bug报告、评审意见等）" |
| 只有反馈信息，没有需求文档 | **停止执行**，向用户说明："请提供需要更新的需求文档" |
| 反馈信息格式无法识别 | 尝试按纯文本解析；若仍失败，向用户确认反馈内容的含义 |
| Notion URL 无法访问 | 提示用户检查 URL 权限，或导出为文件后上传 |
| 文档格式不支持 | 提示用户转换为 .docx / .pdf / .md / .html 之一 |

### 第一步补充：Excel 反馈文件的识别与解析

当反馈信息以 Excel 文件（.xlsx / .xls / .csv）形式提供时，按以下流程解析：

#### 1. 读取 Excel 文件

```python
import pandas as pd

# 读取所有 sheet
all_sheets = pd.read_excel('feedback.xlsx', sheet_name=None)

# 遍历每个 sheet 识别内容
for sheet_name, df in all_sheets.items():
    print(f"Sheet: {sheet_name}, 列: {list(df.columns)}, 行数: {len(df)}")
```

**注意**：使用 `xlsx` skill 的读取能力处理 Excel 文件。本 skill 目录下附带 `scripts/parse_excel_feedback.py` 脚本，可自动识别表格结构并提取标准化反馈条目。

#### 2. 智能识别表格结构

根据列名/表头自动判断反馈类型，支持以下常见表格结构：

**测试用例反馈表**（常见列名关键词）：
| 识别关键词 | 对应字段含义 |
|-----------|------------|
| 用例编号/用例ID/TC_ID/Case ID | 测试用例唯一标识 |
| 用例名称/测试项/Test Case | 测试用例描述 |
| 测试结果/结果/状态/Status/Result | 通过/失败/阻塞 |
| 实际结果/Actual Result | 实际测试表现 |
| 预期结果/Expected Result | 期望的结果 |
| 备注/说明/Remark/Comment | 补充信息 |
| 关联需求/需求编号/Requirement | 对应的需求项 |
| 优先级/Priority/严重程度/Severity | 问题紧急程度 |

**Bug清单/缺陷报告**（常见列名关键词）：
| 识别关键词 | 对应字段含义 |
|-----------|------------|
| Bug编号/缺陷ID/Bug ID/Defect ID | 缺陷唯一标识 |
| Bug标题/缺陷描述/Title/Summary | 缺陷概述 |
| 复现步骤/Steps/操作步骤 | 如何复现 |
| 实际表现/Actual/现象 | 出了什么问题 |
| 期望表现/Expected/预期 | 应该是什么样 |
| 所属模块/Module/功能模块 | 涉及的功能区域 |
| 状态/Status | 新建/已确认/已修复 |
| 建议/修改建议/Suggestion | 处理方案 |

**研发反馈/评审意见表**（常见列名关键词）：
| 识别关键词 | 对应字段含义 |
|-----------|------------|
| 章节/Section/位置/Location | 文档中的位置 |
| 原文/Original/当前描述 | 文档中现有内容 |
| 意见/反馈/Feedback/Comment | 反馈内容 |
| 建议修改/Suggestion/修改为 | 建议的修改方案 |
| 类型/Type（新增/修改/删除） | 变更操作类型 |
| 提出人/Author/反馈人 | 反馈来源 |

**需求变更申请表**（常见列名关键词）：
| 识别关键词 | 对应字段含义 |
|-----------|------------|
| 变更编号/CR编号/Change ID | 变更唯一标识 |
| 变更内容/Description | 变更详情 |
| 变更原因/Reason | 为什么要变更 |
| 影响范围/Impact/影响模块 | 涉及的功能范围 |
| 变更前/Before/原始需求 | 变更前的描述 |
| 变更后/After/新需求 | 变更后的描述 |

#### 3. 自动列名匹配算法

```python
def identify_column_role(col_name, role_keywords):
    """根据关键词匹配列的角色"""
    col_lower = str(col_name).lower().strip()
    for role, keywords in role_keywords.items():
        for kw in keywords:
            if kw.lower() in col_lower:
                return role
    return None

# 各角色的识别关键词
ROLE_KEYWORDS = {
    "id":        ["编号", "id", "序号", "no.", "编码"],
    "title":     ["标题", "名称", "title", "summary", "描述", "测试项", "用例名"],
    "module":    ["模块", "module", "功能", "页面", "章节", "section", "位置"],
    "status":    ["结果", "状态", "status", "result", "是否通过"],
    "actual":    ["实际", "actual", "现象", "表现", "bug描述"],
    "expected":  ["预期", "expected", "期望"],
    "feedback":  ["意见", "反馈", "feedback", "comment", "备注", "说明", "remark", "建议"],
    "suggestion":["建议修改", "修改为", "suggestion", "变更后", "after", "新需求"],
    "original":  ["原文", "original", "变更前", "before", "当前描述", "原始"],
    "priority":  ["优先级", "priority", "严重", "severity", "紧急", "等级"],
    "type":      ["类型", "type", "操作", "变更类型"],
    "author":    ["提出人", "author", "反馈人", "提交人", "测试人"],
}
```

#### 4. 从识别结果提取反馈条目

解析 Excel 后，将每行数据转化为标准化的反馈条目：

```python
def extract_feedback_items(df, column_mapping):
    """将 DataFrame 转化为标准反馈条目列表"""
    items = []
    for _, row in df.iterrows():
        item = {
            "id": row.get(column_mapping.get("id", ""), ""),
            "module": row.get(column_mapping.get("module", ""), ""),
            "title": row.get(column_mapping.get("title", ""), ""),
            "feedback": row.get(column_mapping.get("feedback", ""), ""),
            "suggestion": row.get(column_mapping.get("suggestion", ""), ""),
            "original": row.get(column_mapping.get("original", ""), ""),
            "priority": row.get(column_mapping.get("priority", ""), ""),
            "type": row.get(column_mapping.get("type", ""), "modify"),
        }
        # 跳过空行
        if not any(str(v).strip() for v in item.values() if v):
            continue
        items.append(item)
    return items
```

#### 5. 推断变更类型

当 Excel 中没有明确的「类型」列时，通过内容推断：

| 判断条件 | 推断类型 |
|---------|---------|
| 有"建议修改/修改为"列且有值 | **修改** (modify) |
| 有"原文"列但"建议修改"为空或为"删除" | **删除** (delete) |
| 无"原文"列，仅有反馈描述 | **补充** (add) |
| 状态列为"失败"/"不通过"且有实际/预期结果 | 根据差异判断是 **修改** 还是 **补充** |
| 类型列明确标注"新增/修改/删除" | 直接使用标注的类型 |

#### 6. 处理特殊 Excel 格式

**合并单元格**：使用 `openpyxl` 读取以正确处理合并单元格：
```python
from openpyxl import load_workbook
wb = load_workbook('feedback.xlsx')
ws = wb.active
# openpyxl 自动处理合并单元格的值填充
for row in ws.iter_rows(min_row=2, values_only=False):
    values = [cell.value for cell in row]
```

**多 Sheet 场景**：
- 如果有多个 sheet，逐一解析，每个 sheet 可能是不同类型的反馈
- Sheet 名称也是重要线索（如"测试结果"、"Bug清单"、"评审意见"）
- 合并所有 sheet 的反馈条目后统一匹配到文档

**表头不在第一行**：
```python
# 尝试前 5 行寻找表头
for skip in range(5):
    df = pd.read_excel('feedback.xlsx', skiprows=skip)
    if any(identify_column_role(c, ROLE_KEYWORDS) for c in df.columns):
        break  # 找到有效表头
```

**包含嵌入图片/截图的 Excel**：
- 提取截图信息记录在反馈条目中，但不用于文档匹配
- 在变更摘要中注明"该反馈包含截图，请人工确认"

### 第二步：解析文档结构

读取需求文档，解析其结构：
- 识别文档标题层级（H1/H2/H3...）
- 识别功能模块、需求项、验收标准等区块
- 建立文档的内容索引（章节名 → 位置映射）

### 第三步：匹配反馈到文档位置

对每条反馈信息：
1. 提取反馈的关键信息（涉及的功能、模块、字段、流程等）
2. 在文档结构中匹配最相关的章节/段落
3. 判断操作类型：
   - **补充**：文档中缺少的内容，需要新增
   - **修改**：文档中已有但描述不准确/不完整，需要调整
   - **删除**：文档中的内容经验证后需要移除

### 第三步半：🔴 CHECKPOINT — 确认修改计划

在正式修改文档之前，**必须**向用户展示修改计划并等待确认。这是文档编辑安全的关键防线——防止误改、漏改或过度修改。

**展示内容**：
```
已识别 N 条反馈，匹配到文档的 M 个位置：

1. 【修改】第2.3节 "[流程名称]" - [反馈摘要] → [计划修改简述]
2. 【新增】第3.1节 "异常处理" - [反馈摘要] → [计划新增简述]
3. 【删除】第4.2节 "旧版接口" - [反馈摘要] → [计划删除简述]
...

无法匹配的反馈（如有）：
- 第X条：[反馈内容] → 未找到对应位置，建议新增到"补充需求"章节

请确认：
- 以上匹配是否正确？
- 是否有不应修改的内容？
- 是否继续执行文档更新？
```

**用户确认后再进入第四步**；如果用户指出匹配错误或要求跳过某条反馈，重新调整匹配结果后再确认。

**如果用户未明确回应**：再次询问，不得擅自执行修改。

### 第四步：生成更新后的文档

根据匹配结果，在文档对应位置执行更新，并标记变更：

- **新增内容**：紫色文字（#7B2D8E）
- **修改内容**：紫色文字（#7B2D8E）替换原文
- **删除内容**：原文加删除线
- **涉及表格时**：只在单元格内部操作，不破坏表格结构（详见「表格保护规则」章节）

### 第五步：在目录下方插入变更摘要

在文档目录（TOC）的正下方插入一段变更摘要，列出本次所有修改/新增/删除的条目。如果文档没有目录，则插入在标题之后、正文之前。详见下方「变更摘要（插入到文档目录下方）」章节。

### 第六步：更新文档修订历史表

在文档的修订历史表（Revision History）中追加一条新记录，摘要说明本次修改内容。详见下方「文档修订历史表」章节。

---

## 文档修订历史表

需求文档通常在开头（封面或目录之后、正文之前）有一张**修订历史表**，记录每次文档变更的版本号、日期、修改人、修改摘要。本 Skill 在完成正文更新后，**必须同步更新该表**。

### 识别已有修订历史表

在文档中搜索以下关键词来定位已有的修订历史表：

| 格式 | 搜索方式 |
|------|---------|
| docx | 在 `document.xml` 中搜索表格（`<w:tbl>`），检查第一行单元格是否包含关键词 |
| Markdown | 搜索包含关键词的标题行（`## 修订记录`），其下方的 Markdown 表格即是 |
| HTML | 搜索 `<table>` 或含关键词的 `<h2>`/`<h3>` |
| Notion | 搜索包含关键词的 database 或 table block |

**识别关键词**（中英文均需覆盖）：

```
修订记录、修订历史、版本记录、修改记录、变更记录、文档历史、
版本修订、更新记录、Document History、Revision History、
Change Log、Changelog、Version History、Revision Record
```

**常见的修订历史表列结构**：

| 常见列名 | 含义 | 是否必填 |
|---------|------|---------|
| 版本号 / Version | 文档版本标识（如 V1.0、V1.1） | ✅ 必填 |
| 修订日期 / Date | 修改日期 | ✅ 必填 |
| 修订人 / Author | 修改者 | ✅ 必填，使用"Claude"或用户指定 |
| 修订内容 / Description | 本次修改的摘要说明 | ✅ 必填 |
| 审核人 / Reviewer | 审核者 | 选填，留空 |
| 备注 / Remark | 补充信息 | 选填 |

### 追加新记录

找到修订历史表后，在表格**末尾追加一行新记录**（遵循表格保护规则，不改变列数和格式）。

**版本号递增规则**：
- 读取表中最后一行的版本号
- 如果是 `V1.0` → 新版本为 `V1.1`
- 如果是 `V1.2.1` → 新版本为 `V1.2.2`
- 如果是 `1.0` → 新版本为 `1.1`
- 如果版本号格式不明或为空 → 使用 `V1.1`

**修订内容摘要**：从本次变更摘要中提取关键信息，浓缩为一句话或几行简述，例如：
- `根据测试反馈更新[某流程]验证规则；新增网络超时降级方案；移除废弃接口`
- `根据评审意见补充异常处理场景和权限说明`

**修订人**：默认使用 `Claude`，如果用户明确指定了修改人则使用用户指定的值。

### 各格式的实现

#### docx — 在修订历史表末尾追加行

```xml
<!-- 在修订历史表的 </w:tbl> 之前插入新行 -->
<w:tr>
  <w:trPr><!-- 复制已有行的 trPr --></w:trPr>
  <!-- 版本号 -->
  <w:tc>
    <w:tcPr><!-- 复制同列 tcPr --></w:tcPr>
    <w:p><w:r><w:t>V1.2</w:t></w:r></w:p>
  </w:tc>
  <!-- 修订日期 -->
  <w:tc>
    <w:tcPr><!-- 复制同列 tcPr --></w:tcPr>
    <w:p><w:r><w:t>2025-03-26</w:t></w:r></w:p>
  </w:tc>
  <!-- 修订人 -->
  <w:tc>
    <w:tcPr><!-- 复制同列 tcPr --></w:tcPr>
    <w:p><w:r><w:t>Claude</w:t></w:r></w:p>
  </w:tc>
  <!-- 修订内容摘要 -->
  <w:tc>
    <w:tcPr><!-- 复制同列 tcPr --></w:tcPr>
    <w:p><w:r><w:t>根据测试反馈更新[某流程]；新增异常处理场景</w:t></w:r></w:p>
  </w:tc>
</w:tr>
```

**注意**：修订历史表中的新记录使用**黑色普通文字**，不使用紫色——因为修订记录本身是元信息，不是需求正文内容。

#### Markdown — 在修订历史表末尾追加行

```markdown
## 修订记录

| 版本号 | 修订日期 | 修订人 | 修订内容 |
|--------|---------|--------|---------|
| V1.0 | 2025-01-15 | 张三 | 初始版本 |
| V1.1 | 2025-03-26 | Claude | 根据测试反馈更新[某流程]；新增异常处理场景 |
```

直接在表格最后一个 `|...|` 行之后追加新行，列数保持一致。

#### HTML — 在 `</tbody>` 前追加 `<tr>`

```html
<tr>
  <td>V1.2</td>
  <td>2025-03-26</td>
  <td>Claude</td>
  <td>根据测试反馈更新[某流程]；新增异常处理场景</td>
</tr>
```

#### Notion — 在修订历史 database/table 中追加行

使用 Notion MCP 工具新增一行记录，填写版本号、日期、修订人、修订内容。

### 如果文档中没有修订历史表

当文档中未找到已有修订历史表时，**自动创建一张**，插入位置在**文档封面/标题之后、目录之前**（如果没有目录则在正文第一个章节之前）。

**docx — 创建新表**：

在目标位置插入一个标题段落"修订记录" + 一个包含表头和首行记录的表格。表格的列数和宽度参考文档中已有的表格样式；如果文档中没有其他表格，使用4列（版本号/修订日期/修订人/修订内容）等宽布局。

```xml
<!-- 标题 -->
<w:p>
  <w:pPr>
    <w:pStyle w:val="Heading2"/>
  </w:pPr>
  <w:r><w:t>修订记录</w:t></w:r>
</w:p>
<!-- 表格（表头 + 第一条记录） -->
<w:tbl>
  <w:tblPr>
    <w:tblW w:w="9360" w:type="dxa"/>
    <w:tblBorders>
      <w:top w:val="single" w:sz="4" w:color="auto"/>
      <w:left w:val="single" w:sz="4" w:color="auto"/>
      <w:bottom w:val="single" w:sz="4" w:color="auto"/>
      <w:right w:val="single" w:sz="4" w:color="auto"/>
      <w:insideH w:val="single" w:sz="4" w:color="auto"/>
      <w:insideV w:val="single" w:sz="4" w:color="auto"/>
    </w:tblBorders>
  </w:tblPr>
  <w:tblGrid>
    <w:gridCol w:w="1440"/>
    <w:gridCol w:w="1800"/>
    <w:gridCol w:w="1440"/>
    <w:gridCol w:w="4680"/>
  </w:tblGrid>
  <!-- 表头 -->
  <w:tr>
    <w:tc><w:tcPr><w:tcW w:w="1440" w:type="dxa"/><w:shd w:val="clear" w:fill="D9E2F3"/></w:tcPr>
      <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>版本号</w:t></w:r></w:p></w:tc>
    <w:tc><w:tcPr><w:tcW w:w="1800" w:type="dxa"/><w:shd w:val="clear" w:fill="D9E2F3"/></w:tcPr>
      <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>修订日期</w:t></w:r></w:p></w:tc>
    <w:tc><w:tcPr><w:tcW w:w="1440" w:type="dxa"/><w:shd w:val="clear" w:fill="D9E2F3"/></w:tcPr>
      <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>修订人</w:t></w:r></w:p></w:tc>
    <w:tc><w:tcPr><w:tcW w:w="4680" w:type="dxa"/><w:shd w:val="clear" w:fill="D9E2F3"/></w:tcPr>
      <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>修订内容</w:t></w:r></w:p></w:tc>
  </w:tr>
  <!-- 第一条记录 -->
  <w:tr>
    <w:tc><w:tcPr><w:tcW w:w="1440" w:type="dxa"/></w:tcPr>
      <w:p><w:r><w:t>V1.1</w:t></w:r></w:p></w:tc>
    <w:tc><w:tcPr><w:tcW w:w="1800" w:type="dxa"/></w:tcPr>
      <w:p><w:r><w:t>2025-03-26</w:t></w:r></w:p></w:tc>
    <w:tc><w:tcPr><w:tcW w:w="1440" w:type="dxa"/></w:tcPr>
      <w:p><w:r><w:t>Claude</w:t></w:r></w:p></w:tc>
    <w:tc><w:tcPr><w:tcW w:w="4680" w:type="dxa"/></w:tcPr>
      <w:p><w:r><w:t>根据测试反馈更新文档</w:t></w:r></w:p></w:tc>
  </w:tr>
</w:tbl>
```

**Markdown — 创建新表**：

```markdown
## 修订记录

| 版本号 | 修订日期 | 修订人 | 修订内容 |
|--------|---------|--------|---------|
| V1.1 | 2025-03-26 | Claude | 根据测试反馈更新文档 |
```

**HTML — 创建新表**：

```html
<h2>修订记录</h2>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; width: 100%;">
  <thead>
    <tr style="background: #D9E2F3;">
      <th>版本号</th><th>修订日期</th><th>修订人</th><th>修订内容</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>V1.1</td><td>2025-03-26</td><td>Claude</td><td>根据测试反馈更新文档</td>
    </tr>
  </tbody>
</table>
```

### 修订历史表 vs 变更摘要 的区别

| | 修订历史表 | 变更摘要 |
|---|----------|---------|
| **性质** | 文档的正式版本记录，永久保留 | 本次更新的快速定位入口 |
| **位置** | 文档开头（封面/目录之前或之后） | 目录正下方 |
| **内容粒度** | 每次更新一条摘要记录 | 每处修改一条带跳转链接的明细 |
| **文字样式** | 黑色普通文字 | 黑色普通文字（带超链接） |
| **是否累积** | ✅ 累积所有历史版本 | ❌ 只展示本次更新（下次更新时替换） |
| **更新时机** | 每次文档变更都追加 | 每次文档变更都重新生成 |

## 输出格式指南

### 日期标记规范（重要）

对于 **Markdown (.md)** 和 **Word (.docx)** 格式的文档更新，所有新增或修改的内容**必须在前面添加日期标记**，格式为：

**【XX.XX(月日）更新】**

例如：【04.01(月日）更新】

**规则说明：**
1. 日期格式为 `月.日`，如 4月1日写作 `04.01`
2. 日期标记使用**紫色文字**，与更新内容保持一致
3. 日期标记紧跟在更新内容之前，作为前缀
4. 如果同一位置有多处更新，每处更新都需单独标记日期
5. 删除内容不需要日期标记，仅保留删除线样式

**示例：**
- Markdown: `<span style="color: #7B2D8E;">【04.01(月日）更新】</span>`
- docx: 紫色文字标记 `【04.01(月日）更新】`

---

### 对于 .docx 文件

使用 docx skill 的编辑能力，通过 XML 操作实现标记：

**紫色文字（新增/修改内容，带日期标记）：**
```xml
<w:r>
  <w:rPr>
    <w:color w:val="7B2D8E"/>
  </w:rPr>
  <w:t>【04.01(月日）更新】新增或修改的内容</w:t>
</w:r>
```

**删除线（删除内容）：**
```xml
<w:r>
  <w:rPr>
    <w:strike/>
    <w:color w:val="999999"/>
  </w:rPr>
  <w:t>被删除的内容</w:t>
</w:r>
```

**同时标记修改（先删除线旧内容，再紫色新内容带日期标记）：**
```xml
<!-- 旧内容加删除线 -->
<w:r>
  <w:rPr>
    <w:strike/>
    <w:color w:val="999999"/>
  </w:rPr>
  <w:t>旧的描述</w:t>
</w:r>
<!-- 新内容紫色标记，带日期前缀 -->
<w:r>
  <w:rPr>
    <w:color w:val="7B2D8E"/>
  </w:rPr>
  <w:t>【04.01(月日）更新】新的描述</w:t>
</w:r>
```

完整的 docx 编辑流程：
1. 使用 `docx` skill 的读取与编辑能力处理 Word 文档
2. 解包文档（docx 本质是 ZIP，可用 `unzip docx文件 -d 解包目录` 解包）
3. 在 `word/document.xml` 中找到目标位置并进行编辑
4. 重新打包（`cd 解包目录 && zip -r ../新文档.docx *`）
5. 本 skill 目录下附带 `scripts/mark_changes.py` 脚本，可直接在解包后的 XML 中批量插入紫色/删除线标记

### 对于 Markdown 文件

#### 完整的 Markdown 编辑流程

```
1. 读取 .md 文件 → 纯文本读取（UTF-8）
2. 解析文档结构 → 识别 frontmatter、标题树、代码块、表格等区域
3. 建立内容索引 → 标题行号映射
4. 定位修改位置 → 按行号范围精确编辑
5. 插入标记 → HTML 内联样式（span 标签）
6. 插入变更摘要 → 目录下方
7. 写回文件
```

本 skill 目录下附带 `scripts/mark_changes_md.py` 脚本，可自动完成步骤 2-6：解析 Markdown 结构、在正确位置插入紫色/删除线标记、生成变更摘要并插入目录下方。

#### 第1步：读取与结构解析

```python
import re

with open('doc.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# --- 解析 frontmatter（YAML 头部） ---
frontmatter_end = 0
if lines[0].strip() == '---':
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            frontmatter_end = i + 1
            break

# --- 识别代码块范围（不可在其中插入 span） ---
code_block_ranges = []  # [(start_line, end_line), ...]
in_code = False
code_start = 0
for i, line in enumerate(lines):
    if line.strip().startswith('```'):
        if not in_code:
            in_code = True
            code_start = i
        else:
            in_code = False
            code_block_ranges.append((code_start, i))

def is_in_code_block(line_num):
    return any(s <= line_num <= e for s, e in code_block_ranges)

# --- 构建标题树（章节索引） ---
heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
sections = []  # [{"level": 2, "title": "[章节标题]", "line": 42}, ...]
for i, line in enumerate(lines):
    if is_in_code_block(i):
        continue
    m = heading_pattern.match(line)
    if m:
        sections.append({
            "level": len(m.group(1)),
            "title": m.group(2).strip(),
            "line": i
        })

# --- 识别表格范围 ---
table_ranges = []
in_table = False
table_start = 0
table_pattern = re.compile(r'^\|.*\|')
for i, line in enumerate(lines):
    if table_pattern.match(line.strip()):
        if not in_table:
            in_table = True
            table_start = i
    else:
        if in_table:
            table_ranges.append((table_start, i - 1))
            in_table = False
if in_table:
    table_ranges.append((table_start, len(lines) - 1))

def is_in_table(line_num):
    return any(s <= line_num <= e for s, e in table_ranges)

# --- 识别目录位置 ---
toc_line = None
for i, line in enumerate(lines):
    stripped = line.strip().lower()
    if stripped in ['[toc]', '[[toc]]']:
        toc_line = i
        break
# 如果没有 [TOC]，查找手写目录块（连续的 - [xxx](#yyy) 行）
if toc_line is None:
    link_pattern = re.compile(r'^[\s]*[-*]\s*\[.+\]\(#.+\)')
    for i, line in enumerate(lines):
        if link_pattern.match(line):
            toc_line = i
            # 继续往下找到目录块结束
            while i + 1 < len(lines) and link_pattern.match(lines[i + 1]):
                i += 1
            toc_line = i  # 指向目录块最后一行
            break
```

#### 第2步：Markdown 特殊元素处理规则

**核心原则**：不同 Markdown 元素对 HTML 内联标记的兼容性不同，必须区分处理。

| 元素类型 | 能否插入 `<span>` 标记 | 处理方式 |
|---------|---------------------|---------|
| 普通段落 | ✅ 可以 | 直接在文本中插入 `<span>` |
| 标题行（`# / ## / ###`） | ✅ 可以 | 在标题文字部分插入 `<span>`，不动 `#` 符号 |
| 表格单元格（`| xxx |`） | ✅ 可以 | 在单元格内容中插入 `<span>`，不动 `|` 分隔符 |
| 列表项（`- / * / 1.`） | ✅ 可以 | 在列表内容部分插入 `<span>`，不动列表标记符 |
| 引用块（`>`） | ✅ 可以 | 在引用内容部分插入 `<span>`，不动 `>` 符号 |
| 代码块（` ``` `） | ❌ 不可以 | 在代码块**外部前方**用注释说明变更，代码块本身内容直接替换（不加 span） |
| 行内代码（`` ` ``） | ❌ 不可以 | 将整个行内代码段包在 `<span>` 外部 |
| 图片/链接 | ⚠️ 小心 | 修改 URL/alt 文本时直接替换，不在 `[]()` 内部嵌套 span |
| Frontmatter（`---`间） | ❌ 不可以 | 仅更新 YAML 字段值，不加任何 HTML 标记 |

**各元素的标记示例**：

**普通段落**：
```markdown
这是一段需求描述，其中<span style="text-decoration: line-through; color: #999;">旧的验证规则</span> <span style="color: #7B2D8E;">【04.01(月日）更新】新的验证规则：[字段A]必须满足[规则描述]</span>。
```

**标题行**：
```markdown
## <span style="text-decoration: line-through; color: #999;">用户管理</span> <span style="color: #7B2D8E;">【04.01(月日）更新】用户与权限管理</span>
```

**列表项**：
```markdown
- 支持密码登录
- <span style="text-decoration: line-through; color: #999;">支持[旧登录方式]</span> <span style="color: #7B2D8E;">【04.01(月日）更新】支持[新登录方式A]和[新登录方式B]</span>
- <span style="color: #7B2D8E;">【04.01(月日）更新】支持第三方 OAuth 登录（新增）</span>
```

**引用块**：
```markdown
> 业务规则：<span style="text-decoration: line-through; color: #999;">订单超过24小时未支付自动取消</span> <span style="color: #7B2D8E;">【04.01(月日）更新】订单超过30分钟未支付自动取消</span>
```

**代码块（不能在内部加 span，在外部标注）**：
```markdown
<span style="color: #7B2D8E;">【04.01(月日）更新】【修改】接口返回字段变更如下：</span>

` `` json
{
  "userId": "string",
  "nickName": "string",
  "email": "string"
}
` ``

<span style="text-decoration: line-through; color: #999;">（原接口无 email 字段）</span>
```

**行内代码**：
```markdown
字段类型从 <span style="text-decoration: line-through; color: #999;">`int`</span> 改为 <span style="color: #7B2D8E;">【04.01(月日）更新】`string`</span>
```

**Frontmatter 处理**：
```yaml
---
title: 需求文档
version: 1.1  # 直接更新版本号，不加 span
date: 2025-03-24  # 直接更新日期
---
```

#### 第3步：内联样式标记

**新增/修改内容（必须带日期标记）：**
```markdown
<span style="color: #7B2D8E;">【04.01(月日）更新】新增或修改的内容</span>
```

**删除内容：**
```markdown
<span style="text-decoration: line-through; color: #999999;">被删除的内容</span>
```

**同时标记修改（新内容带日期标记）：**
```markdown
<span style="text-decoration: line-through; color: #999999;">旧的描述</span> <span style="color: #7B2D8E;">【04.01(月日）更新】新的描述</span>
```

#### 第4步：编辑安全检查

对 Markdown 文件修改完成后，执行以下验证：

- [ ] 代码块内部没有插入任何 `<span>` 标签
- [ ] Frontmatter（`---` 之间）没有插入任何 HTML 标记
- [ ] 所有 `<span>` 标签正确闭合（`</span>`）
- [ ] 表格的 `|` 分隔符和 `|---|` 对齐行未被修改
- [ ] 列表缩进层级未被改变
- [ ] 图片和链接的 `[]()`/`![]()` 语法未被破坏
- [ ] 标题行的 `#` 符号数量未被改变（标题层级不变）
- [ ] 变更摘要已插入在目录下方，且使用普通文字+锚点链接

### 对于 HTML 文件

使用 CSS 类标记：

```html
<style>
  .doc-added { color: #7B2D8E; }
  .doc-deleted { text-decoration: line-through; color: #999999; }
</style>

<span class="doc-deleted">旧的描述</span>
<span class="doc-added">新的描述</span>
```

### 对于 Notion 页面

使用 Notion MCP 工具更新页面内容时：
- 新增内容在文字前加标记 `[新增]` 并使用紫色高亮
- 修改内容在文字前加标记 `[修改]` 并使用紫色高亮
- 删除内容使用删除线格式

---

## 表格保护规则（重要）

**核心原则：永远不破坏文档中已有的表格结构。** 表格是需求文档中最常见的结构化内容（如字段列表、接口参数表、状态流转表、权限矩阵等），更新时必须在表格内部按单元格粒度精确操作，严禁增删行列、合并/拆分单元格、改变表格边框和样式等结构性变更。

### 操作分类

| 场景 | 正确做法 | 禁止做法 |
|------|---------|---------|
| 修改某个单元格内容 | 在该单元格内部做删除线+紫色替换 | 删除整行后重新插入 |
| 表格中新增一行数据 | 在表格**末尾**追加新行，紫色标记 | 在表格中间插入行导致结构错位 |
| 删除表格中一行数据 | 对该行所有单元格内容加删除线，保留行结构 | 直接删除 `<w:tr>` 行元素 |
| 补充某个空单元格 | 在空单元格内写入紫色内容 | 改变单元格的合并或宽度 |
| 修改表头 | 在表头单元格内做删除线+紫色替换 | 增删列或改变列顺序 |

### docx 表格编辑规范

#### 修改单元格内容

找到目标 `<w:tc>` 单元格，在其内部的 `<w:p>` 段落中操作文本 run，不触碰 `<w:tcPr>`（单元格属性）、`<w:tblPr>`（表格属性）、`<w:trPr>`（行属性）：

```xml
<!-- ✅ 正确：仅在单元格内部替换文本 run -->
<w:tc>
  <w:tcPr><!-- 保持不变 --></w:tcPr>
  <w:p>
    <!-- 旧内容加删除线 -->
    <w:r>
      <w:rPr><w:strike/><w:color w:val="999999"/></w:rPr>
      <w:t>旧字段描述</w:t>
    </w:r>
    <!-- 新内容紫色 -->
    <w:r>
      <w:rPr><w:color w:val="7B2D8E"/></w:rPr>
      <w:t>新字段描述</w:t>
    </w:r>
  </w:p>
</w:tc>
```

```xml
<!-- ❌ 错误：修改了单元格属性或表格结构 -->
<w:tc>
  <w:tcPr>
    <w:tcW w:w="3000" w:type="dxa"/>  <!-- 被改动了！ -->
  </w:tcPr>
  ...
</w:tc>
```

#### 在表格末尾追加新行

当需要新增一条数据时，在 `</w:tbl>` 之前追加一个完整的 `<w:tr>` 行。**必须复制已有行的结构**（列数、`<w:tcPr>` 宽度、边框等），只替换文本内容为紫色：

```xml
<!-- 在 </w:tbl> 之前插入新行 -->
<w:tr>
  <w:trPr><!-- 复制已有行的 trPr --></w:trPr>
  <w:tc>
    <w:tcPr><!-- 复制同列已有的 tcPr（宽度、边框等） --></w:tcPr>
    <w:p>
      <w:r>
        <w:rPr><w:color w:val="7B2D8E"/></w:rPr>
        <w:t>新增字段名</w:t>
      </w:r>
    </w:p>
  </w:tc>
  <w:tc>
    <w:tcPr><!-- 复制同列已有的 tcPr --></w:tcPr>
    <w:p>
      <w:r>
        <w:rPr><w:color w:val="7B2D8E"/></w:rPr>
        <w:t>新增字段说明</w:t>
      </w:r>
    </w:p>
  </w:tc>
  <!-- ... 每列都要有对应的 tc，列数必须与表头一致 -->
</w:tr>
```

**关键检查项**：
- 新行的 `<w:tc>` 数量必须与表头行的列数完全一致
- 每个 `<w:tc>` 的 `<w:tcPr>` 中的 `<w:tcW>`（宽度）必须复制同列已有单元格的值
- 如果表格使用了 `<w:tblGrid><w:gridCol>`，不要修改它
- 不要改变 `<w:tblPr>` 中的任何属性

#### 删除表格中的一行（标记删除，不移除结构）

对该行每个单元格的文本内容加删除线，但**保留完整的行和单元格 XML 结构**：

```xml
<!-- ✅ 正确：保留行结构，内容加删除线 -->
<w:tr>
  <w:trPr><!-- 保持不变 --></w:trPr>
  <w:tc>
    <w:tcPr><!-- 保持不变 --></w:tcPr>
    <w:p>
      <w:r>
        <w:rPr><w:strike/><w:color w:val="999999"/></w:rPr>
        <w:t>被删除的字段名</w:t>
      </w:r>
    </w:p>
  </w:tc>
  <w:tc>
    <w:tcPr><!-- 保持不变 --></w:tcPr>
    <w:p>
      <w:r>
        <w:rPr><w:strike/><w:color w:val="999999"/></w:rPr>
        <w:t>被删除的字段说明</w:t>
      </w:r>
    </w:p>
  </w:tc>
</w:tr>
```

```xml
<!-- ❌ 错误：直接删除整行 -->
<!-- 删除了 <w:tr>...</w:tr> → 表格行数变化，结构被破坏 -->
```

### Markdown 表格编辑规范

Markdown 表格同样只在单元格内部做标记，不增删列：

```markdown
<!-- ✅ 正确：单元格内做标记，新增/修改内容带日期标记 -->
| 字段名 | 类型 | 说明 |
|--------|------|------|
| userName | String | <span style="text-decoration: line-through; color: #999;">用户名</span> <span style="color: #7B2D8E;">【04.01(月日）更新】用户昵称，最长20字符</span> |
| phone | String | [联系方式字段] |
| <span style="color: #7B2D8E;">【04.01(月日）更新】email</span> | <span style="color: #7B2D8E;">【04.01(月日）更新】String</span> | <span style="color: #7B2D8E;">【04.01(月日）更新】邮箱地址（新增字段）</span> |
```

**新增行**：在表格末尾追加，所有列都必须填写（空列也要保留 `|  |`），内容用紫色标记并带日期前缀。

**删除行**：对整行每个单元格的内容加删除线，不删除该行。

```markdown
<!-- ✅ 正确：删除行 = 每个单元格加删除线 -->
| <span style="text-decoration: line-through; color: #999;">oldField</span> | <span style="text-decoration: line-through; color: #999;">String</span> | <span style="text-decoration: line-through; color: #999;">已废弃字段</span> |
```

```markdown
<!-- ❌ 错误：直接删除整行 Markdown 文本 -->
```

### HTML 表格编辑规范

与 docx 类似，只操作 `<td>` / `<th>` 内部内容，不改动 `<table>`、`<tr>`、`<colgroup>` 等结构元素：

```html
<!-- ✅ 正确：在单元格内操作 -->
<td>
  <span class="doc-deleted">旧描述</span>
  <span class="doc-added">新描述</span>
</td>

<!-- 新增行：在 </tbody> 前追加 -->
<tr>
  <td><span class="doc-added">新字段</span></td>
  <td><span class="doc-added">String</span></td>
  <td><span class="doc-added">新增说明</span></td>
</tr>
```

### 表格编辑的通用检查清单

每次涉及表格修改时，编辑完成后必须验证：

- [ ] 表格行数：只允许在末尾追加，不允许中间插入或删除行
- [ ] 表格列数：修改前后列数完全一致
- [ ] 单元格合并：未改变任何合并单元格（`<w:vMerge>`、`<w:hMerge>`、`rowspan`、`colspan`）
- [ ] 单元格宽度：所有 `<w:tcW>` / `width` 值未被修改
- [ ] 表格样式：`<w:tblPr>` / `<table>` 属性未被修改
- [ ] 新增行格式：新行的列数、宽度与已有行一致

## 智能匹配策略

### 关键词匹配

从反馈中提取关键实体并在文档中定位：

| 反馈关键词类型 | 匹配目标 |
|-------------|---------|
| 功能名称（如"登录"、"支付"） | 对应功能模块章节 |
| 字段名称（如"[字段A]"、"[字段B]"） | 包含该字段的需求描述或表格 |
| 流程步骤（如"提交审核"、"退款"） | 对应流程描述段落 |
| 接口名称（如"getUserInfo"） | 接口设计章节 |
| 页面名称（如"个人中心"、"订单列表"） | 对应页面需求章节 |
| 异常场景（如"网络超时"、"并发"） | 异常处理/边界条件章节 |

### 语义匹配

当关键词无法精确匹配时，使用语义理解：
- 反馈 "点击按钮没反应" → 定位到对应按钮的交互设计段落
- 反馈 "数据不一致" → 定位到数据同步/一致性相关需求
- 反馈 "性能太慢" → 定位到非功能需求/性能指标章节

### Excel 反馈的匹配优先级

当反馈来自 Excel 时，按以下优先级匹配文档位置：

1. **"模块/章节"列直接命中**：Excel 中的模块名直接匹配文档章节标题（最优）
2. **"原文"列精确定位**：用 Excel 中的原文在文档中搜索精确位置
3. **"标题/描述"列语义匹配**：根据反馈描述推断涉及的功能模块
4. **"关联需求编号"列交叉引用**：如果文档中有需求编号，用 Excel 中的需求编号对应
5. **回退策略**：无法匹配时追加到文档末尾的"补充需求"章节

### 无法匹配时的处理

如果反馈内容无法在文档中找到对应位置：
1. 在文档末尾新增一个"补充需求"章节
2. 将反馈内容转化为需求描述放入该章节
3. 用紫色文字标记整个新增章节
4. 在输出中提示用户："以下反馈未找到文档中的对应位置，已新增到文档末尾，请确认是否需要调整位置。"

---

## 变更摘要（插入到文档目录下方）

每次更新完成后，**必须在文档目录（Table of Contents）的正下方插入一段变更摘要**，让读者打开文档后第一时间了解本次改了什么。如果文档没有目录，则插入到文档标题/封面之后、正文之前。

**重要**：变更摘要本身使用**黑色普通文字**（与文档正文一致），不使用紫色。紫色文字只出现在正文中实际被修改/新增的需求内容处。摘要中的每条修改记录必须带**超链接（书签跳转）**，点击即可定位到文档中对应的紫色修改内容。

### 插入位置规则

| 文档结构 | 变更摘要插入位置 |
|---------|---------------|
| 有目录（TOC） | 目录段落结束后、第一个正文章节之前 |
| 有封面/标题页，无目录 | 封面/标题页之后、第一个正文章节之前 |
| 无目录无封面 | 文档最前面，正文第一个标题之前 |

### 变更摘要内容格式

摘要为黑色普通文字，每条记录是一个可点击的超链接，跳转到正文中的对应修改位置：

```
📋 文档更新记录（更新日期：2025-XX-XX）

修改清单：
1. 【修改】第2.3节 "[流程名称]" - 补充了[修改内容描述]    → [点击跳转]
2. 【新增】第3.1节 "异常处理" - 新增网络超时的降级方案      → [点击跳转]
3. 【删除】第4.2节 "旧版接口" - 移除已废弃的接口描述        → [点击跳转]

标记说明：
- 🟣 紫色文字 = 正文中新增或修改的内容
- 删除线灰色文字 = 正文中被移除的内容

待确认项：
- 第2.3节的重试次数限制（3次）需产品确认
```

### 书签 + 超链接机制

核心原理：在正文中每处修改位置插入一个**书签（Bookmark）**作为锚点，然后在变更摘要中用**超链接**指向该书签。

**书签命名规范**：`_change_{序号}` ，如 `_change_1`、`_change_2`、`_change_3`。

流程如下：
1. 在正文中修改内容时，给每处修改包裹一个书签锚点
2. 在变更摘要中，每条记录用超链接指向对应书签
3. 读者点击摘要中的链接 → 自动跳转到正文中紫色修改内容所在位置

### 各格式的具体实现

#### docx 文件

**第1步：在正文修改位置添加书签锚点**

每处修改的紫色内容前后包裹书签标记，书签 ID 全局唯一递增。注意：新增/修改内容必须带日期标记前缀：

```xml
<!-- 在正文修改位置：书签包裹紫色内容（带日期标记） -->
<w:bookmarkStart w:id="100" w:name="_change_1"/>
<w:r>
  <w:rPr>
    <w:color w:val="7B2D8E"/>
  </w:rPr>
  <w:t>【04.01(月日）更新】新增或修改的需求内容</w:t>
</w:r>
<w:bookmarkEnd w:id="100"/>
```

对于"修改"类型（同时有删除线旧内容和紫色新内容），书签包裹整个修改区域：

```xml
<w:bookmarkStart w:id="100" w:name="_change_1"/>
<!-- 旧内容删除线 -->
<w:r>
  <w:rPr>
    <w:strike/>
    <w:color w:val="999999"/>
  </w:rPr>
  <w:t>旧的描述</w:t>
</w:r>
<!-- 新内容紫色，带日期标记 -->
<w:r>
  <w:rPr>
    <w:color w:val="7B2D8E"/>
  </w:rPr>
  <w:t>【04.01(月日）更新】新的描述</w:t>
</w:r>
<w:bookmarkEnd w:id="100"/>
```

**第2步：在目录下方插入黑色变更摘要（带超链接）**

找到目录结束位置后，插入以下段落。注意所有文字均为**黑色**，修改条目使用**内部超链接**指向书签：

```xml
<!-- 变更摘要标题：黑色加粗 -->
<w:p>
  <w:pPr>
    <w:spacing w:before="360" w:after="120"/>
  </w:pPr>
  <w:r>
    <w:rPr><w:b/><w:sz w:val="24"/></w:rPr>
    <w:t xml:space="preserve">&#x1F4CB; 文档更新记录（更新日期：2025-XX-XX）</w:t>
  </w:r>
</w:p>

<!-- 每条修改记录：黑色文字 + 超链接跳转到书签 -->
<w:p>
  <w:hyperlink w:anchor="_change_1" w:history="1">
    <w:r>
      <w:rPr>
        <w:rStyle w:val="Hyperlink"/>
      </w:rPr>
      <w:t>1. 【修改】第2.3节 "[流程名称]" - 补充了[修改内容描述]</w:t>
    </w:r>
  </w:hyperlink>
</w:p>

<w:p>
  <w:hyperlink w:anchor="_change_2" w:history="1">
    <w:r>
      <w:rPr>
        <w:rStyle w:val="Hyperlink"/>
      </w:rPr>
      <w:t>2. 【新增】第3.1节 "异常处理" - 新增网络超时的降级方案</w:t>
    </w:r>
  </w:hyperlink>
</w:p>

<w:p>
  <w:hyperlink w:anchor="_change_3" w:history="1">
    <w:r>
      <w:rPr>
        <w:rStyle w:val="Hyperlink"/>
      </w:rPr>
      <w:t>3. 【删除】第4.2节 "旧版接口" - 移除已废弃的接口描述</w:t>
    </w:r>
  </w:hyperlink>
</w:p>

<!-- 标记说明：黑色小号文字 -->
<w:p>
  <w:r>
    <w:rPr><w:sz w:val="18"/><w:color w:val="666666"/></w:rPr>
    <w:t xml:space="preserve">标记说明：🟣 紫色文字=正文中新增/修改的内容  删除线灰色文字=移除的内容</w:t>
  </w:r>
</w:p>

<!-- 分隔线 -->
<w:p>
  <w:pPr>
    <w:pBdr>
      <w:bottom w:val="single" w:sz="6" w:space="1" w:color="CCCCCC"/>
    </w:pBdr>
    <w:spacing w:after="360"/>
  </w:pPr>
</w:p>
```

**注意事项**：
- `w:anchor` 属性值必须与正文中 `w:bookmarkStart` 的 `w:name` 完全一致
- `w:id` 在整个文档中必须唯一递增，不能与已有书签/批注 ID 冲突
- 如果文档中没有定义 `Hyperlink` 样式，需要在 `word/styles.xml` 中添加，或改用内联样式：
  ```xml
  <w:r>
    <w:rPr>
      <w:color w:val="0563C1"/>
      <w:u w:val="single"/>
    </w:rPr>
    <w:t>链接文字</w:t>
  </w:r>
  ```

**定位目录的方法**：
1. 搜索 `<w:sdt>` 中包含 `<w:docPartGallery w:val="Table of Contents"/>` 的结构化文档标签 → 在 `</w:sdt>` 后插入
2. 如果没有 SDT 结构，搜索包含 TOC 域代码的段落（`<w:fldChar>`...`TOC`...）→ 在最后一个 TOC 相关段落后插入
3. 如果没有目录，搜索第一个 `<w:pStyle w:val="Heading1"/>` → 在其前面插入

#### Markdown 文件

在正文修改处插入 HTML 锚点，摘要中用链接跳转：

**正文修改位置添加锚点（带日期标记）：**
```markdown
<a id="change-1"></a><span style="color: #7B2D8E;">【04.01(月日）更新】新增或修改的需求内容</span>
```

**目录下方的变更摘要（黑色文字+链接）：**
```markdown
---

**📋 文档更新记录（更新日期：2025-XX-XX）**

1. [【修改】第2.3节 "[流程名称]" - 补充了[修改内容描述]](#change-1)
2. [【新增】第3.1节 "异常处理" - 新增网络超时的降级方案](#change-2)
3. [【删除】第4.2节 "旧版接口" - 移除已废弃的接口描述](#change-3)

> 标记说明：🟣 紫色文字=正文中新增/修改  ~~删除线~~=移除

---
```

**定位目录的方法**：
1. 搜索 `[TOC]` 或 `[[toc]]` 标记 → 在其下一行插入
2. 搜索连续的 `- [章节名](#anchor)` 格式的手写目录块 → 在块结束后插入
3. 如果没有目录，在第一个 `## ` 二级标题之前插入

#### HTML 文件

**正文修改位置添加锚点（带日期标记）：**
```html
<span id="change-1" class="doc-added">【04.01(月日）更新】新增或修改的需求内容</span>
```

**目录下方的变更摘要（黑色文字+链接）：**
```html
<div class="change-summary" style="border-left: 4px solid #CCCCCC; padding: 12px 16px; margin: 20px 0;">
  <h3 style="margin-top: 0;">📋 文档更新记录</h3>
  <ol>
    <li><a href="#change-1">【修改】第2.3节 "[流程名称]" - 补充了[修改内容描述]</a></li>
    <li><a href="#change-2">【新增】第3.1节 "异常处理" - 新增网络超时的降级方案</a></li>
    <li><a href="#change-3">【删除】第4.2节 "旧版接口" - 移除已废弃的接口描述</a></li>
  </ol>
  <p style="color: #666; font-size: 0.9em;">标记说明：🟣 紫色文字=正文中新增/修改 · <del>删除线</del>=移除</p>
</div>
```

**定位方法**：搜索 `<nav>` 目录导航、`id="toc"` 元素或 `class="table-of-contents"` → 在其后插入。

#### Notion 页面

使用 Notion MCP 工具在目录块（Table of Contents block）下方插入：
- 一个 **callout block**（灰色/默认样式，非紫色），内容为变更摘要标题
- 每条修改记录作为子内容，使用 Notion 的 **mention/link to block** 功能链接到正文中对应的修改位置
- 正文中的修改内容使用紫色高亮标记

### 同时在回复中附带摘要

除了在文档中插入变更摘要外，回复消息中也应简要列出修改清单，方便用户快速了解本次变更而不必打开文档。

---

## 反例与黑名单

以下操作是**明确禁止**的危险动作，执行任何一项都会破坏文档完整性或导致用户数据丢失。

| # | 禁止操作 | 后果 | 正确做法 |
|---|---------|------|---------|
| 1 | 🔴 **未经 🔴 CHECKPOINT 确认直接修改文档** | 误改、漏改、过度修改，用户无法追溯 | 第三步半必须展示修改计划，等用户明确确认后再执行 |
| 2 | **破坏表格结构**（增删列、改宽度、删行、改合并单元格） | 表格渲染错乱，数据错位 | 只在单元格内部做标记，新增行只能追加在末尾，删除行用删除线保留结构 |
| 3 | **在代码块内部插入 `<span>` 或 HTML 标记** | Markdown/HTML 代码块语法被破坏，无法渲染 | 在代码块外部用注释标注变更，代码内容直接替换不加标记 |
| 4 | **重复使用相同的书签 ID** | Word 文档内部链接失效，点击跳转异常 | 书签 ID 全局唯一递增，与已有书签/批注 ID 不冲突 |
| 5 | **修改与反馈无关的内容** | 引入未经验证的变更，文档版本混乱 | 严格遵循最小改动原则，只修改反馈涉及的位置 |
| 6 | **把变更摘要、修订历史用紫色文字标记** | 元信息被误当作需求正文，颜色语义混乱 | 变更摘要和修订历史使用黑色普通文字 |
| 7 | **在 frontmatter（`---` 之间）插入 HTML 标记** | YAML 解析失败，frontmatter 损坏 | 仅更新 YAML 字段值，不加任何 HTML/XML 标记 |
| 8 | **直接删除表格的 `<w:tr>` 或 Markdown 行** | 表格行数/列数变化，后续内容错位 | 保留完整行结构，对单元格内容加删除线 |
| 9 | **未验证输入缺失就直接开始解析** | 缺少需求文档或反馈信息，流程空转或报错 | 第一步即检查两类输入是否齐全，缺失时明确停止并提示用户 |
| 10 | **跨越 `<w:r>` run 边界做文本替换** | XML 结构被破坏，Word 打开报错 | 在单个 run 内部操作，或拆分/重建 run 时保持 XML 闭合 |

**特别警告**：本 skill 涉及直接编辑用户文档的底层结构（Word XML、Markdown 源码、HTML DOM），任何结构性破坏都可能导致文档无法打开或内容丢失。**当对某处修改没有十足把握时，宁可跳过该处并向用户说明，也不要冒险执行。**

---

## 使用注意事项

1. **日期标记原则（新增）**：对于 Markdown 和 docx 格式的文档，所有新增/修改内容**必须**在前面添加【XX.XX(月日）更新】标记，使用紫色文字
2. **颜色使用原则**：紫色文字**仅用于正文中实际修改/新增的需求内容**；变更摘要、修订历史表等均为**黑色普通文字**
3. **表格保护原则**：更新涉及表格时，**严禁破坏表格结构**（不增删列、不改宽度/合并/边框），只在单元格内部按字段粒度做紫色/删除线标记；新增行只能追加在表格末尾
4. **修订历史必须更新**：每次文档变更后，必须在修订历史表中追加一条新记录（版本号、日期、修订人、修订内容摘要）；如果文档没有修订历史表则自动创建
5. **变更摘要位置**：变更摘要必须插入到文档目录下方，每条记录带超链接可跳转到正文对应修改处
6. **保持文档结构**：更新时不改变原文档的整体结构和排版风格，只在需要修改的位置做精确调整
7. **最小改动原则**：只修改反馈涉及的内容，不对无关内容做调整
8. **保留上下文**：修改时保留足够的上下文，让读者能理解变更的前因后果
9. **反馈溯源**：在变更摘要和修订历史中标注修改对应的反馈来源（如"来自测试用例TC-001"）

---

## 与其他 Skill 的协作

- 读取 .docx 文件时，先使用 `docx` skill 的读取能力
- 读取 .pdf 文件时，使用 `pdf` skill 的提取能力
- **读取 .xlsx/.xls/.csv 反馈文件时，使用 `xlsx` skill 的读取能力**
- 编辑 .docx 文件时，遵循 `docx` skill 的 XML 编辑规范
- 创建新的 .docx 输出时，遵循 `docx` skill 的创建规范
- 读取 Notion 内容时，使用 Notion MCP 工具
- 读取上传文件时，使用文件读取工具处理
