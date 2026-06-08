#!/usr/bin/env python3
"""
parse_excel_feedback.py - 从 Excel 文件中智能识别和提取反馈内容

用法：
  python parse_excel_feedback.py <excel_file> [--output <output_json>]

输出：标准化的反馈条目 JSON 列表，每条包含：
  - id: 编号
  - module: 所属模块/章节
  - title: 标题/描述
  - feedback: 反馈内容
  - suggestion: 建议修改
  - original: 原文
  - priority: 优先级
  - type: 变更类型 (modify/add/delete)
  - source: 来源（sheet名 + 行号）
"""

import json
import sys
import os
import argparse

try:
    import pandas as pd
except ImportError:
    print("Error: pandas is required. Install with: pip install pandas openpyxl")
    sys.exit(1)


# 各角色的识别关键词
ROLE_KEYWORDS = {
    "id": ["编号", "id", "序号", "no.", "编码", "no", "用例编号", "tc_id", "case id", "变更编号", "cr编号", "change id"],
    "title": ["标题", "名称", "title", "summary", "描述", "测试项", "用例名", "bug标题", "缺陷描述", "变更内容"],
    "module": ["模块", "module", "功能", "页面", "章节", "section", "位置", "location", "所属模块", "功能模块", "影响范围", "impact", "影响模块"],
    "status": ["结果", "状态", "status", "result", "是否通过", "测试结果"],
    "actual": ["实际", "actual", "现象", "表现", "bug描述", "实际结果", "实际表现"],
    "expected": ["预期", "expected", "期望", "预期结果", "期望表现"],
    "feedback": ["意见", "反馈", "feedback", "comment", "备注", "说明", "remark", "建议", "评审意见", "变更原因", "reason"],
    "suggestion": ["建议修改", "修改为", "suggestion", "变更后", "after", "新需求", "修改建议"],
    "original": ["原文", "original", "变更前", "before", "当前描述", "原始", "原始需求"],
    "priority": ["优先级", "priority", "严重", "severity", "紧急", "等级", "严重程度"],
    "type": ["类型", "type", "操作", "变更类型"],
    "author": ["提出人", "author", "反馈人", "提交人", "测试人", "评审人"],
    "steps": ["复现步骤", "steps", "操作步骤", "step"],
}


def identify_column_role(col_name):
    """根据关键词匹配列的角色"""
    col_lower = str(col_name).lower().strip()
    for role, keywords in ROLE_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in col_lower:
                return role
    return None


def find_header_row(filepath, sheet_name=0, max_scan=5):
    """尝试在前 N 行中找到有效表头"""
    for skip in range(max_scan):
        try:
            df = pd.read_excel(filepath, sheet_name=sheet_name, skiprows=skip, nrows=1)
            roles = [identify_column_role(c) for c in df.columns]
            valid_roles = [r for r in roles if r is not None]
            if len(valid_roles) >= 2:  # 至少识别出2个角色才认为找到了表头
                return skip
        except Exception:
            continue
    return 0  # 默认无跳过


def build_column_mapping(df):
    """构建 列名 → 角色 的映射"""
    mapping = {}  # role -> column_name
    for col in df.columns:
        role = identify_column_role(col)
        if role and role not in mapping:
            mapping[role] = col
    return mapping


def infer_change_type(row, mapping):
    """推断变更类型"""
    # 优先使用显式类型列
    if "type" in mapping:
        type_val = str(row.get(mapping["type"], "")).strip().lower()
        if type_val in ["新增", "add", "补充"]:
            return "add"
        elif type_val in ["删除", "delete", "移除", "废弃"]:
            return "delete"
        elif type_val in ["修改", "modify", "变更", "调整", "update"]:
            return "modify"

    # 根据内容推断
    has_original = "original" in mapping and pd.notna(row.get(mapping.get("original", ""), None))
    has_suggestion = "suggestion" in mapping and pd.notna(row.get(mapping.get("suggestion", ""), None))
    has_feedback = "feedback" in mapping and pd.notna(row.get(mapping.get("feedback", ""), None))

    suggestion_val = str(row.get(mapping.get("suggestion", ""), "")).strip().lower()
    if suggestion_val in ["删除", "delete", "移除", "废弃"]:
        return "delete"

    if has_original and has_suggestion:
        return "modify"
    elif has_original and not has_suggestion:
        return "delete"
    elif not has_original and (has_suggestion or has_feedback):
        return "add"

    # 测试用例：失败 → 需要修改
    if "status" in mapping:
        status = str(row.get(mapping["status"], "")).strip().lower()
        if status in ["失败", "fail", "failed", "不通过", "blocked", "阻塞"]:
            return "modify"

    return "modify"  # 默认修改


def safe_str(val):
    """安全转换为字符串，处理 NaN"""
    if pd.isna(val):
        return ""
    return str(val).strip()


def extract_feedback_items(df, column_mapping, sheet_name="Sheet1"):
    """将 DataFrame 转化为标准反馈条目列表"""
    items = []
    for idx, row in df.iterrows():
        item = {}
        for role in ["id", "module", "title", "feedback", "suggestion", "original", "priority", "actual", "expected", "author", "steps", "status"]:
            col = column_mapping.get(role, "")
            item[role] = safe_str(row.get(col, "")) if col else ""

        # 推断变更类型
        item["type"] = infer_change_type(row, column_mapping)

        # 组合反馈内容：如果没有专门的 feedback 列，从其他列组合
        if not item["feedback"]:
            parts = []
            if item["actual"]:
                parts.append(f"实际结果: {item['actual']}")
            if item["expected"]:
                parts.append(f"预期结果: {item['expected']}")
            if item["steps"]:
                parts.append(f"复现步骤: {item['steps']}")
            if item["title"] and not parts:
                parts.append(item["title"])
            item["feedback"] = "; ".join(parts)

        # 来源标识
        item["source"] = f"{sheet_name}:行{idx + 2}"

        # 跳过空行
        meaningful = [item.get(k, "") for k in ["title", "feedback", "suggestion", "original"]]
        if not any(v for v in meaningful):
            continue

        # 只保留标准字段
        clean_item = {k: item.get(k, "") for k in ["id", "module", "title", "feedback", "suggestion", "original", "priority", "type", "source", "author"]}
        items.append(clean_item)

    return items


def parse_excel(filepath):
    """解析整个 Excel 文件，返回所有反馈条目"""
    all_items = []

    # 判断文件类型
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(filepath)
        mapping = build_column_mapping(df)
        if mapping:
            items = extract_feedback_items(df, mapping, "CSV")
            all_items.extend(items)
        return all_items

    # Excel 文件：读取所有 sheet
    try:
        xl = pd.ExcelFile(filepath)
        sheet_names = xl.sheet_names
    except Exception as e:
        print(f"Error reading Excel file: {e}", file=sys.stderr)
        return []

    for sheet_name in sheet_names:
        try:
            # 找表头行
            skip = find_header_row(filepath, sheet_name=sheet_name)
            df = pd.read_excel(filepath, sheet_name=sheet_name, skiprows=skip)

            # 去除全空行
            df = df.dropna(how="all")

            # 构建列映射
            mapping = build_column_mapping(df)
            if not mapping:
                print(f"  Sheet '{sheet_name}': 未识别出有效列结构，跳过", file=sys.stderr)
                continue

            print(f"  Sheet '{sheet_name}': 识别到列映射 {json.dumps({k: v for k, v in mapping.items()}, ensure_ascii=False)}", file=sys.stderr)

            # 提取反馈条目
            items = extract_feedback_items(df, mapping, sheet_name)
            all_items.extend(items)
            print(f"  Sheet '{sheet_name}': 提取到 {len(items)} 条反馈", file=sys.stderr)

        except Exception as e:
            print(f"  Sheet '{sheet_name}': 解析失败 - {e}", file=sys.stderr)
            continue

    return all_items


def main():
    parser = argparse.ArgumentParser(description="从 Excel 文件中提取反馈内容")
    parser.add_argument("excel_file", help="Excel 文件路径 (.xlsx/.xls/.csv)")
    parser.add_argument("--output", "-o", help="输出 JSON 文件路径（默认输出到 stdout）")
    parser.add_argument("--pretty", action="store_true", help="美化 JSON 输出")
    args = parser.parse_args()

    if not os.path.exists(args.excel_file):
        print(f"Error: 文件不存在: {args.excel_file}", file=sys.stderr)
        sys.exit(1)

    print(f"解析文件: {args.excel_file}", file=sys.stderr)
    items = parse_excel(args.excel_file)
    print(f"共提取 {len(items)} 条反馈", file=sys.stderr)

    # 输出结果
    indent = 2 if args.pretty else None
    result = json.dumps(items, ensure_ascii=False, indent=indent)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"结果已保存到: {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
