"""
测试 code_reviewer 技能 - 显示详细报告
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from markflow.cli.commands import execute_skill


def print_report(result, title):
    """打印审查报告"""
    if not result or not isinstance(result, dict):
        print("❌ 执行失败")
        return
    
    print("\n" + "=" * 70)
    print(f"📊 {title}")
    print("=" * 70)
    
    # 如果是错误
    if result.get("status") == "error":
        print(f"❌ 错误: {result.get('error', '未知错误')}")
        return
    
    # 获取结果数据
    result_data = result.get("result", {})
    
    print(f"📁 审查路径: {result_data.get('code_path', '未知')}")
    print(f"📄 总文件数: {result_data.get('total_files', 0)}")
    print(f"🌐 语言: {', '.join(result_data.get('languages', []))}")
    print(f"📊 总体评分: {result_data.get('overall_score', 0)}/100")
    print(f"🐛 问题总数: {result_data.get('issues_count', 0)}")
    
    # 按语言显示结果
    results_by_lang = result_data.get("results_by_language", [])
    if results_by_lang:
        print("\n" + "-" * 70)
        print("📋 各语言详情:")
        print("-" * 70)
        for lang_result in results_by_lang:
            lang = lang_result.get("language", "unknown")
            files = lang_result.get("files", 0)
            issues = lang_result.get("issues_count", 0)
            score = lang_result.get("score", 0)
            tools = ", ".join(lang_result.get("tools", []))
            error = lang_result.get("error", "")
            
            if error:
                print(f"  ❌ {lang.upper()}: {error}")
            else:
                status_icon = "✅" if score >= 70 else "⚠️" if score >= 50 else "❌"
                print(f"  {status_icon} {lang.upper()}: {files} 个文件, {issues} 个问题, 评分 {score}/100")
                if tools:
                    print(f"     🛠️  工具: {tools}")
    
    # 显示前 5 个问题
    issues = result_data.get("issues", [])
    if issues:
        print("\n" + "-" * 70)
        print("🐛 前 5 个问题:")
        print("-" * 70)
        for i, issue in enumerate(issues[:5], 1):
            file_path = issue.get("file", "未知文件")
            # 简化文件路径
            file_name = Path(file_path).name if file_path else "未知"
            severity = issue.get("severity", "unknown")
            severity_icon = "🔴" if severity == "critical" else "🟠" if severity == "high" else "🟡" if severity == "medium" else "🟢"
            message = issue.get("message", "")
            line = issue.get("line", 0)
            
            print(f"  {i}. {severity_icon} [{severity}] {file_name}:{line}")
            print(f"     {message[:100]}")
            if len(message) > 100:
                print(f"     ...")
    
    # 报告文件位置
    report_file = result_data.get("report_file")
    if not report_file:
        # 尝试从元数据获取
        metadata = result.get("metadata", {})
        # 实际上报告文件在 result_data 里没有，需要从日志中获取
    
    print("\n" + "-" * 70)
    print(f"📁 报告保存在: skills/code_reviewer/output/")
    print("=" * 70)


def view_latest_report():
    """查看最新报告内容"""
    report_dir = Path("skills/code_reviewer/output")
    if not report_dir.exists():
        print("❌ 报告目录不存在")
        return
    
    reports = list(report_dir.glob("review_*.json"))
    if not reports:
        print("❌ 未找到报告文件")
        return
    
    # 获取最新报告
    latest = max(reports, key=lambda p: p.stat().st_mtime)
    
    print("\n" + "=" * 70)
    print(f"📄 最新报告: {latest.name}")
    print("=" * 70)
    
    with open(latest, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    result_data = data.get("result", data)
    
    print(f"📁 审查路径: {result_data.get('code_path', '未知')}")
    print(f"📊 评分: {result_data.get('overall_score', 0)}/100")
    print(f"🐛 问题数: {result_data.get('issues_count', 0)}")
    
    # 显示问题列表
    issues = result_data.get("issues", [])
    if issues:
        print("\n📋 问题列表:")
        print("-" * 50)
        for i, issue in enumerate(issues[:20], 1):
            file_path = issue.get("file", "")
            file_name = Path(file_path).name if file_path else "未知"
            severity = issue.get("severity", "unknown")
            message = issue.get("message", "")
            line = issue.get("line", 0)
            print(f"  {i:2d}. [{severity:8}] {file_name}:{line} - {message[:60]}")
    
    print("\n" + "=" * 70)


def test_reviewer():
    """测试代码审查"""
    
    # 测试 1: 审查 markflow 目录
    print("\n" + "=" * 70)
    print("🚀 测试 1: 审查 markflow 框架代码")
    print("=" * 70)
    
    result = execute_skill("code_reviewer", code_path="./markflow")
    print_report(result, "markflow 框架审查结果")
    
    # 测试 2: 审查单个文件
    print("\n" + "=" * 70)
    print("🚀 测试 2: 审查单个文件 (generate_all_girls.py)")
    print("=" * 70)
    
    result = execute_skill("code_reviewer", code_path="./scripts/generate_all_girls.py")
    print_report(result, "单文件审查结果")
    
    # 测试 3: 只检查安全
    print("\n" + "=" * 70)
    print("🚀 测试 3: 只检查安全问题 (markflow)")
    print("=" * 70)
    
    result = execute_skill("code_reviewer", code_path="./markflow", focus="security")
    print_report(result, "安全审查结果")
    
    # 查看最新报告
    view_latest_report()


if __name__ == "__main__":
    test_reviewer()