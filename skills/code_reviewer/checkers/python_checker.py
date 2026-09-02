"""
Python 代码检查器
使用: pylint, flake8, bandit, radon
"""

import json
import subprocess
from typing import Dict, Any, List, Optional
from .base import BaseChecker


class PythonChecker(BaseChecker):
    """Python 代码检查器"""
    
    def check(self, files: List[str], focus: str, review_level: str, max_files: int) -> Dict[str, Any]:
        issues = []
        tools = []
        
        files = self._limit_files(files, max_files)
        
        for file_path in files:
            # pylint - 综合检查
            if focus in ["all", "style", "performance"]:
                result = self._run_pylint(file_path)
                if result.get("issues"):
                    issues.extend(result["issues"])
                    if "pylint" not in tools:
                        tools.append("pylint")
            
            # flake8 - 代码风格
            if focus in ["all", "style"]:
                result = self._run_flake8(file_path)
                if result.get("issues"):
                    issues.extend(result["issues"])
                    if "flake8" not in tools:
                        tools.append("flake8")
            
            # bandit - 安全扫描
            if focus in ["all", "security"]:
                result = self._run_bandit(file_path)
                if result.get("issues"):
                    issues.extend(result["issues"])
                    if "bandit" not in tools:
                        tools.append("bandit")
            
            # radon - 复杂度分析
            if focus in ["all", "performance"]:
                result = self._run_radon(file_path)
                if result.get("issues"):
                    issues.extend(result["issues"])
                    if "radon" not in tools:
                        tools.append("radon")
        
        score = self._calculate_score(issues)
        
        return {
            "tools": tools,
            "issues": issues,
            "score": score,
            "files_checked": len(files),
        }
    
    def _run_pylint(self, file_path: str) -> Dict:
        try:
            result = subprocess.run(
                ["python", "-m", "pylint", file_path, "--output-format=json"],
                capture_output=True, text=True, timeout=60
            )
            if result.stdout:
                data = json.loads(result.stdout)
                issues = []
                for item in data:
                    issues.append({
                        "tool": "pylint",
                        "type": item.get("type", "convention"),
                        "severity": "high" if item.get("type") == "error" else "medium",
                        "message": item.get("message", ""),
                        "line": item.get("line", 0),
                        "symbol": item.get("symbol", ""),
                        "file": file_path,
                    })
                return {"issues": issues}
            return {"issues": []}
        except Exception as e:
            return {"issues": [], "error": str(e)}
    
    def _run_flake8(self, file_path: str) -> Dict:
        try:
            result = subprocess.run(
                ["python", "-m", "flake8", file_path, "--format=json"],
                capture_output=True, text=True, timeout=30
            )
            issues = []
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    for file_key, file_issues in data.items():
                        for item in file_issues:
                            issues.append({
                                "tool": "flake8",
                                "type": "style",
                                "severity": "low",
                                "code": item.get("code", ""),
                                "message": item.get("text", ""),
                                "line": item.get("line_number", 0),
                                "file": file_path,
                            })
                except json.JSONDecodeError:
                    for line in result.stdout.strip().split("\n"):
                        if line:
                            issues.append({
                                "tool": "flake8",
                                "type": "style",
                                "severity": "low",
                                "message": line,
                                "file": file_path,
                            })
            return {"issues": issues}
        except Exception as e:
            return {"issues": [], "error": str(e)}
    
    def _run_bandit(self, file_path: str) -> Dict:
        try:
            result = subprocess.run(
                ["python", "-m", "bandit", "-r", file_path, "-f", "json"],
                capture_output=True, text=True, timeout=60
            )
            issues = []
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    for item in data.get("results", []):
                        severity = item.get("issue_severity", "MEDIUM").lower()
                        issues.append({
                            "tool": "bandit",
                            "type": "security",
                            "severity": "critical" if severity == "high" else severity,
                            "message": item.get("issue_text", ""),
                            "line": item.get("line_number", 0),
                            "code": item.get("code", ""),
                            "file": file_path,
                        })
                except json.JSONDecodeError:
                    pass
            return {"issues": issues}
        except Exception as e:
            return {"issues": [], "error": str(e)}
    
    def _run_radon(self, file_path: str) -> Dict:
        try:
            issues = []
            cc_result = subprocess.run(
                ["python", "-m", "radon", "cc", file_path, "-j"],
                capture_output=True, text=True, timeout=30
            )
            if cc_result.stdout:
                try:
                    data = json.loads(cc_result.stdout)
                    for file_key, items in data.items():
                        for item in items:
                            complexity = item.get("complexity", 0)
                            if complexity > 10:
                                issues.append({
                                    "tool": "radon",
                                    "type": "performance",
                                    "severity": "high" if complexity > 20 else "medium",
                                    "message": f"函数 {item.get('name', '')} 圈复杂度 {complexity}，建议拆分",
                                    "line": item.get("lineno", 0),
                                    "file": file_path,
                                    "complexity": complexity,
                                })
                except json.JSONDecodeError:
                    pass
            return {"issues": issues}
        except Exception as e:
            return {"issues": [], "error": str(e)}
    
    def _calculate_score(self, issues: List[Dict]) -> int:
        score = 100
        for issue in issues:
            severity = issue.get("severity", "medium")
            if severity == "critical":
                score -= 5
            elif severity == "high":
                score -= 3
            elif severity == "medium":
                score -= 1.5
            else:
                score -= 0.5
        return max(0, min(100, int(score)))