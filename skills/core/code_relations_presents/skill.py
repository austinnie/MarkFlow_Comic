"""
code_relations_presents - 代码关系分析报告生成器

功能：
  - 目录结构可视化
  - 模块依赖分析（内部/外部）
  - 函数调用关系分析
  - 调用链分析
  - 类继承关系分析
  - 核心模块识别（被引用最多）
  - Mermaid 依赖关系图
  - 模块引用矩阵
  - 入口文件识别
  - 代码统计
  - 输出 Markdown 报告
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime
import ast
from collections import defaultdict

logger = logging.getLogger(__name__)


class CodeRelationsPresents:
    """
    代码关系分析报告生成器
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "code_relations_presents"
        self.version = "1.0.0"
        self._setup_logging()
        self._setup_config()
        logger.info("CodeRelationsPresents 初始化完成")

    def _setup_logging(self):
        log_level = self.config.get("log_level", "INFO")
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    def _setup_config(self):
        defaults = {
            "output_dir": "./skills/code_relations_presents/output",
            "exclude_patterns": ["__pycache__", "node_modules", ".git", "*.pyc", ".DS_Store", "venv", "env", ".pytest_cache"],
            "max_depth": 5,
            "include_tests": False,
            "show_private": False,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

        Path(self.config["output_dir"]).mkdir(parents=True, exist_ok=True)

    # ==================== 目录树生成 ====================

    def _should_include(self, path: Path) -> bool:
        """检查是否应该包含该路径"""
        exclude_patterns = self.config.get("exclude_patterns", ["__pycache__", "node_modules", ".git"])

        for pattern in exclude_patterns:
            if pattern.startswith("*."):
                if path.suffix == pattern[1:]:
                    return False
            elif pattern in path.parts:
                return False

        if path.name.startswith(".") and path.name not in [".gitignore", ".env"]:
            return False

        if not self.config.get("include_tests", False):
            if "test" in path.parts or "tests" in path.parts:
                return False

        return True

    def _get_file_description(self, path: Path) -> str:
        """获取文件描述"""
        if path.suffix == ".py":
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                tree = ast.parse(content)
                docstring = ast.get_docstring(tree)
                if docstring:
                    return docstring.split("\n")[0][:30]
            except:
                pass
            return "Python 模块"
        elif path.suffix == ".json":
            return "JSON 配置"
        elif path.suffix == ".md":
            return "Markdown 文档"
        elif path.suffix == ".txt":
            return "文本文件"
        elif path.suffix in [".yaml", ".yml"]:
            return "YAML 配置"
        elif path.suffix in [".js", ".ts"]:
            return "JavaScript/TypeScript"
        elif path.suffix == ".html":
            return "HTML 文件"
        elif path.suffix == ".css":
            return "CSS 文件"
        else:
            return ""

    def _get_tree(self, path: Path, prefix: str = "", depth: int = 0, max_depth: int = None) -> List[str]:
        """生成目录树"""
        if max_depth is None:
            max_depth = self.config.get("max_depth", 5)

        if depth > max_depth:
            return []

        lines = []
        items = sorted([p for p in path.iterdir() if self._should_include(p)])

        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            is_dir = item.is_dir()
            connector = "└── " if is_last else "├── "

            name = item.name
            if is_dir:
                name = f"📁 {name}/"
            else:
                desc = self._get_file_description(item)
                name = f"{name}  # {desc}" if desc else name

            lines.append(f"{prefix}{connector}{name}")

            if is_dir:
                new_prefix = prefix + ("    " if is_last else "│   ")
                lines.extend(self._get_tree(item, new_prefix, depth + 1, max_depth))

        return lines

    # ==================== 模块依赖分析 ====================

    def _get_module_name(self, file_path: Path, root_path: Path) -> str:
        """获取模块名称（相对路径转点号分隔）"""
        rel = file_path.relative_to(root_path)
        parts = list(rel.parts)
        if parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]
        return ".".join(parts)

    def _collect_internal_modules(self, root_path: Path) -> Set[str]:
        """收集所有内部模块名（包括包）"""
        internal = set()
        
        for file_path in root_path.rglob("*.py"):
            if not self._should_include(file_path):
                continue
            
            rel = file_path.relative_to(root_path)
            parts = list(rel.parts)
            
            if parts[-1].endswith(".py"):
                parts[-1] = parts[-1][:-3]
            
            if parts[-1] == "__init__":
                if len(parts) > 1:
                    # 包名：父目录部分
                    internal.add(".".join(parts[:-1]))
                    for i in range(1, len(parts[:-1])):
                        internal.add(".".join(parts[:i]))
            else:
                module_name = ".".join(parts)
                internal.add(module_name)
                for i in range(1, len(parts)):
                    internal.add(".".join(parts[:i]))
        
        return internal
    
    def _analyze_imports(self, root_path: Path) -> Tuple[Dict, Dict]:
        """分析所有 Python 文件的 import 依赖"""
        imports = {}
        ref_count = defaultdict(int)
        internal_modules = self._collect_internal_modules(root_path)

        for file_path in root_path.rglob("*.py"):
            if not self._should_include(file_path):
                continue

            module_name = self._get_module_name(file_path, root_path)
            if module_name == "__init__":
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                tree = ast.parse(content)

                file_imports = {"internal": [], "external": []}

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imp = alias.name
                            self._classify_import(imp, internal_modules, file_imports, ref_count)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imp = node.module
                            self._classify_import(imp, internal_modules, file_imports, ref_count)

                imports[module_name] = file_imports
            except:
                pass

        return imports, dict(ref_count)

    def _classify_import(self, imp: str, internal_modules: Set[str], file_imports: Dict, ref_count: Dict):
        """分类导入为内部或外部"""
        is_internal = False
        
        # 1. 精确匹配
        if imp in internal_modules:
            is_internal = True
        else:
            # 2. 检查是否是内部模块的子模块
            for internal in internal_modules:
                if imp.startswith(internal + "."):
                    is_internal = True
                    break
            
            # 3. 检查相对导入的变体
            if not is_internal:
                for internal in internal_modules:
                    if internal.endswith("." + imp) or internal == imp:
                        is_internal = True
                        break
        
        if is_internal:
            file_imports["internal"].append(imp)
            ref_count[imp] += 1
        else:
            file_imports["external"].append(imp)

    # ==================== 函数调用关系 ====================

    def _analyze_calls(self, root_path: Path) -> Dict:
        """分析函数调用关系"""
        calls = {}

        for file_path in root_path.rglob("*.py"):
            if not self._should_include(file_path):
                continue

            module_name = self._get_module_name(file_path, root_path)
            if module_name == "__init__":
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                tree = ast.parse(content)

                module_calls = {}
                call_references = defaultdict(list)  # 函数 -> 被谁调用

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_name = node.name
                        if func_name.startswith("_") and not self.config.get("show_private", False):
                            continue

                        called_funcs = []
                        for child in ast.walk(node):
                            if isinstance(child, ast.Call):
                                if isinstance(child.func, ast.Name):
                                    called_funcs.append(child.func.id)
                                elif isinstance(child.func, ast.Attribute):
                                    called_funcs.append(child.func.attr)

                        builtins = ["print", "len", "str", "int", "float", "list", "dict", "set", "tuple", "open",
                                    "sum", "max", "min", "sorted", "type", "isinstance", "hasattr", "getattr",
                                    "range", "enumerate", "zip", "map", "filter", "any", "all", "abs", "round"]

                        filtered_calls = [c for c in called_funcs if c not in builtins]
                        if filtered_calls:
                            module_calls[func_name] = filtered_calls[:10]

                if module_calls:
                    calls[module_name] = module_calls
            except:
                pass

        return calls

    # ==================== 调用链分析 ====================

    def _analyze_call_chains(self, calls: Dict, module: str, func: str, depth: int = 3) -> List[str]:
        """分析函数的调用链"""
        if depth <= 0:
            return []

        chain = [f"{module}.{func}"]
        if module in calls and func in calls[module]:
            for called in calls[module][func][:2]:
                # 尝试找到被调用函数所在的模块
                for m, funcs in calls.items():
                    if called in funcs:
                        sub_chain = self._analyze_call_chains(calls, m, called, depth - 1)
                        if sub_chain:
                            chain.extend(sub_chain)
                            break
        return chain

    # ==================== 类继承关系 ====================

    def _analyze_inheritance(self, root_path: Path) -> Dict:
        """分析类继承关系"""
        inheritance = {}

        for file_path in root_path.rglob("*.py"):
            if not self._should_include(file_path):
                continue

            module_name = self._get_module_name(file_path, root_path)
            if module_name == "__init__":
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        bases = []
                        for base in node.bases:
                            if isinstance(base, ast.Name):
                                bases.append(base.id)
                            elif isinstance(base, ast.Attribute):
                                bases.append(base.attr)
                        if bases:
                            key = f"{module_name}.{node.name}"
                            inheritance[key] = bases[:5]
            except:
                pass

        return inheritance

    # ==================== 入口文件识别 ====================

    def _identify_entry_points(self, path: Path) -> List[str]:
        """识别入口文件"""
        entry_points = []

        for file_path in path.rglob("*.py"):
            if not self._should_include(file_path):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if 'if __name__ == "__main__"' in content:
                    entry_points.append(str(file_path.relative_to(path)))
            except:
                pass

        return entry_points

    # ==================== 代码统计 ====================

    def _count_code(self, path: Path) -> Dict:
        """统计代码"""
        stats = {
            "total_files": 0,
            "total_lines": 0,
            "code_lines": 0,
            "comment_lines": 0,
            "blank_lines": 0,
            "python_files": 0,
        }

        for file_path in path.rglob("*"):
            if not self._should_include(file_path):
                continue

            if file_path.is_file():
                stats["total_files"] += 1

                if file_path.suffix == ".py":
                    stats["python_files"] += 1
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                        stats["total_lines"] += len(lines)

                        for line in lines:
                            stripped = line.strip()
                            if not stripped:
                                stats["blank_lines"] += 1
                            elif stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                                stats["comment_lines"] += 1
                            else:
                                stats["code_lines"] += 1
                    except:
                        pass

        return stats

    # ==================== 模块引用矩阵 ====================

    def _build_reference_matrix(self, imports: Dict, max_items: int = 10) -> List[Dict]:
        """构建模块引用矩阵"""
        matrix = []
        # 统计每个模块被引用的次数（内部）
        ref_count = defaultdict(int)
        for module, deps in imports.items():
            for imp in deps.get("internal", []):
                ref_count[imp] += 1

        sorted_refs = sorted(ref_count.items(), key=lambda x: x[1], reverse=True)[:max_items]
        for imp, count in sorted_refs:
            # 找出哪些模块引用了它
            referenced_by = []
            for module, deps in imports.items():
                if imp in deps.get("internal", []):
                    referenced_by.append(module)
            matrix.append({
                "module": imp,
                "ref_count": count,
                "referenced_by": referenced_by[:5]
            })

        return matrix

    # ==================== Mermaid 依赖图 ====================

    def _generate_mermaid_diagram(self, imports: Dict, max_nodes: int = 15) -> str:
        """生成 Mermaid 依赖关系图"""
        lines = ["graph TD"]

        # 收集前 N 个最常被引用的模块
        ref_count = defaultdict(int)
        for module, deps in imports.items():
            for imp in deps.get("internal", []):
                ref_count[imp] += 1

        top_modules = set([m for m, _ in sorted(ref_count.items(), key=lambda x: x[1], reverse=True)[:max_nodes]])
        # 添加这些模块的引用方
        for module, deps in imports.items():
            if module in top_modules or any(dep in top_modules for dep in deps.get("internal", [])):
                top_modules.add(module)

        # 生成节点
        for module in top_modules:
            safe_module = module.replace(".", "_").replace("-", "_")
            lines.append(f"    {safe_module}[\"{module}\"]")

        # 生成边
        for module, deps in imports.items():
            if module in top_modules:
                for imp in deps.get("internal", []):
                    if imp in top_modules and imp != module:
                        safe_module = module.replace(".", "_").replace("-", "_")
                        safe_imp = imp.replace(".", "_").replace("-", "_")
                        lines.append(f"    {safe_module} --> {safe_imp}")

        return "\n".join(lines)

    # ==================== 生成报告 ====================

    def generate_report(self, code_path: str) -> Dict:
        """生成代码分析报告"""
        path = Path(code_path)

        if not path.exists():
            return {"error": f"路径不存在: {code_path}"}

        # 分析
        imports, ref_count = self._analyze_imports(path)
        calls = self._analyze_calls(path)
        inheritance = self._analyze_inheritance(path)

        report = {
            "path": str(path.absolute()),
            "name": path.name,
            "tree": self._get_tree(path),
            "imports": imports,
            "ref_count": ref_count,
            "calls": calls,
            "inheritance": inheritance,
            "entry_points": self._identify_entry_points(path),
            "statistics": self._count_code(path),
            "ref_matrix": self._build_reference_matrix(imports),
            "mermaid": self._generate_mermaid_diagram(imports),
            "generated_at": datetime.now().isoformat(),
        }

        return report

    def save_report(self, report: Dict, output_format: str = "md") -> str:
        """保存报告"""
        output_dir = Path(self.config["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = re.sub(r'[<>:"/\\|?*]', '', report.get("name", "project"))

        if output_format == "json":
            file_path = output_dir / f"{safe_name}_{timestamp}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            return str(file_path)

        # Markdown 格式
        file_path = output_dir / f"{safe_name}_{timestamp}.md"
        lines = []

        lines.append(f"# 代码分析报告: {report.get('name', '')}")
        lines.append("")
        lines.append(f"> 生成时间: {report.get('generated_at', '')}")
        lines.append("")

        # 1. 目录结构
        lines.append("## 目录结构")
        lines.append("")
        lines.append("```text")
        lines.extend(report.get("tree", []))
        lines.append("```")
        lines.append("")

        # 2. 入口文件
        entry_points = report.get("entry_points", [])
        if entry_points:
            lines.append("## 入口文件")
            lines.append("")
            for ep in entry_points:
                lines.append(f"- 🚀 `{ep}`")
            lines.append("")

        # 3. 核心模块
        ref_count = report.get("ref_count", {})
        if ref_count:
            sorted_refs = sorted(ref_count.items(), key=lambda x: x[1], reverse=True)[:10]
            lines.append("## 核心模块（被引用最多）")
            lines.append("")
            lines.append("| 排名 | 模块 | 被引用次数 |")
            lines.append("|------|------|------------|")
            for i, (mod, count) in enumerate(sorted_refs, 1):
                lines.append(f"| {i} | `{mod}` | {count} |")
            lines.append("")

        # 4. 模块引用矩阵
        ref_matrix = report.get("ref_matrix", [])
        if ref_matrix:
            lines.append("## 模块引用矩阵")
            lines.append("")
            lines.append("| 模块 | 被引用次数 | 被以下模块引用 |")
            lines.append("|------|------------|----------------|")
            for item in ref_matrix[:10]:
                refs = ", ".join([f"`{r}`" for r in item["referenced_by"]])
                if len(item["referenced_by"]) > 3:
                    refs += f" ... 等 {len(item['referenced_by'])} 个"
                lines.append(f"| `{item['module']}` | {item['ref_count']} | {refs} |")
            lines.append("")

        # 5. 依赖关系图（Mermaid）
        mermaid = report.get("mermaid", "")
        if mermaid:
            lines.append("## 依赖关系图（Mermaid）")
            lines.append("")
            lines.append("```mermaid")
            lines.append(mermaid)
            lines.append("```")
            lines.append("")

        # 6. 代码统计
        stats = report.get("statistics", {})
        lines.append("## 代码统计")
        lines.append("")
        lines.append("| 指标 | 数量 |")
        lines.append("|------|------|")
        lines.append(f"| 总文件数 | {stats.get('total_files', 0)} |")
        lines.append(f"| Python 文件 | {stats.get('python_files', 0)} |")
        lines.append(f"| 总行数 | {stats.get('total_lines', 0)} |")
        lines.append(f"| 代码行数 | {stats.get('code_lines', 0)} |")
        lines.append(f"| 注释行数 | {stats.get('comment_lines', 0)} |")
        lines.append(f"| 空白行数 | {stats.get('blank_lines', 0)} |")
        lines.append("")
        lines.append(f"**注释率**: {stats.get('comment_lines', 0) / max(stats.get('total_lines', 1), 1) * 100:.1f}%")
        lines.append("")

        # 7. 模块依赖关系
        imports = report.get("imports", {})
        if imports:
            lines.append("## 模块依赖关系")
            lines.append("")

            for module, deps in sorted(imports.items())[:15]:
                internal_deps = deps.get("internal", [])
                external_deps = deps.get("external", [])

                if internal_deps or external_deps:
                    lines.append(f"### `{module}`")
                    lines.append("")

                    if internal_deps:
                        lines.append("**内部依赖**:")
                        for dep in internal_deps[:5]:
                            lines.append(f"  - `{dep}`")
                        if len(internal_deps) > 5:
                            lines.append(f"  - ... 还有 {len(internal_deps) - 5} 个")
                        lines.append("")

                    if external_deps:
                        lines.append("**外部依赖**:")
                        for dep in external_deps[:5]:
                            lines.append(f"  - `{dep}`")
                        if len(external_deps) > 5:
                            lines.append(f"  - ... 还有 {len(external_deps) - 5} 个")
                        lines.append("")

        # 8. 函数调用关系
        calls = report.get("calls", {})
        if calls:
            lines.append("## 函数调用关系")
            lines.append("")

            for module, funcs in sorted(calls.items())[:10]:
                lines.append(f"### `{module}`")
                lines.append("")
                lines.append("| 函数 | 调用的函数 |")
                lines.append("|------|------------|")
                for func, called in list(funcs.items())[:5]:
                    lines.append(f"| `{func}` | {', '.join([f'`{c}`' for c in called[:5]])} |")
                if len(funcs) > 5:
                    lines.append(f"| ... | 还有 {len(funcs) - 5} 个函数 |")
                lines.append("")

        # 9. 类继承关系
        inheritance = report.get("inheritance", {})
        if inheritance:
            lines.append("## 类继承关系")
            lines.append("")
            for cls, bases in list(inheritance.items())[:10]:
                lines.append(f"- `{cls}` → 继承自: {', '.join([f'`{b}`' for b in bases])}")
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append(f"*报告由 CodeRelationsPresents 生成于 {report.get('generated_at', '')}*")

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        return str(file_path)

    # ==================== 执行入口 ====================

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行代码分析"""
        logger.info(f"执行技能: {self.name} (v{self.version})")

        try:
            code_path = kwargs.get("code_path", "")
            if not code_path:
                return {"status": "error", "error": "请提供 code_path 参数"}

            output_format = kwargs.get("output_format", "md")

            report = self.generate_report(code_path)
            if "error" in report:
                return {"status": "error", "error": report["error"]}

            saved_path = self.save_report(report, output_format)

            return {
                "status": "success",
                "result": {
                    "report_path": saved_path,
                    "name": report.get("name", ""),
                    "total_files": report.get("statistics", {}).get("total_files", 0),
                    "entry_points": report.get("entry_points", []),
                    "core_modules": sorted(report.get("ref_count", {}).items(), key=lambda x: x[1], reverse=True)[:5],
                    "generated_at": report.get("generated_at", ""),
                },
                "metadata": {
                    "skill": self.name,
                    "version": self.version,
                }
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "skill": self.name,
            }

    def __repr__(self):
        return f"<CodeRelationsPresents(name={self.name}, version={self.version})>"