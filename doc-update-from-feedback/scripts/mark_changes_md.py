#!/usr/bin/env python3
"""
mark_changes_md.py - 在 Markdown 文件中标记文档变更（结构感知版）

特性：
- 自动识别代码块、frontmatter、表格等特殊区域
- 代码块内部不插入 <span> 标记
- frontmatter 区域不插入 HTML 标记
- 表格内仅在单元格内容中标记，不破坏 | 分隔符
- 自动解析文档标题树用于反馈定位
- 自动生成变更摘要并插入目录下方（黑色文字+锚点链接）

用法：
  python mark_changes_md.py <input_file> <changes_json> <output_file>

changes_json 格式：
[
  {
    "type": "modify",          // modify | add | delete
    "target_text": "旧文本",   // 要查找的原文
    "new_text": "新文本",      // 替换后的文本
    "after_text": "插入锚点",  // 在此文本之后插入（add 类型可选）
    "section": "章节名"        // 可选，缩小搜索范围
  }
]
"""

import json
import sys
import re
import os


PURPLE_STYLE = 'color: #7B2D8E;'
STRIKE_STYLE = 'text-decoration: line-through; color: #999999;'


def mark_purple(text):
    return f'<span style="{PURPLE_STYLE}">{text}</span>'


def mark_strikethrough(text):
    return f'<span style="{STRIKE_STYLE}">{text}</span>'


# ============================================================
# Markdown 结构解析
# ============================================================

def parse_md_structure(lines):
    """解析 Markdown 文件结构，返回各区域信息"""
    structure = {
        "frontmatter": None,      # (start, end) 行号
        "code_blocks": [],        # [(start, end), ...]
        "tables": [],             # [(start, end), ...]
        "headings": [],           # [{"level":int, "title":str, "line":int}, ...]
        "toc_line": None,         # 目录结束行号
    }

    # --- frontmatter ---
    if lines and lines[0].strip() == '---':
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                structure["frontmatter"] = (0, i)
                break

    # --- 代码块 ---
    in_code = False
    code_start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('```'):
            if not in_code:
                in_code = True
                code_start = i
            else:
                in_code = False
                structure["code_blocks"].append((code_start, i))

    def is_in_code(line_num):
        return any(s <= line_num <= e for s, e in structure["code_blocks"])

    # --- 标题树 ---
    heading_pat = re.compile(r'^(#{1,6})\s+(.+)$')
    for i, line in enumerate(lines):
        if is_in_code(i):
            continue
        m = heading_pat.match(line)
        if m:
            structure["headings"].append({
                "level": len(m.group(1)),
                "title": m.group(2).strip(),
                "line": i
            })

    # --- 表格 ---
    table_pat = re.compile(r'^\|.*\|')
    in_table = False
    table_start = 0
    for i, line in enumerate(lines):
        if is_in_code(i):
            continue
        if table_pat.match(line.strip()):
            if not in_table:
                in_table = True
                table_start = i
        else:
            if in_table:
                structure["tables"].append((table_start, i - 1))
                in_table = False
    if in_table:
        structure["tables"].append((table_start, len(lines) - 1))

    # --- 目录位置 ---
    for i, line in enumerate(lines):
        stripped = line.strip().lower()
        if stripped in ['[toc]', '[[toc]]']:
            structure["toc_line"] = i
            break
    if structure["toc_line"] is None:
        link_pat = re.compile(r'^[\s]*[-*]\s*\[.+\]\(#.+\)')
        for i, line in enumerate(lines):
            if link_pat.match(line):
                last = i
                while last + 1 < len(lines) and link_pat.match(lines[last + 1]):
                    last += 1
                structure["toc_line"] = last
                break

    return structure


def is_in_range(line_num, ranges):
    return any(s <= line_num <= e for s, e in ranges)


def find_line_of_text(lines, text, structure, section=None):
    """
    在 Markdown 行中查找包含 text 的行号。
    如果指定 section，先限定搜索范围到该章节内。
    跳过 frontmatter 和代码块。
    """
    search_start = 0
    search_end = len(lines)

    if section:
        for idx, h in enumerate(structure["headings"]):
            if section.lower() in h["title"].lower():
                search_start = h["line"]
                for nh in structure["headings"][idx + 1:]:
                    if nh["level"] <= h["level"]:
                        search_end = nh["line"]
                        break
                break

    fm = structure.get("frontmatter")
    for i in range(search_start, search_end):
        if fm and fm[0] <= i <= fm[1]:
            continue
        if is_in_range(i, structure["code_blocks"]):
            continue
        if text in lines[i]:
            return i
    return -1


# ============================================================
# 变更应用
# ============================================================

def apply_change_to_line(line, target_text, replacement, line_num, structure):
    """在一行中做替换，感知表格/代码块等上下文"""
    if is_in_range(line_num, structure["code_blocks"]):
        # 代码块内：直接替换文本，不加 span
        plain_new = re.sub(r'<span[^>]*>|</span>', '', replacement)
        return line.replace(target_text, plain_new, 1)

    if is_in_range(line_num, structure["tables"]):
        # 表格分隔行不做修改
        if re.match(r'^\|[\s\-:|]+\|$', line.strip()):
            return line
        return line.replace(target_text, replacement, 1)

    return line.replace(target_text, replacement, 1)


def apply_changes(content, changes):
    """应用所有变更"""
    lines = content.split('\n')
    structure = parse_md_structure(lines)
    results = []
    change_counter = 0

    for i, change in enumerate(changes):
        change_type = change.get("type", "modify")
        target_text = change.get("target_text", "")
        new_text = change.get("new_text", "")
        section = change.get("section", "")
        success = False

        if change_type == "modify" and target_text and new_text:
            line_num = find_line_of_text(lines, target_text, structure, section)
            if line_num >= 0:
                change_counter += 1
                anchor = f'<a id="change-{change_counter}"></a>'
                replacement = anchor + mark_strikethrough(target_text) + " " + mark_purple(new_text)
                lines[line_num] = apply_change_to_line(
                    lines[line_num], target_text, replacement, line_num, structure
                )
                success = True

        elif change_type == "delete" and target_text:
            line_num = find_line_of_text(lines, target_text, structure, section)
            if line_num >= 0:
                change_counter += 1
                anchor = f'<a id="change-{change_counter}"></a>'
                replacement = anchor + mark_strikethrough(target_text)
                lines[line_num] = apply_change_to_line(
                    lines[line_num], target_text, replacement, line_num, structure
                )
                success = True

        elif change_type == "add" and new_text:
            after_text = change.get("after_text", "")
            change_counter += 1
            anchor = f'<a id="change-{change_counter}"></a>'
            if after_text:
                line_num = find_line_of_text(lines, after_text, structure, section)
                if line_num >= 0:
                    if is_in_range(line_num, structure["tables"]):
                        # 表格内新增：在表格末尾追加行
                        table_end = line_num
                        for ts, te in structure["tables"]:
                            if ts <= line_num <= te:
                                table_end = te
                                break
                        col_count = lines[line_num].count('|') - 1
                        if '|' in new_text:
                            cells = [mark_purple(c.strip()) for c in new_text.split('|')]
                        else:
                            cells = [mark_purple(new_text)] + [mark_purple(' ')] * (col_count - 1)
                        new_row = '| ' + ' | '.join(cells) + ' |'
                        lines.insert(table_end + 1, anchor + new_row)
                    else:
                        lines.insert(line_num + 1, anchor + mark_purple(new_text))
                    success = True
            else:
                section_name = section or "补充需求"
                lines.append(f"\n## {section_name}\n")
                lines.append(anchor + mark_purple(new_text))
                success = True

        results.append({
            "index": i,
            "change_id": change_counter if success else None,
            "type": change_type,
            "target": target_text[:50] if target_text else "",
            "new": new_text[:50] if new_text else "",
            "success": success
        })

    modified_content = '\n'.join(lines)
    return modified_content, results, change_counter


def generate_summary_block(changes_input, results):
    """生成变更摘要文本块（黑色文字+锚点链接）"""
    from datetime import date
    today = date.today().strftime("%Y-%m-%d")

    summary_lines = [
        "",
        "---",
        "",
        f"**📋 文档更新记录（更新日期：{today}）**",
        "",
    ]
    type_labels = {"modify": "修改", "delete": "删除", "add": "新增"}
    count = 0
    for ci, r in zip(changes_input, results):
        if not r["success"]:
            continue
        count += 1
        cid = r["change_id"]
        label = type_labels.get(r["type"], "修改")
        desc = ci.get("new_text") or ci.get("target_text") or ""
        if len(desc) > 60:
            desc = desc[:60] + "..."
        section = ci.get("section", "")
        prefix = f'{section} - ' if section else ''
        summary_lines.append(
            f'{count}. [【{label}】{prefix}{desc}](#change-{cid})'
        )

    summary_lines.extend([
        "",
        "> 标记说明：🟣 紫色文字=正文中新增/修改  ~~删除线~~=移除",
        "",
        "---",
        "",
    ])
    return '\n'.join(summary_lines)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python mark_changes_md.py <input_file> <changes_json> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    changes_file = sys.argv[2]
    output_file = sys.argv[3]

    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    with open(changes_file, "r", encoding="utf-8") as f:
        changes = json.load(f)

    modified_content, results, change_count = apply_changes(content, changes)

    # 生成并插入变更摘要
    if any(r["success"] for r in results):
        summary = generate_summary_block(changes, results)
        lines = modified_content.split('\n')
        structure = parse_md_structure(lines)
        insert_at = 0
        if structure["toc_line"] is not None:
            insert_at = structure["toc_line"] + 1
        elif structure["frontmatter"] is not None:
            insert_at = structure["frontmatter"][1] + 1
        elif structure["headings"]:
            insert_at = structure["headings"][0]["line"]
        lines.insert(insert_at, summary)
        modified_content = '\n'.join(lines)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(modified_content)

    print(json.dumps(results, ensure_ascii=False, indent=2))
