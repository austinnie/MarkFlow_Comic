"""
基础检查器 - 所有语言检查器的基类
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class BaseChecker:
    """基础检查器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
    
    def check(self, files: List[str], focus: str, review_level: str, max_files: int) -> Dict[str, Any]:
        """
        检查文件列表
        
        Args:
            files: 文件路径列表
            focus: 审查重点 (security/performance/style/all)
            review_level: 审查深度 (basic/deep)
            max_files: 最大文件数
            
        Returns:
            审查结果
        """
        raise NotImplementedError("子类必须实现 check 方法")
    
    def _limit_files(self, files: List[str], max_files: int) -> List[str]:
        """限制文件数量"""
        if len(files) > max_files:
            logger.info(f"限制文件数: {len(files)} -> {max_files}")
            return files[:max_files]
        return files