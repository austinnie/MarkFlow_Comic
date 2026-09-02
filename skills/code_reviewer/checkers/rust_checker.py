"""
Rust 代码检查器
使用: clippy
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from .base import BaseChecker


class RustChecker(BaseChecker):
    """Rust 代码检查器"""
    
    def check(self, files: List[str], focus: str, review_level: str, max_files: int) -> Dict[str, Any]:
        issues = []
        tools = []
        
        files = self._limit_files(files, max_files)
        
        # 检查 Rust 环境
        has_cargo = self._check_cargo()
        
        if not has_cargo:
            return {
                "tools": [],
                "issues": [],
                "score": 0,
                "error": "Cargo not installed",
                "files_checked": 0,
            }
        
        # 对每个文件运行 clippy
        for file_path in files:
            # clippy - 全面检查
            result = self._run_clippy(file_path)
            if result.get("issues"):
                issues.extend(result["issues"])
                if "clippy" not in tools:
                    tools.append("clippy")
        
        score = self._calculate_score(issues)
        
        return {
            "tools": tools,
            "issues": issues,
            "score": score,
            "files_checked": len(files),
        }
    
    def _check_cargo(self) -> bool:
        """检查 Cargo 是否可用"""
        try:
            result = subprocess.run(
                ["cargo", "--version"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _run_clippy(self, file_path: str) -> Dict:
        """运行 clippy"""
        try:
            # 在文件所在目录运行 cargo clippy
            file_path_obj = Path(file_path)
            project_dir = file_path_obj.parent
            
            # 查找 Cargo.toml
            cargo_file = project_dir / "Cargo.toml"
            if not cargo_file.exists():
                return {"issues": [], "error": "Cargo.toml not found"}
            
            result = subprocess.run(
                ["cargo", "clippy", "--message-format=json"],
                cwd=str(project_dir),
                capture_output=True, text=True, timeout=120
            )
            
            issues = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get("reason") == "compiler-message":
                        message = data.get("message", {})
                        if message:
                            issues.append({
                                "tool": "clippy",
                                "type": message.get("code", {}).get("code", "clippy"),
                                "severity": "high" if message.get("level") == "error" else "medium",
                                "message": message.get("message", ""),
                                "line": message.get("spans", [{}])[0].get("line_start", 0),
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
            if severity == "critical":
                score -= 5
            elif severity == "high":
                score -= 3
            elif severity == "medium":
                score -= 1.5
            else:
                score -= 0.5
        return max(0, min(100, int(score)))