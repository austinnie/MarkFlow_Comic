"""
code_reviewer - 多语言代码审查助手

支持语言:
  - Python (pylint, flake8, bandit, radon)
  - JavaScript/TypeScript (eslint)
  - Java (checkstyle, spotbugs)
  - C/C++ (cppcheck, clang-tidy)
  - Go (golint, staticcheck)
  - Rust (clippy)
  - Android (android lint)
"""

import os
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class CodeReviewer:
    """
    多语言代码审查助手
    """
    
    # 支持的语言列表
    SUPPORTED_LANGUAGES = {
        "python": {
            "extensions": [".py"],
            "tools": ["pylint", "flake8", "bandit", "radon"],
            "checker": "PythonChecker"
        },
        "javascript": {
            "extensions": [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"],
            "tools": ["eslint"],
            "checker": "JavaScriptChecker"
        },
        "typescript": {
            "extensions": [".ts", ".tsx"],
            "tools": ["eslint", "tsc"],
            "checker": "JavaScriptChecker"
        },
        "java": {
            "extensions": [".java"],
            "tools": ["checkstyle", "spotbugs"],
            "checker": "JavaChecker"
        },
        "c": {
            "extensions": [".c", ".h"],
            "tools": ["cppcheck", "clang-tidy"],
            "checker": "CppChecker"
        },
        "cpp": {
            "extensions": [".cpp", ".cc", ".cxx", ".h", ".hpp"],
            "tools": ["cppcheck", "clang-tidy"],
            "checker": "CppChecker"
        },
        "go": {
            "extensions": [".go"],
            "tools": ["golint", "staticcheck", "go vet"],
            "checker": "GoChecker"
        },
        "rust": {
            "extensions": [".rs"],
            "tools": ["clippy"],
            "checker": "RustChecker"
        },
        "android": {
            "extensions": [".java", ".kt", ".xml"],
            "tools": ["android-lint", "ktlint"],
            "checker": "AndroidChecker"
        }
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "code_reviewer"
        self.version = "1.0.0"
        self._setup_logging()
        self._setup_config()
        self._load_checkers()
        logger.info(f"多语言代码审查助手 初始化完成，支持 {len(self._checkers)} 种语言")
    
    def _setup_logging(self):
        log_level = self.config.get("log_level", "INFO")
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    def _setup_config(self):
        defaults = {
            "output_dir": "./skills/code_reviewer/output",
            "auto_detect": True,
            "max_files": 20,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def _load_checkers(self):
        """加载各语言检查器"""
        self._checkers = {}
        try:
            from .checkers.python_checker import PythonChecker
            self._checkers["python"] = PythonChecker
        except ImportError:
            pass
        
        try:
            from .checkers.javascript_checker import JavaScriptChecker
            self._checkers["javascript"] = JavaScriptChecker
            self._checkers["typescript"] = JavaScriptChecker
        except ImportError:
            pass
        
        try:
            from .checkers.java_checker import JavaChecker
            self._checkers["java"] = JavaChecker
        except ImportError:
            pass
        
        try:
            from .checkers.cpp_checker import CppChecker
            self._checkers["c"] = CppChecker
            self._checkers["cpp"] = CppChecker
        except ImportError:
            pass
        
        try:
            from .checkers.go_checker import GoChecker
            self._checkers["go"] = GoChecker
        except ImportError:
            pass
        
        try:
            from .checkers.rust_checker import RustChecker
            self._checkers["rust"] = RustChecker
        except ImportError:
            pass
        
        try:
            from .checkers.android_checker import AndroidChecker
            self._checkers["android"] = AndroidChecker
        except ImportError:
            pass
    
    def _detect_language(self, file_path: str) -> Optional[str]:
        """根据文件扩展名自动检测语言"""
        ext = Path(file_path).suffix.lower()
        for lang, info in self.SUPPORTED_LANGUAGES.items():
            if ext in info["extensions"]:
                return lang
        return None
    
    def _get_files(self, code_path: str, language: str = None) -> Dict[str, List[str]]:
        """获取所有文件，按语言分组"""
        path = Path(code_path)
        files_by_lang = {}
        
        if path.is_file():
            lang = language or self._detect_language(str(path))
            if lang:
                files_by_lang[lang] = [str(path)]
            return files_by_lang
        
        # 遍历目录
        for lang, info in self.SUPPORTED_LANGUAGES.items():
            if language and lang != language:
                continue
            files = []
            for ext in info["extensions"]:
                files.extend([str(f) for f in path.rglob(f"*{ext}")])
            if files:
                files_by_lang[lang] = files
        
        return files_by_lang
    
    def _calculate_quality_score(self, issues: List[Dict]) -> int:
        """计算质量评分 (0-100)"""
        if not issues:
            return 100
        
        # 按严重程度扣分
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
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行代码审查"""
        start_time = time.time()
        logger.info(f"执行技能: {self.name} (v{self.version})")

        # 检测工具
        from .checkers.tools import check_all_tools, get_missing_tools
        all_tools = check_all_tools()
        missing = get_missing_tools()
        
        if missing:
            logger.warning("以下工具未安装，部分功能将不可用:")
            for lang, tools in missing.items():
                logger.warning(f"  {lang}: {', '.join(tools)}")
            
        try:
            code_path = kwargs.get("code_path")
            language = kwargs.get("language", "")
            review_level = kwargs.get("review_level", "basic")
            focus = kwargs.get("focus", "all")
            auto_detect = kwargs.get("auto_detect", self.config.get("auto_detect", True))
            
            if not code_path:
                return {
                    "status": "error",
                    "error": "code_path 是必填参数",
                    "skill": self.name,
                    "timestamp": datetime.now().isoformat()
                }
            
            path = Path(code_path)
            if not path.exists():
                return {
                    "status": "error",
                    "error": f"路径不存在: {code_path}",
                    "skill": self.name,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 获取文件
            files_by_lang = self._get_files(code_path, language if language else None)
            if not files_by_lang:
                return {
                    "status": "error",
                    "error": f"未找到支持的文件: {code_path}",
                    "supported": list(self.SUPPORTED_LANGUAGES.keys()),
                    "skill": self.name,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 统计
            total_files = sum(len(f) for f in files_by_lang.values())
            logger.info(f"找到 {total_files} 个文件，{len(files_by_lang)} 种语言")
            
            # 限制文件数
            max_files = self.config.get("max_files", 20)
            if total_files > max_files and review_level == "basic":
                logger.info(f"文件数 {total_files} 超过限制 {max_files}，仅审查前 {max_files} 个")
            
            all_results = []
            all_issues = []
            
            # 逐语言审查
            for lang, files in files_by_lang.items():
                logger.info(f"审查 {lang.upper()} 代码 ({len(files)} 个文件)")
                
                checker_class = self._checkers.get(lang)
                if not checker_class:
                    logger.warning(f"未找到 {lang} 的检查器")
                    continue
                
                try:
                    checker = checker_class(self.config)
                    result = checker.check(files, focus, review_level, max_files)
                    
                    if result.get("issues"):
                        for issue in result["issues"]:
                            issue["language"] = lang
                        all_issues.extend(result["issues"])
                    
                    all_results.append({
                        "language": lang,
                        "files": len(files),
                        "issues_count": len(result.get("issues", [])),
                        "tools": result.get("tools", []),
                        "score": result.get("score", 100),
                    })
                    
                except Exception as e:
                    logger.error(f"{lang} 审查失败: {e}")
                    all_results.append({
                        "language": lang,
                        "error": str(e),
                    })
            
            # 计算总体评分
            overall_score = self._calculate_quality_score(all_issues) if all_issues else 100
            
            # 生成报告
            result_data = {
                "status": "success",
                "message": "代码审查完成",
                "total_files": total_files,
                "languages": list(files_by_lang.keys()),
                "overall_score": overall_score,
                "issues_count": len(all_issues),
                "results_by_language": all_results,
                "issues": all_issues[:50],
                "review_level": review_level,
                "focus": focus,
                "code_path": code_path,
            }
            
            # 保存报告
            output_dir = Path(self.config.get("output_dir", "./skills/code_reviewer/output"))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            report_file = output_dir / f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"审查完成，评分: {overall_score}")
            logger.info(f"报告保存: {report_file}")
            
            return {
                "status": "success",
                "result": result_data,
                "metadata": {
                    "skill": self.name,
                    "version": self.version,
                    "executed_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "skill": self.name,
                "timestamp": datetime.now().isoformat()
            }
    
    def __repr__(self):
        return f"<CodeReviewer(name={self.name}, version={self.version})>"