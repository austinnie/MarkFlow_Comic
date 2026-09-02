"""
md_converter - 智能Markdown转换器

设计原则:
  1. 通用规则函数: 处理标准Markdown语法
  2. 专门修复函数: 处理特定格式的顽固问题
  3. 管道式处理: 按顺序应用所有函数
"""

import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class MarkdownFixer:
    """
    Markdown修复器 - 管道式处理
    """
    
    def __init__(self):
        # 处理管道: 按顺序执行所有修复函数
        self.pipeline: List[Callable[[str], str]] = [
            self.fix_code_block_lang,      # 修复代码块语言标记
            self.fix_headers,              # 修复标题
            self.fix_bash_code_blocks,     # 专门修复bash代码块
            self.fix_lists,                # 修复列表
            self.fix_tables,               # 修复表格
            self.fix_quotes,               # 修复引用
            self.fix_hr_lines,             # 修复分隔线
            self.fix_emphasis,             # 修复强调
            self.fix_links,                # 修复链接
            self.fix_empty_lines,          # 修复空行
        ]
    
    def process(self, content: str) -> str:
        """按管道顺序处理内容"""
        for fix_func in self.pipeline:
            content = fix_func(content)
        return content
    
    # ============================================================
    # 通用规则函数
    # ============================================================
    
    def fix_code_block_lang(self, content: str) -> str:
        """修复代码块语言标记: 确保 ``` 后有正确的语言标识"""
        valid_langs = ['bash', 'text', 'python', 'json', 'yaml', 'xml', 'html', 
                       'css', 'javascript', 'js', 'sql', 'go', 'rust', 'cpp', 'c', 'java',
                       'ruby', 'php', 'swift', 'kotlin', 'typescript', 'ts', 'shell',
                       'powershell', 'diff', 'dockerfile', 'makefile', 'markdown']
        
        lines = content.split('\n')
        result = []
        in_block = False
        
        for line in lines:
            stripped = line.strip()
            # 检测代码块开始
            code_start = re.match(r'^(`{3,})(\w*)$', stripped)
            if code_start and not in_block:
                lang = code_start.group(2) or 'text'
                if lang and lang not in valid_langs:
                    lang = 'text'
                result.append(f'```{lang}')
                in_block = True
                continue
            
            # 检测代码块结束
            if stripped == '```' and in_block:
                result.append('```')
                in_block = False
                continue
            
            result.append(line)
        
        # 如果代码块未闭合，补全
        if in_block:
            result.append('```')
        
        return '\n'.join(result)
    
    def fix_headers(self, content: str) -> str:
        """修复标题: 检测并修正标题层级"""
        lines = content.split('\n')
        result = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # 已经是标准标题 (#开头)
            if re.match(r'^#{1,6}\s+', stripped):
                result.append(line)
                i += 1
                continue
            
            # 下划线标题 (=== 或 ---)
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if re.match(r'^=+$', next_line):
                    result.append(f"# {stripped}")
                    i += 2
                    continue
                if re.match(r'^-+$', next_line):
                    result.append(f"## {stripped}")
                    i += 2
                    continue
            
            # 中文数字标题 (一、 或 1.)
            num_match = re.match(r'^[一二三四五六七八九十]+[、.．]\s*(.+)$', stripped)
            if num_match:
                result.append(f"## {num_match.group(1).strip()}")
                i += 1
                continue
            
            num_match2 = re.match(r'^(\d+)[、.．]\s*(.+)$', stripped)
            if num_match2:
                result.append(f"### {num_match2.group(2).strip()}")
                i += 1
                continue
            
            # 常见标题关键词 (短文本、无标点)
            if len(stripped) < 30 and not re.search(r'[，。！？、：；,.!?:;]', stripped):
                # 但不是列表
                if not re.match(r'^[-*+]\s+', stripped) and not re.match(r'^\d+\.', stripped):
                    # 检查是否是 "xxx：" 格式
                    if re.match(r'^.+[：:]\s*$', stripped):
                        result.append(f"## {stripped}")
                        i += 1
                        continue
            
            result.append(line)
            i += 1
        
        return '\n'.join(result)
    
    def fix_lists(self, content: str) -> str:
        """修复列表: 统一列表格式"""
        lines = content.split('\n')
        result = []
        in_list = False
        
        for line in lines:
            stripped = line.strip()
            
            # 任务列表 □ ✓
            if re.match(r'^□\s+(.+)$', stripped):
                content_text = re.sub(r'^□\s+', '', stripped)
                result.append(f"- [ ] {content_text}")
                in_list = True
                continue
            
            if re.match(r'^✓\s+(.+)$', stripped):
                content_text = re.sub(r'^✓\s+', '', stripped)
                result.append(f"- [x] {content_text}")
                in_list = True
                continue
            
            # 数字列表 1. 或 1) 或 1、
            num_match = re.match(r'^(\d+)[.．、\)]\s+(.+)$', stripped)
            if num_match:
                content_text = num_match.group(2).strip()
                # 检查是否已经是标准列表
                if not stripped.startswith('1. '):
                    result.append(f"1. {content_text}")
                else:
                    result.append(line)
                in_list = True
                continue
            
            # 符号列表 - * + 
            symbol_match = re.match(r'^([-*+])\s+(.+)$', stripped)
            if symbol_match:
                content_text = symbol_match.group(2).strip()
                if not stripped.startswith('- '):
                    result.append(f"- {content_text}")
                else:
                    result.append(line)
                in_list = True
                continue
            
            # 检测缩进子列表 (以2个以上空格开头)
            indent_match = re.match(r'^(\s{2,})([^-].*)$', line)
            if indent_match and in_list:
                indent = indent_match.group(1)
                content_text = indent_match.group(2).strip()
                # 检查是否是数字开头
                if re.match(r'^\d+[.．、]', content_text):
                    content_text = re.sub(r'^\d+[.．、]\s*', '', content_text)
                    result.append(f"{indent}- {content_text}")
                else:
                    result.append(f"{indent}- {content_text}")
                continue
            
            # 空行重置列表状态
            if stripped == '':
                in_list = False
                result.append('')
                continue
            
            result.append(line)
        
        return '\n'.join(result)
    
    def fix_tables(self, content: str) -> str:
        """修复表格: 确保表格有分隔行"""
        lines = content.split('\n')
        result = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # 检测表格开始 (以|开头和结尾)
            if stripped.startswith('|') and stripped.endswith('|') and stripped.count('|') >= 3:
                table_rows = [stripped]
                i += 1
                # 收集连续表格行
                while i < len(lines):
                    next_line = lines[i].strip()
                    if next_line.startswith('|') and next_line.endswith('|') and next_line.count('|') >= 3:
                        table_rows.append(next_line)
                        i += 1
                    else:
                        break
                
                # 检查是否有分隔行
                has_separator = False
                for row in table_rows:
                    if re.match(r'^[\s\|:+-]+$', row):
                        has_separator = True
                        break
                
                # 插入分隔行
                if not has_separator and len(table_rows) >= 2:
                    cols = table_rows[0].count('|') - 1
                    separator = '|' + '|'.join(['---'] * cols) + '|'
                    table_rows.insert(1, separator)
                
                result.extend(table_rows)
                result.append('')
                continue
            
            result.append(line)
            i += 1
        
        return '\n'.join(result)
    
    def fix_quotes(self, content: str) -> str:
        """修复引用: 确保引用以 > 开头"""
        lines = content.split('\n')
        result = []
        in_quote = False
        
        for line in lines:
            stripped = line.strip()
            
            # 已经是引用
            if stripped.startswith('>'):
                result.append(line)
                in_quote = True
                continue
            
            # 检测是否是引用内容 (以特殊字符开头)
            if stripped.startswith('"') or stripped.startswith('「') or stripped.startswith('『'):
                if in_quote:
                    result.append(f"> {line}")
                    continue
            
            # 空行重置引用状态
            if stripped == '':
                in_quote = False
                result.append('')
                continue
            
            result.append(line)
        
        return '\n'.join(result)
    
    def fix_hr_lines(self, content: str) -> str:
        """修复分隔线: 统一为 ---"""
        lines = content.split('\n')
        result = []
        
        for line in lines:
            stripped = line.strip()
            if re.match(r'^[-=_]{3,}$', stripped):
                result.append('---')
            else:
                result.append(line)
        
        return '\n'.join(result)
    
    def fix_emphasis(self, content: str) -> str:
        """修复强调: 确保 ** 和 * 成对"""
        # 简单的成对检测
        patterns = [
            (r'\*\*(.+?)\*\*', r'**\1**'),  # 粗体
            (r'__(.+?)__', r'__\1__'),      # 粗体
            (r'\*(.+?)\*', r'*\1*'),        # 斜体
            (r'_(.+?)_', r'_\1_'),          # 斜体
            (r'~~(.+?)~~', r'~~\1~~'),      # 删除线
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        return content
    
    def fix_links(self, content: str) -> str:
        """修复链接: 确保链接格式正确"""
        # 检测没有闭合的链接
        content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'[\1](\2)', content)
        # 检测自动链接
        content = re.sub(r'<([^>]+)>', r'<\1>', content)
        return content
    
    def fix_empty_lines(self, content: str) -> str:
        """修复空行: 保留合理空行，移除过多空行"""
        # 移除4个以上的连续空行
        content = re.sub(r'\n{5,}', '\n\n\n', content)
        # 移除行首行尾空白
        lines = content.split('\n')
        result = []
        for line in lines:
            result.append(line.rstrip())
        return '\n'.join(result)
    
    # ============================================================
    # 专门修复函数 (针对顽固问题)
    # ============================================================
        
    def fix_bash_code_blocks(self, content: str) -> str:
        """
        专门修复bash代码块
        逻辑:
          1. 删除最开头的 ```bash (多余)
          2. 遇到 "bash" 行 -> 开始代码块
          3. 持续收集命令, 直到遇到标题 (# 开头) 或文件结尾
          4. 空行保留在代码块内, 不结束代码块
        """
        lines = content.split('\n')
        result = []
        i = 0
        in_code = False
        code_lines = []
        header_pattern = re.compile(r'^#{1,6}\s+')
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # 1. 删除最开头的 ```bash
            if i == 0 and stripped == '```bash':
                i += 1
                continue
            
            # 2. 检测单独的 "bash" 行 -> 开始代码块
            if stripped == 'bash' and not in_code:
                in_code = True
                code_lines = []
                i += 1
                continue
            
            # 3. 在代码块内
            if in_code:
                # 检测到标题 -> 结束代码块, 标题由其他函数处理
                if header_pattern.match(stripped):
                    # 输出代码块
                    if code_lines:
                        result.append('```bash')
                        result.extend(code_lines)
                        result.append('```')
                    in_code = False
                    # 当前行由其他函数处理, 不跳过
                    continue
                
                # 检测到另一个 "bash" -> 结束当前代码块
                if stripped == 'bash':
                    if code_lines:
                        result.append('```bash')
                        result.extend(code_lines)
                        result.append('```')
                    in_code = False
                    # 当前行由外层循环处理
                    continue
                
                # 检测到代码块结束标记 ``` -> 结束代码块 (但不要重复添加)
                if stripped == '```':
                    if code_lines:
                        result.append('```bash')
                        result.extend(code_lines)
                        result.append('```')
                    in_code = False
                    i += 1
                    continue
                
                # 保留内容 (包括空行)
                code_lines.append(line)
                i += 1
                continue
            
            # 4. 检测已经存在的代码块 (```xxx ... ```) 保留原样
            if stripped.startswith('```') and not in_code:
                # 检测是否是代码块开始
                if len(stripped) >= 3 and stripped.endswith('```') is False:
                    # 这是 ```bash 这样的开始标记
                    result.append(line)
                    i += 1
                    in_code = True
                    code_lines = []
                    continue
            
            # 5. 普通行, 保留
            result.append(line)
            i += 1
        
        # 如果文件结尾还在代码块中, 输出代码块
        if in_code and code_lines:
            result.append('```bash')
            result.extend(code_lines)
            result.append('```')
        
        return '\n'.join(result)
    
    def fix_missing_headers(self, content: str) -> str:
        """
        专门修复缺失的标题标记
        处理: "使用方法" -> "## 使用方法"
        """
        # 常见需要加标题的词汇
        header_keywords = [
            '使用方法', '参数说明', '示例', '输出位置', 
            '常见问题', '安装', '配置', '部署', '测试',
            '功能介绍', '注意事项', '更新日志', '贡献指南'
        ]
        
        lines = content.split('\n')
        result = []
        in_code = False
        
        for line in lines:
            stripped = line.strip()
            
            # 跳过代码块内的内容
            if stripped.startswith('```'):
                in_code = not in_code
                result.append(line)
                continue
            if in_code:
                result.append(line)
                continue
            
            # 检测是否需要加标题
            for keyword in header_keywords:
                if stripped == keyword:
                    # 检查是否已经是标题
                    if not re.match(r'^#{1,6}\s+', stripped):
                        # 检查前面是否有空行
                        if result and result[-1] != '':
                            result.append('')
                        result.append(f'## {keyword}')
                        result.append('')
                        break
                    else:
                        result.append(line)
                        break
            else:
                result.append(line)
        
        return '\n'.join(result)
    
    def fix_way_headers(self, content: str) -> str:
        """
        专门修复 "方式一：xxx" 格式的标题
        """
        lines = content.split('\n')
        result = []
        
        for line in lines:
            stripped = line.strip()
            
            # 检测 "方式一：xxx" 或 "方式一: xxx"
            way_match = re.match(r'^(方式[一二三四五六七八九十]+)[：:]\s*(.+)$', stripped)
            if way_match:
                prefix = way_match.group(1)
                title = way_match.group(2).strip()
                if title:
                    result.append(f'### {prefix}：{title}')
                else:
                    result.append(f'### {prefix}')
                continue
            
            # 检测 "支持的文件格式：" 
            if stripped == '支持的文件格式：' or stripped == '支持的文件格式:':
                result.append('#### 支持的文件格式')
                continue
            
            # 检测 "方式" 开头的其他变体
            if stripped.startswith('方式') and len(stripped) < 20:
                if not re.match(r'^#{1,6}\s+', stripped):
                    result.append(f'### {stripped}')
                    continue
            
            result.append(line)
        
        return '\n'.join(result)


class MDConverter:
    """Markdown转换器主类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "md_converter"
        self.version = "3.0.0"
        self._setup_logging()
        self._setup_config()
        self.fixer = MarkdownFixer()
        
        logger.info("智能Markdown转换器 初始化完成")
    
    def _setup_logging(self):
        log_level = self.config.get("log_level", "INFO")
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    def _setup_config(self):
        defaults = {
            "output_dir": "./skills/md_converter/output",
            "default_filename": "converted_{timestamp}",
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
        
        Path(self.config["output_dir"]).mkdir(parents=True, exist_ok=True)
    
    def _read_file_content(self, file_path: str) -> str:
        """从文件读取内容"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'cp936']
        
        for encoding in encodings:
            try:
                with open(path, 'r', encoding=encoding) as f:
                    content = f.read()
                logger.info(f"成功读取文件: {file_path} (编码: {encoding})")
                return content
            except UnicodeDecodeError:
                continue
        
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    def _fix_markdown(self, content: str) -> str:
        """执行所有修复"""
        # 1. 去除 ```markdown
        content = re.sub(r'^```markdown\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'^```\s*$', '', content, flags=re.MULTILINE)
        
        # 2. 应用修复管道
        content = self.fixer.process(content)
        
        # 3. 额外修复: 移除多余的 ```markdown
        content = content.replace('```markdown', '')
        
        return content
    
    def convert(self, content: str = None, file_path: str = None,
                title: str = None, output_name: str = None) -> Dict[str, Any]:
        """转换内容为Markdown"""
        if file_path:
            logger.info(f"从文件读取: {file_path}")
            content = self._read_file_content(file_path)
            if title is None:
                title = Path(file_path).stem
        elif content:
            logger.info("使用直接传入的内容")
        else:
            raise ValueError("请提供 content 或 file_path 参数")
        
        if title is None:
            title = "转换文档"
        
        logger.info(f"开始转换: {title}")
        
        md_content = self._fix_markdown(content)
        
        # 如果没有标题，添加标题
        lines = md_content.split('\n')
        has_title = False
        for line in lines:
            if re.match(r'^#{1,6}\s+', line.strip()):
                has_title = True
                break
        
        if not has_title and title:
            md_content = f"# {title}\n\n" + md_content
        
        # 生成文件名
        if not output_name:
            if file_path:
                output_name = Path(file_path).stem + "_fixed"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_name = f"converted_{timestamp}"
        
        if not output_name.endswith('.md'):
            output_name += '.md'
        
        output_dir = Path(self.config["output_dir"])
        file_path_out = output_dir / output_name
        
        if file_path_out.exists():
            counter = 1
            base_name = output_name.replace('.md', '')
            while True:
                new_path = output_dir / f"{base_name}_{counter}.md"
                if not new_path.exists():
                    file_path_out = new_path
                    break
                counter += 1
        
        with open(file_path_out, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"已保存: {file_path_out}")
        
        return {
            "file_path": str(file_path_out),
            "content": md_content,
            "title": title,
            "size": len(md_content),
            "line_count": len(md_content.split('\n')),
            "source": file_path if file_path else "direct",
            "timestamp": datetime.now().isoformat()
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行转换"""
        logger.info(f"执行技能: {self.name} (v{self.version})")
        
        try:
            content = kwargs.get("content")
            file_path = kwargs.get("file_path")
            
            if not content and not file_path:
                return {
                    "status": "error",
                    "error": "请提供 content 或 file_path 参数",
                    "timestamp": datetime.now().isoformat()
                }
            
            title = kwargs.get("title")
            output_name = kwargs.get("output_name")
            
            result = self.convert(content, file_path, title, output_name)
            
            print("\n" + "="*60)
            print(f"✅ 转换完成!")
            print(f"  源文件: {result['source']}")
            print(f"  输出文件: {result['file_path']}")
            print(f"  大小: {result['size']} 字符")
            print(f"  行数: {result['line_count']}")
            print("="*60)
            
            print("\n📄 预览 (前800字符):")
            print("-"*40)
            preview = result['content'][:800]
            if len(result['content']) > 800:
                preview += "...\n[内容已截断，请查看完整文件]"
            print(preview)
            print("="*60 + "\n")
            
            return {
                "status": "success",
                "result": result,
                "metadata": {
                    "skill": self.name,
                    "version": self.version,
                    "executed_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"转换失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


if __name__ == "__main__":
    converter = MDConverter()