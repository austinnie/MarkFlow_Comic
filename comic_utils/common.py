from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path(__file__).parent.parent


def get_image_paths(pattern: str = "bubbled_*.png", 
                   directory: Optional[Path] = None) -> List[str]:
    """获取图片路径列表"""
    if directory is None:
        directory = PROJECT_ROOT / "skills/comics/manga_bubble_adder/output"
    
    if not directory.exists():
        return []
    
    return sorted([str(p) for p in directory.glob(pattern)])