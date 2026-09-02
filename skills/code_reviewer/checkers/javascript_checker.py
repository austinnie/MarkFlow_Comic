"""
JavaScript/TypeScript 代码检查器
使用: eslint
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from .base import BaseChecker


class JavaScriptChecker(BaseChecker):
    """JavaScript/TypeScript 代码检查器"""
    
    def check(self, files: List[str], focus: str, review_level: str, max_files: int) -> Dict[str, Any]:
        issues = []
        tools = []
        
        files = self._limit_files(files, max_files)
        
        # 检查是否有 eslint
        has_eslint = self._check_eslint()
        
        for file_path in files:
            # ESLint
            if has_eslint:
                result = self._run_eslint(file_path)
                if result.get("issues"):
                    issues.extend(result["issues"])
                    if "eslint" not in tools:
                        tools.append("eslint")
        
        score = self._calculate_score(issues)
        
        return {
            "tools": tools,
            "issues": issues,
            "score": score,
            "files_checked": len(files),
        }
    
    def _check_eslint(self) -> bool:
        """检查 eslint 是否可用"""
        try:
            result = subprocess.run(
                ["npx", "eslint", "--version"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _run_eslint(self, file_path: str) -> Dict:
        try:
            result = subprocess.run(
                ["npx", "eslint", file_path, "--format=json"],
                capture_output=True, text=True, timeout=60
            )
            issues = []
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    for item in data:
                        for message in item.get("messages", []):
                            issues.append({
                                "tool": "eslint",
                                "type": message.get("ruleId", "unknown"),
                                "severity": "high" if message.get("severity") == 2 else "medium",
                                "message": message.get("message", ""),
                                "line": message.get("line", 0),
                                "file": file_path,
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
            if severity == "high":
                score -= 3
            elif severity == "medium":
                score -= 1.5
            else:
                score -= 0.5
        return max(0, min(100, int(score)))