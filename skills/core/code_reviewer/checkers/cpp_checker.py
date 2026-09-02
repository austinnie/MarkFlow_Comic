"""
C/C++ 代码检查器
使用: cppcheck, clang-tidy
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from .base import BaseChecker


class CppChecker(BaseChecker):
    """C/C++ 代码检查器"""
    
    def check(self, files: List[str], focus: str, review_level: str, max_files: int) -> Dict[str, Any]:
        issues = []
        tools = []
        
        files = self._limit_files(files, max_files)
        
        # 检查是否有 cppcheck
        has_cppcheck = self._check_cppcheck()
        
        # 检查是否有 clang-tidy
        has_clang_tidy = self._check_clang_tidy()
        
        for file_path in files:
            # Cppcheck - 通用检查
            if has_cppcheck:
                result = self._run_cppcheck(file_path, focus)
                if result.get("issues"):
                    issues.extend(result["issues"])
                    if "cppcheck" not in tools:
                        tools.append("cppcheck")
            
            # Clang-tidy - 深度检查
            if focus in ["all", "security", "performance"] and has_clang_tidy:
                result = self._run_clang_tidy(file_path)
                if result.get("issues"):
                    issues.extend(result["issues"])
                    if "clang-tidy" not in tools:
                        tools.append("clang-tidy")
        
        score = self._calculate_score(issues)
        
        return {
            "tools": tools,
            "issues": issues,
            "score": score,
            "files_checked": len(files),
        }
    
    def _check_cppcheck(self) -> bool:
        """检查 cppcheck 是否可用"""
        try:
            result = subprocess.run(
                ["cppcheck", "--version"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _check_clang_tidy(self) -> bool:
        """检查 clang-tidy 是否可用"""
        try:
            result = subprocess.run(
                ["clang-tidy", "--version"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _run_cppcheck(self, file_path: str, focus: str) -> Dict:
        """运行 cppcheck 检查"""
        try:
            # 构建命令
            cmd = ["cppcheck", "--enable=all", "--xml", "--xml-version=2"]
            
            if focus == "security":
                cmd.append("--enable=security")
            elif focus == "performance":
                cmd.append("--enable=performance")
            elif focus == "style":
                cmd.append("--enable=style")
            # else: all
            
            cmd.append(file_path)
            
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=60
            )
            
            issues = []
            # 解析 XML 输出
            if "<?xml" in result.stdout:
                import xml.etree.ElementTree as ET
                try:
                    root = ET.fromstring(result.stdout)
                    for error in root.findall(".//error"):
                        severity = error.get("severity", "style")
                        severity_map = {
                            "error": "critical",
                            "warning": "high",
                            "style": "medium",
                            "performance": "medium",
                            "portability": "low"
                        }
                        issues.append({
                            "tool": "cppcheck",
                            "type": error.get("id", "general"),
                            "severity": severity_map.get(severity, "medium"),
                            "message": error.get("msg", ""),
                            "line": int(error.get("line", 0)),
                            "file": file_path,
                        })
                except:
                    pass
            else:
                # 解析非 XML 输出
                for line in result.stdout.strip().split("\n"):
                    if "error:" in line or "warning:" in line or "style:" in line:
                        issues.append({
                            "tool": "cppcheck",
                            "type": "general",
                            "severity": "high" if "error:" in line else "medium",
                            "message": line,
                            "file": file_path,
                        })
            
            return {"issues": issues}
        except Exception as e:
            return {"issues": [], "error": str(e)}
    
    def _run_clang_tidy(self, file_path: str) -> Dict:
        """运行 clang-tidy 检查"""
        try:
            # 需要编译数据库 compile_commands.json
            # 简化处理：使用默认配置
            cmd = ["clang-tidy", file_path, "--", "-std=c++17"]
            
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=120
            )
            
            issues = []
            for line in result.stdout.strip().split("\n"):
                if "warning:" in line or "error:" in line:
                    # 解析格式: file:line:col: severity: message
                    parts = line.split(":")
                    if len(parts) >= 4:
                        try:
                            line_num = int(parts[1])
                            severity = "high" if "error" in parts[3].lower() else "medium"
                            issues.append({
                                "tool": "clang-tidy",
                                "type": "general",
                                "severity": severity,
                                "message": ":".join(parts[3:]),
                                "line": line_num,
                                "file": file_path,
                            })
                        except:
                            issues.append({
                                "tool": "clang-tidy",
                                "type": "general",
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