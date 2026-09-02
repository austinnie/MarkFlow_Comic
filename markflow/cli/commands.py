"""
命令行工具
"""

import argparse
import sys
from pathlib import Path
import json

try:
    from rich.console import Console
    from rich.table import Table
    from rich.syntax import Syntax
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # 创建简单的替代
    class Console:
        def print(self, *args, **kwargs):
            print(*args)

from ..core.executor import SkillExecutor


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="MarkFlow - 从Markdown到可执行技能",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  markflow build weather.md                    # 从Markdown构建技能
  markflow build weather.md --quality          # 构建并执行质量检查
  markflow build weather.md --tests            # 构建并生成单元测试
  markflow build weather.md --review           # 构建并执行AI代码审查
  markflow build weather.md --no-format        # 构建时不格式化代码
  markflow list                               # 列出所有技能
  markflow execute WeatherFetcher city=Beijing # 执行技能
  markflow generate -t data -n data_cleaner   # 从模板生成
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # build命令
    build_parser = subparsers.add_parser("build", help="从Markdown构建技能")
    build_parser.add_argument("file", help="Markdown文件路径")
    build_parser.add_argument("--no-save", action="store_true", help="不保存到文件")
    build_parser.add_argument("--output", "-o", default="./skills", help="输出目录")

    # ========== 新增选项 ==========
    build_parser.add_argument("--quality", "-q", action="store_true", 
                              help="执行代码质量检查")
    build_parser.add_argument("--no-quality", action="store_true", 
                              help="禁用代码质量检查")
    build_parser.add_argument("--tests", "-t", action="store_true", 
                              help="生成单元测试")
    build_parser.add_argument("--no-tests", action="store_true", 
                              help="禁用单元测试生成")
    build_parser.add_argument("--review", "-r", action="store_true", 
                              help="执行AI代码审查（需要Ollama）")
    build_parser.add_argument("--no-format", action="store_true", 
                              help="禁用代码格式化")
    build_parser.add_argument("--model", "-m", default="qwen2.5:7b", 
                              help="Ollama模型名称（用于审查）")
    build_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细日志")  # 新增                              
          
    #自动根据AI审查结果修复代码（需配合 --review 使用）           
    build_parser.add_argument("--auto-fix", "-f", action="store_true",
                             help="自动根据AI审查结果修复代码（需配合 --review 使用）")
    build_parser.add_argument("--iterations", "-i", type=int, default=1,
                             help="AI 优化迭代次数 (默认: 1)")
                         
    # execute命令
    exec_parser = subparsers.add_parser("execute", help="执行技能")
    exec_parser.add_argument("skill", help="技能名称")
    exec_parser.add_argument("params", nargs="*", help="参数 key=value")
    
    # list命令
    subparsers.add_parser("list", help="列出所有技能")
    
    # info命令
    info_parser = subparsers.add_parser("info", help="显示技能详情")
    info_parser.add_argument("skill", help="技能名称")
    
    # generate命令
    gen_parser = subparsers.add_parser("generate", help="从模板生成技能")
    gen_parser.add_argument("--template", "-t", choices=["basic", "data", "api", "automation"],
                           default="basic", help="模板类型")
    gen_parser.add_argument("--name", "-n", required=True, help="技能名称")
    gen_parser.add_argument("--description", "-d", default="", help="技能描述")
    gen_parser.add_argument("--output", "-o", default="./skills", help="输出目录")
    
    # remove命令
    remove_parser = subparsers.add_parser("remove", help="删除技能")
    remove_parser.add_argument("skill", help="技能名称")
    
    args = parser.parse_args()
    
    if RICH_AVAILABLE:
        console = Console()
    else:
        console = Console()
    
    executor = SkillExecutor()
    
    if args.command == "build":
        build_skill(args, executor, console)
    elif args.command == "execute":
        skill_name = getattr(args, 'skill', None)
        if not skill_name:
            console.print("[red]❌ 请指定技能名称[/red]")
            return
        
        # ✅ 改进参数解析 - 支持 key=value 和 key="value with spaces"
        kwargs = {}
        for param in args.params or []:
            if '=' in param:
                key, value = param.split('=', 1)
                # 移除可能的引号（支持单引号和双引号）
                value = value.strip()
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                kwargs[key] = value
        
        execute_skill(skill_name, **kwargs)
    elif args.command == "list":
        list_skills(executor, console)
    elif args.command == "info":
        show_info(args, executor, console)
    elif args.command == "generate":
        generate_skill(args, executor, console)
    elif args.command == "remove":
        remove_skill(args, executor, console)
    else:
        parser.print_help()


def build_skill(args, executor, console):
    """构建技能"""
    from pathlib import Path
    import sys
    import logging
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger('markflow').setLevel(logging.DEBUG)
        
    file_path = Path(args.file)
    
    if not file_path.exists():
        console.print("[red]错误: 文件不存在: {}[/red]".format(file_path))
        sys.exit(1)

    # ========== 确定构建参数 ==========
    quality_check = args.quality or not args.no_quality
    format_code = not args.no_format
    generate_tests = args.tests or not args.no_tests
    review = args.review
    model = args.model
    
    auto_fix = args.auto_fix
    iterations = args.iterations    
    
    try:
        # ========== 读取并解析 ==========
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

          
        # ========== 构建技能 ==========
        # 构建技能
        if auto_fix:
            console.print(f"🔧 启用自动修复模式，迭代 {iterations} 次")
            result = executor.build_from_markdown_with_auto_fix(
                content,
                save=not args.no_save,
                quality_check=quality_check,
                format_code=format_code,
                generate_tests=generate_tests,
                review=review,
                auto_fix=auto_fix,
                iterations=iterations,
                model=model
            )
        else:
            result = executor.build_from_markdown(
                content,
                save=not args.no_save,
                quality_check=quality_check,
                format_code=format_code,
                generate_tests=generate_tests,
                review=review,
                model=model
            )
        
        # ========== 显示结果 ==========
        console.print("\n[bold green]✅ 技能构建成功![/bold green]")
        console.print("  名称: [cyan]{}[/cyan]".format(result['name']))
        console.print("  类名: [cyan]{}[/cyan]".format(result['class_name']))
        console.print("  版本: [cyan]{}[/cyan]".format(result['metadata'].get('version', '1.0.0')))
        
        # 显示质量信息
        if result.get('quality'):
            quality = result['quality']
            score = quality.get('score', 0)
            if score >= 80:
                score_icon = "🟢"
            elif score >= 60:
                score_icon = "🟡"
            else:
                score_icon = "🔴"
            console.print(f"  质量评分: {score_icon} {score}/100")
            if quality.get('errors'):
                console.print(f"    ⚠️ 错误: {len(quality['errors'])} 个")
            if quality.get('warnings'):
                console.print(f"    ⚠️ 警告: {len(quality['warnings'])} 个")
        
        # 显示追溯信息
        if result.get('trace'):
            trace = result['trace']
            coverage = trace.get('coverage', 0) * 100
            console.print(f"  需求覆盖: {coverage:.1f}% ({trace.get('implemented', 0)}/{trace.get('total_requirements', 0)})")
        
        # 显示测试信息
        if result.get('tests'):
            console.print("  测试文件: [blue]tests/test_skill.py[/blue]")
        
        # 显示依赖
        if result['metadata'].get('dependencies'):
            deps = ", ".join(result['metadata']['dependencies'])
            console.print("  依赖: [yellow]{}[/yellow]".format(deps))
        

        # 显示保存位置
        if not args.no_save:
            skill_dir = executor.registry.storage_dir / result['class_name'].lower()
            console.print(f"  保存位置: [blue]{skill_dir}[/blue]")
        
        # ========== 显示审查结果 ==========
        if review and result.get('review'):
            review_result = result['review']
            console.print("\n[bold]📋 AI 审查结果:[/bold]")
            console.print(f"  评分: {review_result.get('score', 0)}/100")
            if review_result.get('issues'):
                console.print("  问题:")
                for issue in review_result['issues'][:5]:
                    console.print(f"    - {issue}")
            if review_result.get('suggestions'):
                console.print("  建议:")
                for suggestion in review_result['suggestions'][:3]:
                    console.print(f"    - {suggestion}")
        
        # ========== 显示代码预览 ==========
        if RICH_AVAILABLE:
            console.print("\n[bold]代码预览:[/bold]")
            syntax = Syntax(result['code'][:500] + "...", "python", theme="monokai")
            console.print(syntax)
        
    except Exception as e:
        console.print("[red]❌ 构建失败: {}[/red]".format(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)


def execute_skill(skill_name, **kwargs):
    """执行技能 - 支持子目录"""
    import importlib
    import importlib.util
    import sys
    from pathlib import Path
    import ast
    
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # ============================================================
    # 技能名 → 实际导入路径映射
    # ============================================================
    SKILL_PATH_MAP = {
        # ===== 图片技能 (image/) =====
        'change_pose': 'skills.image.change_pose',
        'change_expression': 'skills.image.change_expression',
        'change_face': 'skills.image.change_face',
        'change_hair': 'skills.image.change_hair',
        'change_background': 'skills.image.change_background',
        'change_clothes': 'skills.image.change_clothes',
        'change_body_type': 'skills.image.change_body_type',
        'change_lighting': 'skills.image.change_lighting',
        'change_perspective': 'skills.image.change_perspective',
        'change_eye_color': 'skills.image.change_eye_color',
        'change_makeup': 'skills.image.change_makeup',
        'change_age': 'skills.image.change_age',
        'change_gender': 'skills.image.change_gender',
        'change_nationality': 'skills.image.change_nationality',
        'change_clothing_style': 'skills.image.change_clothing_style',
        'change_furniture': 'skills.image.change_furniture',
        'change_skin_tone': 'skills.image.change_skin_tone',
        'real_to_anime': 'skills.image.real_to_anime',
        'anime_to_real': 'skills.image.anime_to_real',
        'sketch_to_real': 'skills.image.sketch_to_real',
        'style_transfer': 'skills.image.style_transfer',
        'season_transfer': 'skills.image.season_transfer',
        'weather_transfer': 'skills.image.weather_transfer',
        'day_night_transfer': 'skills.image.day_night_transfer',
        'remove_object': 'skills.image.remove_object',
        'replace_object': 'skills.image.replace_object',
        'fix_human_anatomy': 'skills.image.fix_human_anatomy',
        'old_photo_restore': 'skills.image.old_photo_restore',
        'photo_restorer': 'skills.image.photo_restorer',
        'colorize_sketch': 'skills.image.colorize_sketch',
        'fantasy_character': 'skills.image.fantasy_character',
        'mecha_generator': 'skills.image.mecha_generator',
        'human_to_robot': 'skills.image.human_to_robot',
        'sd_image_generator': 'skills.image.sd_image_generator',
        'controlnet': 'skills.image.controlnet',
        'controlnet_img2img': 'skills.image.controlnet_img2img',
        'chattoimage': 'skills.image.chattoimage',
        'add_animal_ears': 'skills.image.add_animal_ears',
        'add_glasses': 'skills.image.add_glasses',
        'add_tattoo': 'skills.image.add_tattoo',
        'add_background_objects': 'skills.image.add_background_objects',
        'expand_to_full_body': 'skills.image.expand_to_full_body',
        'photo_realistic': 'skills.image.photo_realistic',
        'nude_oil_painting': 'skills.image.nude_oil_painting',
        'nude_sculpture': 'skills.image.nude_sculpture',
        'mosaic_reducer': 'skills.image.mosaic_reducer',
        'meta_cleaner': 'skills.image.meta_cleaner',
        'signatureextractor': 'skills.image.signatureextractor',
        'exif_injector': 'skills.image.exif_injector',
        'bathroom_nude': 'skills.image.bathroom_nude',
        'beach_lingerie': 'skills.image.beach_lingerie',
        'bedroom_lingerie': 'skills.image.bedroom_lingerie',
        'bedroom_nude': 'skills.image.bedroom_nude',
        'pool_nude': 'skills.image.pool_nude',
        'studio_nude': 'skills.image.studio_nude',
        'intimate_closeup': 'skills.image.intimate_closeup',
        'remove_clothes': 'skills.image.remove_clothes',
        
        # ===== 内容技能 (content/) =====
        'novel_writer': 'skills.content.novel_writer',
        'news_aggregator': 'skills.content.news_aggregator',
        'voice_assistant': 'skills.content.voice_assistant',
        'tech_hot_article': 'skills.content.tech_hot_article',
        'music_player': 'skills.content.music_player',
        'radio_player': 'skills.content.radio_player',
        
        # ===== 核心技能 (core/) =====
        'code_gen_from_md': 'skills.core.code_gen_from_md',
        'code_reviewer': 'skills.core.code_reviewer',
        'doc_generator': 'skills.core.doc_generator',
        'md_converter': 'skills.core.md_converter',
        'imagerecognizer': 'skills.core.imagerecognizer',
        'language_learner': 'skills.core.language_learner',
        'fast_doc_point_learner': 'skills.core.fast_doc_point_learner',
        'code_relations_presents': 'skills.core.code_relations_presents',
        
        # ===== 漫画技能 (comics/) =====
        'manga_generator': 'skills.comics.manga_generator',
        'manga_script_writer': 'skills.comics.manga_script_writer',
        'manga_layout_editor': 'skills.comics.manga_layout_editor',
        'manga_style_unifier': 'skills.comics.manga_style_unifier',
        'manga_bubble_adder': 'skills.comics.manga_bubble_adder',
        'manga_to_pdf': 'skills.comics.manga_to_pdf',
        'manga_to_epub': 'skills.comics.manga_to_epub',
        'manga_audio_book': 'skills.comics.manga_audio_book',
        
        # ===== 工具技能 (utils/) =====
        'stock_analyzer': 'skills.utils.stock_analyzer',
    }
    
    skill_class = None
    module = None
    
    # markflow/cli/commands.py - 修改映射部分

    # ============================================================
    # 1. 通过映射直接导入
    # ============================================================
    if skill_name in SKILL_PATH_MAP:
        path = SKILL_PATH_MAP[skill_name]
        try:
            # ===== 修复：使用 importlib.import_module 并确保模块完全加载 =====
            module = importlib.import_module(path)
            
            # ===== 修复：强制重新加载模块，确保所有类被注册 =====
            import importlib
            module = importlib.reload(module)
            
            print(f"✅ 通过映射导入: {path}")
            
            # ===== 修复：获取模块中所有非私有属性 =====
            all_attrs = [x for x in dir(module) if not x.startswith('_')]
            print(f"   模块属性: {all_attrs}")
            
            # ===== 修复：直接查找 ChangePose 类 =====
            pure_name = skill_name
            if '.' in skill_name:
                pure_name = skill_name.split('.')[-1]
            
            # 尝试 CamelCase (change_pose → ChangePose)
            class_name = ''.join(word.capitalize() for word in pure_name.split('_'))
            print(f"   查找类名: {class_name}")
            
            # ===== 核心修复：直接从模块的 __dict__ 中查找 =====
            if hasattr(module, class_name):
                skill_class = getattr(module, class_name)
                print(f"   ✅ 找到类: {class_name}")
            else:
                # 遍历模块的 __dict__ 查找
                for attr_name, attr in module.__dict__.items():
                    if attr_name.startswith('_'):
                        continue
                    if isinstance(attr, type) and hasattr(attr, 'execute'):
                        skill_class = attr
                        print(f"   ✅ 从 __dict__ 找到类: {attr_name}")
                        break
            
            # 如果还没找到，尝试从 skill.py 文件重新加载
            if skill_class is None:
                print(f"   ⚠️ 类 {class_name} 未在模块中找到，尝试从文件加载...")
                skill_file = Path("./skills") / path.replace('.', '/') / "skill.py"
                if skill_file.exists():
                    import importlib.util
                    spec = importlib.util.spec_from_file_location(path, skill_file)
                    file_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(file_module)
                    # 从文件模块中查找
                    for attr_name in dir(file_module):
                        if attr_name.startswith('_'):
                            continue
                        attr = getattr(file_module, attr_name)
                        if isinstance(attr, type) and hasattr(attr, 'execute'):
                            skill_class = attr
                            module = file_module
                            print(f"   ✅ 从文件加载找到类: {attr_name}")
                            break
                        
        except ImportError as e:
            print(f"⚠️ 映射导入失败: {e}")
        except Exception as e:
            print(f"⚠️ 导入异常: {e}")
            import traceback
            traceback.print_exc()
    
    # ============================================================
    # 2. 如果映射失败，尝试原有自动发现
    # ============================================================
    # ... 保留原有自动发现代码 ...
    
    if not skill_class:
        print(f"❌ 未找到技能: {skill_name}")
        return False
    
    # ============================================================
    # 执行技能
    # ============================================================
    skill = skill_class()
    
    parsed_kwargs = {}
    for key, value in kwargs.items():
        if isinstance(value, str):
            try:
                parsed = ast.literal_eval(value)
                parsed_kwargs[key] = parsed
            except (ValueError, SyntaxError):
                cleaned = value.strip()
                if (cleaned.startswith('"') and cleaned.endswith('"')) or \
                   (cleaned.startswith("'") and cleaned.endswith("'")):
                    cleaned = cleaned[1:-1]
                parsed_kwargs[key] = cleaned
        else:
            parsed_kwargs[key] = value
    
    if hasattr(skill, 'execute'):
        result = skill.execute(**parsed_kwargs)
        if isinstance(result, dict):
            if result.get('status') == 'success':
                print(f"✅ 执行成功")
            else:
                print(f"❌ 执行失败: {result.get('error', '未知错误')}")
        elif result is False:
            print(f"❌ 执行失败: 返回值为 False")
        else:
            print(f"✅ 执行成功")
        return result
    else:
        print(f"❌ 技能 {skill_name} 没有 execute 方法")
        return False
        
def list_skills(executor, console):
    """列出所有技能 - 自动扫描所有子目录"""
    from pathlib import Path
    import json
    
    skill_dir = Path("./skills")
    skills = {}
    
    if skill_dir.exists():
        # 递归扫描所有子目录中的 skill.py
        for skill_file in skill_dir.rglob("skill.py"):
            # 跳过 __pycache__
            if "__pycache__" in str(skill_file):
                continue
            
            skill_dir_path = skill_file.parent
            skill_name = skill_dir_path.name
            
            # 读取 meta.json
            meta_file = skill_dir_path / "meta.json"
            metadata = {}
            if meta_file.exists():
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                except:
                    pass
            
            # 如果 meta.json 没有 name，使用目录名
            if not metadata.get('name'):
                metadata['name'] = skill_name
            
            # 获取相对路径（用于显示分类）
            rel_path = skill_dir_path.relative_to(skill_dir)
            category = str(rel_path.parent) if rel_path.parent != Path('.') else "根目录"
            
            skills[skill_name] = {
                **metadata,
                "_category": category,
                "_path": str(rel_path)
            }
    
    if not skills:
        console.print("[yellow]未找到任何技能[/yellow]")
        console.print("使用 [cyan]markflow build <file>[/cyan] 创建技能")
        return
    
    if RICH_AVAILABLE:
        table = Table(title="📚 已注册技能")
        table.add_column("分类", style="dim", no_wrap=True)
        table.add_column("名称", style="cyan", no_wrap=True)
        table.add_column("描述", style="green")
        table.add_column("版本", style="yellow")
        table.add_column("依赖", style="magenta")
        
        # 按分类排序
        for name, metadata in sorted(skills.items(), key=lambda x: (x[1].get('_category', ''), x[0])):
            table.add_row(
                metadata.get('_category', ''),
                name,
                metadata.get('description', '')[:40],
                metadata.get('version', '1.0.0'),
                ", ".join(metadata.get('dependencies', []))[:20]
            )
        
        console.print(table)
    else:
        console.print("已注册技能:")
        for name, metadata in sorted(skills.items()):
            console.print(f"  [{metadata.get('_category', '')}] {name}: {metadata.get('description', '')[:40]}")
    
    console.print("\n总计: [bold]{}[/bold] 个技能".format(len(skills)))

def show_info(args, executor, console):
    """显示技能详情"""
    from pathlib import Path
    import json
    
    skill_name = args.skill
    
    # ✅ 直接从 skills 目录读取
    skill_dir = Path("./skills") / skill_name
    meta_file = skill_dir / "meta.json"
    
    if not meta_file.exists():
        console.print(f"[red]技能 '{skill_name}' 不存在[/red]")
        console.print(f"[yellow]  请检查: {meta_file}[/yellow]")
        sys.exit(1)
    
    try:
        with open(meta_file, 'r', encoding='utf-8') as f:
            info = json.load(f)
    except Exception as e:
        console.print(f"[red]读取技能信息失败: {e}[/red]")
        sys.exit(1)
    
    console.print("\n[bold cyan]📋 {}[/bold cyan]".format(skill_name))
    console.print("  描述: {}".format(info.get('description', '')))
    console.print("  版本: {}".format(info.get('version', '1.0.0')))
    
    if info.get('tags'):
        console.print("  标签: {}".format(', '.join(info['tags'])))
    
    if info.get('dependencies'):
        console.print("  依赖: {}".format(', '.join(info['dependencies'])))
    
    if info.get('inputs'):
        console.print("\n[bold]输入参数:[/bold]")
        for inp in info['inputs']:
            required = "必填" if inp.get('required', False) else "可选"
            console.print("  - {} ({}): {} [{}]".format(
                inp['name'], 
                inp.get('type', 'string'), 
                inp.get('description', ''),
                required
            ))
    
    if info.get('outputs'):
        console.print("\n[bold]输出:[/bold]")
        for out in info['outputs']:
            console.print("  - {}: {}".format(out['name'], out.get('description', '')))
    
    if info.get('config'):
        console.print("\n[bold]配置:[/bold]")
        for key, value in info['config'].items():
            console.print("  - {}: {}".format(key, value))
    
    # 显示 skill.py 路径
    skill_file = skill_dir / "skill.py"
    if skill_file.exists():
        console.print("\n[bold]文件位置:[/bold]")
        console.print("  📄 skill.py: {}".format(skill_file))
        console.print("  📄 meta.json: {}".format(meta_file))
        console.print("  📁 output/: {}/output/".format(skill_dir))

def generate_skill(args, executor, console):
    """从模板生成技能"""
    skill_name = args.name
    skill_title = skill_name.title()
    
    templates = {
        'basic': {
            'description': '基础技能模板',
            'markdown': """# {name}

## 描述
{description}

## 目的
执行基本功能

## 输入
- input_data: string: 输入数据

## 输出
- result: 执行结果

## 步骤
1. 处理输入数据
2. 执行主要功能
3. 返回结果

## 依赖

## 示例
```python
skill = {title}()
result = skill.execute(input_data="test")
print(result)
```""".format(
                name=skill_name,
                description=args.description or skill_name + ' 基础技能',
                title=skill_title
            )
        },
        'data': {
            'description': '数据处理模板',
            'markdown': """# {name}

## 描述
{description}

## 目的
处理和分析数据

## 输入
- data_source: string: 数据源路径
- method: string: 处理方法
- output: string: 输出路径

## 输出
- processed_data: 处理后的数据
- report: 处理报告

## 步骤
1. 读取数据源
2. 数据清洗
3. 数据处理
4. 生成报告
5. 保存结果

## 依赖
- pandas
- numpy

## 示例
```python
skill = {title}()
result = skill.execute(
    data_source="data.csv",
    method="clean",
    output="result.csv"
)
```""".format(
                name=skill_name,
                description=args.description or skill_name + ' 数据处理技能',
                title=skill_title
            )
        },
        'api': {
            'description': 'API客户端模板',
            'markdown': """# {name}

## 描述
{description}

## 目的
调用外部API服务

## 输入
- endpoint: string: API端点
- method: string: HTTP方法 (GET, POST)
- params: json: 请求参数

## 输出
- response: API响应数据
- status_code: HTTP状态码

## 步骤
1. 构建请求
2. 发送请求
3. 处理响应
4. 返回数据

## 依赖
- requests

## 示例
```python
skill = {title}()
result = skill.execute(
    endpoint="/api/data",
    method="GET",
    params={{'page': 1}}
)
```""".format(
                name=skill_name,
                description=args.description or skill_name + ' API客户端',
                title=skill_title
            )
        },
        'automation': {
            'description': '自动化任务模板',
            'markdown': """# {name}

## 描述
{description}

## 目的
自动化执行重复性任务

## 输入
- schedule: string: 调度配置
- target: string: 目标
- action: string: 执行动作

## 输出
- task_id: 任务ID
- status: 任务状态

## 步骤
1. 解析任务配置
2. 执行任务
3. 记录日志
4. 返回结果

## 依赖
- schedule

## 示例
```python
skill = {title}()
result = skill.execute(
    schedule="daily",
    target="report",
    action="generate"
)
```""".format(
                name=skill_name,
                description=args.description or skill_name + ' 自动化任务',
                title=skill_title
            )
        }
    }
    
    template = templates.get(args.template, templates['basic'])
    result = executor.build_from_markdown(template['markdown'])
    
    console.print("\n[bold green]✅ 技能生成成功![/bold green]")
    console.print("  名称: [cyan]{}[/cyan]".format(result['name']))
    console.print("  模板: [yellow]{}[/yellow] ({})".format(
        args.template, 
        template['description']
    ))
    console.print("  类名: [cyan]{}[/cyan]".format(result['class_name']))
    
    code_file = executor.registry.storage_dir / "{}.py".format(result['class_name'])
    console.print("  保存位置: [blue]{}[/blue]".format(code_file))


def remove_skill(args, executor, console):
    """删除技能"""
    skill_dir = Path("./skills")
    if not skill_dir.exists():
        console.print("[yellow]没有找到技能目录[/yellow]")
        return
    
    code_file = skill_dir / "{}.py".format(args.skill)
    meta_file = skill_dir / "{}.meta.json".format(args.skill)
    
    removed = []
    if code_file.exists():
        code_file.unlink()
        removed.append(str(code_file))
    
    if meta_file.exists():
        meta_file.unlink()
        removed.append(str(meta_file))
    
    if removed:
        console.print("[green]✅ 已删除: {}[/green]".format(', '.join(removed)))
        executor.registry.unregister(args.skill)
    else:
        console.print("[yellow]未找到技能: {}[/yellow]".format(args.skill))


if __name__ == "__main__":
    main()