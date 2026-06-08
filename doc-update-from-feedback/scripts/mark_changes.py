#!/usr/bin/env python3
"""
mark_changes.py - 在解包后的 docx XML 中标记文档变更

用法：
  python mark_changes.py <unpacked_dir> <changes_json>

changes_json 格式：
[
  {
    "type": "modify",          // modify | add | delete
    "target_text": "旧文本",   // 要查找的原文（modify/delete 必填）
    "new_text": "新文本",      // 替换后的文本（modify/add 必填）
    "after_text": "插入锚点",  // 在此文本之后插入（add 类型可选）
    "section": "章节名"        // 可选，缩小搜索范围
  }
]

标记规则：
- 新增/修改内容：紫色文字 (#7B2D8E)
- 删除内容：删除线 + 灰色文字 (#999999)
"""

import json
import re
import sys
import os


PURPLE = "7B2D8E"
GRAY = "999999"


def make_purple_run(text):
    """生成紫色文字的 XML run"""
    escaped = escape_xml(text)
    preserve = ' xml:space="preserve"' if text.startswith(' ') or text.endswith(' ') else ''
    return (
        f'<w:r><w:rPr><w:color w:val="{PURPLE}"/></w:rPr>'
        f'<w:t{preserve}>{escaped}</w:t></w:r>'
    )


def make_strikethrough_run(text):
    """生成删除线+灰色文字的 XML run"""
    escaped = escape_xml(text)
    preserve = ' xml:space="preserve"' if text.startswith(' ') or text.endswith(' ') else ''
    return (
        f'<w:r><w:rPr><w:strike/><w:color w:val="{GRAY}"/></w:rPr>'
        f'<w:t{preserve}>{escaped}</w:t></w:r>'
    )


def escape_xml(text):
    """转义 XML 特殊字符"""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&#x2019;")
    return text


def find_and_replace_in_xml(xml_content, target_text, replacement_xml):
    """
    在 XML 中查找包含 target_text 的 <w:t> 元素并替换对应的 <w:r> 块。
    返回 (modified_xml, success_bool)
    """
    # 提取所有 run 及其文本
    run_pattern = re.compile(r'(<w:r\b[^>]*>.*?</w:r>)', re.DOTALL)
    text_pattern = re.compile(r'<w:t[^>]*>(.*?)</w:t>', re.DOTALL)

    runs = list(run_pattern.finditer(xml_content))
    if not runs:
        return xml_content, False

    # 构建 run 索引：连续 run 的文本拼接
    run_texts = []
    for run_match in runs:
        t_match = text_pattern.search(run_match.group())
        run_texts.append(t_match.group(1) if t_match else "")

    # 尝试在连续 run 的拼接文本中找到 target_text
    full_text = "".join(run_texts)

    # 先对 target_text 做 XML 转义以便匹配
    escaped_target = escape_xml(target_text)

    idx = full_text.find(escaped_target)
    if idx == -1:
        # 尝试不转义的版本
        idx = full_text.find(target_text)
        if idx == -1:
            return xml_content, False

    # 找到包含目标文本的 run 范围
    char_pos = 0
    start_run = -1
    end_run = -1
    for i, rt in enumerate(run_texts):
        if start_run == -1 and char_pos + len(rt) > idx:
            start_run = i
        if start_run != -1 and char_pos + len(rt) >= idx + len(escaped_target if escaped_target in full_text else target_text):
            end_run = i
            break
        char_pos += len(rt)

    if start_run == -1 or end_run == -1:
        return xml_content, False

    # 替换这些 run
    first_run_start = runs[start_run].start()
    last_run_end = runs[end_run].end()

    modified = xml_content[:first_run_start] + replacement_xml + xml_content[last_run_end:]
    return modified, True


def apply_changes(unpacked_dir, changes):
    """应用变更到解包后的 docx"""
    doc_path = os.path.join(unpacked_dir, "word", "document.xml")

    if not os.path.exists(doc_path):
        print(f"Error: {doc_path} not found")
        return False

    with open(doc_path, "r", encoding="utf-8") as f:
        xml_content = f.read()

    results = []

    for i, change in enumerate(changes):
        change_type = change.get("type", "modify")
        target_text = change.get("target_text", "")
        new_text = change.get("new_text", "")
        success = False

        if change_type == "modify" and target_text and new_text:
            # 修改：删除线旧文本 + 紫色新文本
            replacement = make_strikethrough_run(target_text) + make_purple_run(new_text)
            xml_content, success = find_and_replace_in_xml(xml_content, target_text, replacement)

        elif change_type == "delete" and target_text:
            # 删除：删除线标记
            replacement = make_strikethrough_run(target_text)
            xml_content, success = find_and_replace_in_xml(xml_content, target_text, replacement)

        elif change_type == "add" and new_text:
            after_text = change.get("after_text", "")
            if after_text:
                # 在指定文本之后插入紫色文字
                anchor_run = f'<w:t'
                # 找到 after_text 所在的 run，在其后插入
                insertion = make_purple_run(new_text)
                # 简单策略：在 after_text 对应的 </w:r> 后插入
                xml_content, success = find_and_insert_after(xml_content, after_text, insertion)
            else:
                # 在文档末尾的 </w:body> 前插入新段落
                new_para = (
                    f'<w:p><w:pPr><w:rPr><w:color w:val="{PURPLE}"/></w:rPr></w:pPr>'
                    + make_purple_run(new_text)
                    + '</w:p>'
                )
                xml_content = xml_content.replace('</w:body>', new_para + '</w:body>')
                success = True

        results.append({
            "index": i,
            "type": change_type,
            "target": target_text[:50] if target_text else "",
            "new": new_text[:50] if new_text else "",
            "success": success
        })

    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(xml_content)

    return results


def find_and_insert_after(xml_content, after_text, insertion_xml):
    """在包含 after_text 的 run 之后插入内容"""
    text_pattern = re.compile(r'<w:t[^>]*>(.*?)</w:t>', re.DOTALL)
    run_pattern = re.compile(r'(<w:r\b[^>]*>.*?</w:r>)', re.DOTALL)

    escaped = escape_xml(after_text)

    for run_match in run_pattern.finditer(xml_content):
        t_match = text_pattern.search(run_match.group())
        if t_match and (escaped in t_match.group(1) or after_text in t_match.group(1)):
            insert_pos = run_match.end()
            modified = xml_content[:insert_pos] + insertion_xml + xml_content[insert_pos:]
            return modified, True

    return xml_content, False


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python mark_changes.py <unpacked_dir> <changes_json_file>")
        sys.exit(1)

    unpacked_dir = sys.argv[1]
    changes_file = sys.argv[2]

    with open(changes_file, "r", encoding="utf-8") as f:
        changes = json.load(f)

    results = apply_changes(unpacked_dir, changes)
    print(json.dumps(results, ensure_ascii=False, indent=2))
