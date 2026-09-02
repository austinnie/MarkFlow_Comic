"""
Go 代码检查器
使用: golint, staticcheck, go vet
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from .base import BaseChecker


class GoChecker(BaseChecker):
    """Go 代码检查器"""
    
    def check(self, files: List[str], focus: str, review_level: str, max_files: int) -> Dict[str, Any]:
        issues = []
        tools = []
        
        files = self._limit_files(files, max_files)
        
        # 检查 Go 环境
        has_go = self._check_go()
        
        if not has_go:
            return {
                "tools": [],
                "issues": [],
                "score": 0,
                "error": "Go not installed",
                "files_checked": 0,
            }
        
        for file_path in files:
            # go vet - 基础检查
            if focus in ["all", "security"]:
                result = self._run_go_vet(file_path)
                if result.get("issues"):
                    issues.extend(result["issues"])
                    if "go vet" not in tools:
                        tools.append("go vet")
            
            # golint - 代码风格
            if focus in ["all", "style"]:
                result = self._run_golint(file_path)
                if result.get("issues"):
                    issues.extend(result["issues"])
                    if "golint" not in tools:
                        tools.append("golint")
            
            # staticcheck - 深度分析
            if focus in ["all", "performance"] and review_level == "deep":
                result = self._run_staticcheck(file_path)
                if result.get("issues"):
                    issues.extend(result["issues"])
                    if "staticcheck" not in tools:
                        tools.append("staticcheck")
        
        score = self._calculate_score(issues)
        
        return {
            "tools": tools,
            "issues": issues,
            "score": score,
            "files_checked": len(files),
        }
    
    def _check_go(self) -> bool:
        """检查 Go 是否可用"""
        try:
            result = subprocess.run(
                ["go", "version"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _run_go_vet(self, file_path: str) -> Dict:
        """运行 go vet"""
        try:
            result = subprocess.run(
                ["go", "vet", file_path],
                capture_output=True, text=True, timeout=30
            )
            issues = []
            for line in result.stderr.strip().split("\n"):
                if line:
                    issues.append({
                        "tool": "go vet",
                        "type": "security",
                        "severity": "high",
                        "message": line,
                        "file": file_path,
                    })
            return {"issues": issues}
        except Exception as e:
            return {"issues": [], "error": str(e)}
    
    def _run_golint(self, file_path: str) -> Dict:
        """运行 golint"""
        try:
            result = subprocess.run(
                ["golint", file_path],
                capture_output=True, text=True, timeout=30
            )
            issues = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    issues.append({
                        "tool": "golint",
                        "type": "style",
                        "severity": "medium",
                        "message": line,
                        "file": file_path,
                    })
            return {"issues": issues}
        except Exception as e:
            return {"issues": [], "error": str(e)}
    
    def _run_staticcheck(self, file_path: str) -> Dict:
        """运行 staticcheck"""
        try:
            result = subprocess.run(
                ["staticcheck", file_path],
                capture_output=True, text=True, timeout=60
            )
            issues = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    issues.append({
                        "tool": "staticcheck",
                        "type": "performance",
                        "severity": "medium",
                        "message": line,
                        "file": file_path,
                    })
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