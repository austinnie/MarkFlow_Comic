"""
Android 代码检查器
使用: android-lint, ktlint
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from .base import BaseChecker


class AndroidChecker(BaseChecker):
    """Android 代码检查器"""
    
    def check(self, files: List[str], focus: str, review_level: str, max_files: int) -> Dict[str, Any]:
        issues = []
        tools = []
        
        files = self._limit_files(files, max_files)
        
        # 检查 Android 环境
        has_android = self._check_android()
        
        for file_path in files:
            # Android Lint - 综合检查
            if has_android:
                result = self._run_android_lint(file_path)
                if result.get("issues"):
                    issues.extend(result["issues"])
                    if "android-lint" not in tools:
                        tools.append("android-lint")
            
            # KtLint - Kotlin 代码风格
            if file_path.endswith(".kt"):
                result = self._run_ktlint(file_path)
                if result.get("issues"):
                    issues.extend(result["issues"])
                    if "ktlint" not in tools:
                        tools.append("ktlint")
        
        score = self._calculate_score(issues)
        
        return {
            "tools": tools,
            "issues": issues,
            "score": score,
            "files_checked": len(files),
        }
    
    def _check_android(self) -> bool:
        """检查 Android SDK 是否可用"""
        android_home = Path(os.environ.get("ANDROID_HOME", ""))
        if android_home.exists():
            lint_path = android_home / "tools" / "bin" / "lint"
            if lint_path.exists():
                return True
            lint_path = android_home / "cmdline-tools" / "latest" / "bin" / "lint"
            if lint_path.exists():
                return True
        return False
    
    def _run_android_lint(self, file_path: str) -> Dict:
        """运行 Android Lint"""
        try:
            # 查找项目根目录
            file_path_obj = Path(file_path)
            project_dir = file_path_obj.parent
            
            # 查找 AndroidManifest.xml 或 build.gradle
            while project_dir.parent != project_dir:
                if (project_dir / "AndroidManifest.xml").exists() or (project_dir / "build.gradle").exists():
                    break
                project_dir = project_dir.parent
            
            android_home = Path(os.environ.get("ANDROID_HOME", ""))
            if android_home:
                lint_cmd = android_home / "tools" / "bin" / "lint"
                if not lint_cmd.exists():
                    lint_cmd = android_home / "cmdline-tools" / "latest" / "bin" / "lint"
            
            if not lint_cmd.exists():
                return {"issues": [], "error": "Android lint not found"}
            
            result = subprocess.run(
                [str(lint_cmd), "--html", "lint_report.html", str(project_dir)],
                capture_output=True, text=True, timeout=120
            )
            
            issues = []
            # 解析 HTML 报告（简化处理）
            if Path("lint_report.html").exists():
                import re
                with open("lint_report.html", 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 提取问题
                pattern = r'<td>([^<]+)</td>.*?<td>([^<]+)</td>.*?<td>([^<]+)</td>'
                matches = re.findall(pattern, content, re.DOTALL)
                for match in matches:
                    issues.append({
                        "tool": "android-lint",
                        "type": match[0].strip(),
                        "severity": "high" if "Error" in match[1] else "medium",
                        "message": match[2].strip()[:200],
                        "file": file_path,
                    })
                
                Path("lint_report.html").unlink()
            
            return {"issues": issues}
        except Exception as e:
            return {"issues": [], "error": str(e)}
    
    def _run_ktlint(self, file_path: str) -> Dict:
        """运行 ktlint"""
        try:
            result = subprocess.run(
                ["ktlint", file_path],
                capture_output=True, text=True, timeout=30
            )
            issues = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split(":")
                    if len(parts) >= 3:
                        try:
                            issues.append({
                                "tool": "ktlint",
                                "type": "style",
                                "severity": "medium",
                                "message": parts[-1].strip(),
                                "line": int(parts[1]),
                                "file": file_path,
                            })
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