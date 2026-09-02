"""
Java 代码检查器
使用: checkstyle, spotbugs
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from .base import BaseChecker


class JavaChecker(BaseChecker):
    """Java 代码检查器"""
    
    def check(self, files: List[str], focus: str, review_level: str, max_files: int) -> Dict[str, Any]:
        issues = []
        tools = []
        
        files = self._limit_files(files, max_files)
        
        # 检查是否有 checkstyle
        has_checkstyle = self._check_checkstyle()
        
        # 检查是否有 spotbugs
        has_spotbugs = self._check_spotbugs()
        
        for file_path in files:
            # Checkstyle - 代码风格和规范
            if focus in ["all", "style"] and has_checkstyle:
                result = self._run_checkstyle(file_path)
                if result.get("issues"):
                    issues.extend(result["issues"])
                    if "checkstyle" not in tools:
                        tools.append("checkstyle")
            
            # SpotBugs - 安全漏洞和潜在错误
            if focus in ["all", "security"] and has_spotbugs:
                result = self._run_spotbugs(file_path)
                if result.get("issues"):
                    issues.extend(result["issues"])
                    if "spotbugs" not in tools:
                        tools.append("spotbugs")
        
        score = self._calculate_score(issues)
        
        return {
            "tools": tools,
            "issues": issues,
            "score": score,
            "files_checked": len(files),
        }
    
    def _check_checkstyle(self) -> bool:
        """检查 checkstyle 是否可用"""
        try:
            # 检查是否存在 checkstyle jar
            import glob
            jars = glob.glob("**/checkstyle-*.jar", recursive=True)
            if jars:
                return True
            # 尝试命令行调用
            result = subprocess.run(
                ["java", "-cp", "checkstyle.jar", "com.puppycrawl.tools.checkstyle.Main", "--version"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _check_spotbugs(self) -> bool:
        """检查 spotbugs 是否可用"""
        try:
            import glob
            jars = glob.glob("**/spotbugs-*.jar", recursive=True)
            if jars:
                return True
            result = subprocess.run(
                ["spotbugs", "-version"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _run_checkstyle(self, file_path: str) -> Dict:
        """运行 checkstyle 检查"""
        try:
            # 使用命令行调用 checkstyle
            # 假设 checkstyle jar 在 lib 目录下
            import glob
            jar_files = glob.glob("lib/checkstyle-*.jar") + glob.glob("checkstyle-*.jar")
            
            if not jar_files:
                return {"issues": [], "error": "checkstyle jar not found"}
            
            checkstyle_jar = jar_files[0]
            
            result = subprocess.run(
                [
                    "java", "-jar", checkstyle_jar,
                    "-f", "json",
                    "-c", "/sun_checks.xml",
                    file_path
                ],
                capture_output=True, text=True, timeout=60
            )
            
            issues = []
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    for item in data.get("files", []):
                        for error in item.get("errors", []):
                            issues.append({
                                "tool": "checkstyle",
                                "type": "style",
                                "severity": "medium",
                                "message": error.get("message", ""),
                                "line": error.get("line", 0),
                                "file": file_path,
                            })
                except json.JSONDecodeError:
                    # 尝试解析非 JSON 输出
                    for line in result.stdout.strip().split("\n"):
                        if "[WARN]" in line or "[ERROR]" in line:
                            issues.append({
                                "tool": "checkstyle",
                                "type": "style",
                                "severity": "high" if "[ERROR]" in line else "medium",
                                "message": line,
                                "file": file_path,
                            })
            return {"issues": issues}
        except Exception as e:
            return {"issues": [], "error": str(e)}
    
    def _run_spotbugs(self, file_path: str) -> Dict:
        """运行 spotbugs 检查"""
        try:
            # 编译 class 文件（简化处理）
            # 实际使用中需要先编译 Java 文件
            class_dir = Path("target/classes")
            class_dir.mkdir(parents=True, exist_ok=True)
            
            # 编译 Java 文件
            compile_result = subprocess.run(
                ["javac", "-d", str(class_dir), file_path],
                capture_output=True, text=True, timeout=30
            )
            
            if compile_result.returncode != 0:
                return {"issues": [], "error": "Compilation failed"}
            
            # 使用 spotbugs 检查
            import glob
            jar_files = glob.glob("lib/spotbugs-*.jar") + glob.glob("spotbugs-*.jar")
            
            if not jar_files:
                return {"issues": [], "error": "spotbugs jar not found"}
            
            spotbugs_jar = jar_files[0]
            
            result = subprocess.run(
                [
                    "java", "-jar", spotbugs_jar,
                    "-textui",
                    "-xml:withMessages",
                    "-output", "spotbugs_result.xml",
                    str(class_dir)
                ],
                capture_output=True, text=True, timeout=60
            )
            
            issues = []
            # 解析 XML 输出
            if Path("spotbugs_result.xml").exists():
                import xml.etree.ElementTree as ET
                try:
                    tree = ET.parse("spotbugs_result.xml")
                    root = tree.getroot()
                    for bug in root.findall(".//BugInstance"):
                        severity = bug.get("priority", "2")
                        severity_map = {"1": "critical", "2": "high", "3": "medium"}
                        issues.append({
                            "tool": "spotbugs",
                            "type": "security",
                            "severity": severity_map.get(severity, "medium"),
                            "message": bug.get("message", ""),
                            "file": file_path,
                        })
                    Path("spotbugs_result.xml").unlink()
                except:
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