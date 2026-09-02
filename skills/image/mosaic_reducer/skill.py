# skills/mosaic_reducer/skill.py
"""
mosaic_reducer - 视频/图片马赛克减轻工具
支持三种方案：NVIDIA GPU加速、通用CPU、专用工具(Jasna)
默认使用方案二(CPU)
支持单文件或目录批量处理
处理完成后自动对比原图并输出差异数据
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
import logging

logger = logging.getLogger(__name__)

# 项目路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# ==================== 检查依赖 ====================
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import numpy as np
    from PIL import Image, ImageFilter, ImageEnhance
    import cv2
    CV_AVAILABLE = True
except ImportError as e:
    CV_AVAILABLE = False
    logger.warning(f"部分依赖未安装: {e}")

# ==================== 方案三：Jasna ====================
JASNA_AVAILABLE = False
try:
    result = subprocess.run(["jasna", "--help"], capture_output=True, timeout=5)
    if result.returncode == 0:
        JASNA_AVAILABLE = True
except (subprocess.SubprocessError, FileNotFoundError):
    pass

# ==================== 支持的文件扩展名 ====================
IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.gif'}
VIDEO_EXTS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}


def compare_images(original_path: str, processed_path: str) -> Dict[str, Any]:
    """
    对比两张图片的像素差异
    
    Args:
        original_path: 原图路径
        processed_path: 处理后的图片路径
    
    Returns:
        包含差异数据的字典
    """
    try:
        img1 = Image.open(original_path).convert('RGB')
        img2 = Image.open(processed_path).convert('RGB')
        
        if img1.size != img2.size:
            logger.warning(f"  图片尺寸不一致，将处理后的图片缩放到原图尺寸")
            img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)
        
        arr1 = np.array(img1, dtype=np.int16)
        arr2 = np.array(img2, dtype=np.int16)
        
        diff = np.abs(arr1 - arr2)
        
        mean_diff = np.mean(diff)
        max_diff = np.max(diff)
        std_diff = np.std(diff)
        diff_percent = (mean_diff / 255) * 100
        changed_pixels = np.sum(diff > 2) / diff.size * 100
        
        if mean_diff > 15:
            conclusion = "✅ 变化明显 - 处理效果显著"
            level = "high"
        elif mean_diff > 8:
            conclusion = "🟡 有一定变化 - 处理效果可见"
            level = "medium"
        elif mean_diff > 3:
            conclusion = "🔸 变化轻微 - 处理效果较弱"
            level = "low"
        else:
            conclusion = "❌ 几乎无变化 - 处理效果不明显"
            level = "none"
        
        return {
            "status": "success",
            "mean_diff": float(mean_diff),
            "max_diff": int(max_diff),
            "std_diff": float(std_diff),
            "diff_percent": float(diff_percent),
            "changed_pixels_percent": float(changed_pixels),
            "conclusion": conclusion,
            "level": level,
            "width": img1.size[0],
            "height": img1.size[1],
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


class MosaicReducer:
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "mosaic_reducer"
        self.version = "1.0.0"
        
        self.skill_dir = Path(__file__).parent.absolute()
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        self.default_method = self.config.get('default_method', 'cpu')
        
        self._setup_logging()
        self._setup_config()
        
        logger.info(f"MosaicReducer v{self.version} 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  默认方案: {self.default_method}")
        logger.info(f"  Jasna 可用: {JASNA_AVAILABLE}")
    
    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _setup_config(self):
        defaults = {
            'default_method': 'cpu',
            'default_scale': 2,
            'default_quality': 'HIGH',
            'default_deblur_level': 'high',
            'default_strength': 0.7,
            'recursive': False,
            'overwrite': False,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def _get_default_config(self) -> Dict:
        return {
            'default_method': 'cpu',
            'default_scale': 2,
            'default_quality': 'HIGH',
            'default_deblur_level': 'high',
            'default_strength': 0.7,
            'recursive': False,
            'overwrite': False,
        }
    
    def _is_image(self, path: Path) -> bool:
        return path.suffix.lower() in IMAGE_EXTS
    
    def _is_video(self, path: Path) -> bool:
        return path.suffix.lower() in VIDEO_EXTS
    
    def _is_supported(self, path: Path) -> bool:
        return self._is_image(path) or self._is_video(path)
    
    def _scan_files(self, input_path: Path, recursive: bool = False) -> List[Path]:
        files = []
        if recursive:
            for ext in IMAGE_EXTS | VIDEO_EXTS:
                files.extend(input_path.rglob(f"*{ext}"))
        else:
            for ext in IMAGE_EXTS | VIDEO_EXTS:
                files.extend(input_path.glob(f"*{ext}"))
        return sorted(files)
    
    def _generate_output_path(self, input_path: Path, output_dir: Path, 
                              suffix: str = "_reduced") -> Path:
        stem = input_path.stem
        ext = input_path.suffix
        return output_dir / f"{stem}{suffix}{ext}"
    
    # ==================== 方案一：NVIDIA GPU ====================
    
    def _method_nvidia_gpu(self, input_path: str, output_path: str, 
                           scale: int = 2, quality: str = "HIGH") -> Dict:
        logger.info(f"[方案一] NVIDIA GPU 加速 (scale={scale}, quality={quality})")
        
        if not TORCH_AVAILABLE:
            return {"status": "error", "error": "PyTorch 未安装", "method": "nvidia"}
        
        if not torch.cuda.is_available():
            return {"status": "error", "error": "未检测到 CUDA GPU", "method": "nvidia"}
        
        try:
            try:
                from nvvfx import ImageSuperRes
                if self._is_image(Path(input_path)):
                    processor = ImageSuperRes(scale=scale, quality=quality)
                    processor.process(input_path, output_path)
                    return {
                        "status": "success",
                        "output_path": output_path,
                        "method": "nvidia",
                        "scale": scale,
                        "quality": quality,
                        "type": "image"
                    }
            except ImportError:
                pass
            
            from PIL import Image
            import torchvision.transforms as transforms
            from torch.nn.functional import interpolate
            
            img = Image.open(input_path).convert('RGB')
            tensor = transforms.ToTensor()(img).unsqueeze(0).cuda()
            output_tensor = interpolate(tensor, scale_factor=scale, mode='bicubic', align_corners=False)
            output_img = transforms.ToPILImage()(output_tensor.cpu().squeeze(0))
            output_img.save(output_path)
            
            return {
                "status": "success",
                "output_path": output_path,
                "method": "nvidia",
                "scale": scale,
                "quality": quality,
                "type": "image"
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "method": "nvidia"}
    
    # ==================== 方案二：通用 CPU ====================
    
    def _method_cpu(self, input_path: str, output_path: str,
                    deblur_level: str = "high", strength: float = 0.7) -> Dict:
        logger.info(f"[方案二] 通用 CPU (deblur_level={deblur_level}, strength={strength})")
        
        input_path = Path(input_path)
        if not input_path.exists():
            return {"status": "error", "error": f"文件不存在: {input_path}"}
        
        try:
            if self._is_image(input_path):
                return self._process_image_cpu(str(input_path), output_path, deblur_level, strength)
            elif self._is_video(input_path):
                return self._process_video_cpu(str(input_path), output_path, deblur_level, strength)
            else:
                return {"status": "error", "error": f"不支持的文件类型: {input_path.suffix}"}
        except Exception as e:
            logger.error(f"CPU 处理失败: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e), "method": "cpu"}
    
    def _process_image_cpu(self, input_path: str, output_path: str,
                           deblur_level: str, strength: float = 0.7) -> Dict:
        import cv2
        import numpy as np
        from PIL import Image, ImageEnhance
        
        img = cv2.imread(input_path)
        if img is None:
            return self._process_image_cpu_pil(input_path, output_path, deblur_level, strength)
        
        # 【修改说明 1】动态降低降噪强度，strength 控制去噪半径，防止过度涂抹
        if deblur_level == "high":
            denoise_h = 5 + int(strength * 5)  # 最高不超过 10
            radius = 7
        else:  # medium / low
            denoise_h = 3 + int(strength * 3)  # 最高不超过 6
            radius = 5
            
        # 1. 核心降噪：仅保留轻量的非局部均值去噪，防止出现大面积色块
        img = cv2.fastNlMeansDenoisingColored(img, None, denoise_h, denoise_h, radius, 21)
        
        # 2. 轻微的双边滤波，平滑锯齿边缘，但保留面部轮廓
        img = cv2.bilateralFilter(img, 5, 25, 25)
        
        # 【修改说明 2】完全删除了 CLAHE 和锐化核 (Sharpen Kernel)！
        # 这两步是产生大量黑白噪点和怪异的锐化环的元凶。
        
        # 3. 转换为 PIL 进行极其轻柔的后期处理
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        
        # 【修改说明 3】降低对比度，防止马赛克色块被强行拉开导致变黑/变白
        # 力度受 strength 控制，但上限很低
        contrast_amount = 0.95 + (strength * 0.05)  # 范围 0.95 ~ 1.0，基本不调整
        enhancer = ImageEnhance.Contrast(pil_img)
        pil_img = enhancer.enhance(contrast_amount)
        
        # 【修改说明 4】纯靠 PIL 做极轻微的柔和锐化，使用 UnsharpMask (代替生硬的卷积核)
        # 降低锐化百分比和半径，保留画面自然纹理
        sharpen_percent = int(30 + strength * 20)  # 30%~50%
        pil_img = pil_img.filter(ImageFilter.UnsharpMask(radius=1, percent=sharpen_percent, threshold=2))
        
        pil_img.save(output_path, quality=95, subsampling=0)
        
        return {
            "status": "success",
            "output_path": output_path,
            "method": "cpu",
            "deblur_level": deblur_level,
            "strength": strength,
            "type": "image"
        }

    def _process_image_cpu_pil(self, input_path: str, output_path: str,
                                deblur_level: str, strength: float = 0.7) -> Dict:
        from PIL import Image, ImageFilter, ImageEnhance
        
        img = Image.open(input_path).convert('RGB')
        
        # 【修改说明 5】彻底重写 PIL 回退方案
        # 1. 使用中值滤波去除孤立的噪点，但不破坏图像结构
        if deblur_level == "high":
            img = img.filter(ImageFilter.MedianFilter(size=3))
            # 改为极度柔和的 UnsharpMask
            img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=50 + int(strength * 30), threshold=2))
        else:
            img = img.filter(ImageFilter.MedianFilter(size=3))
            # 仅仅做轻微锐化
            img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=30 + int(strength * 20), threshold=2))
        
        # 【修改说明 6】不再使用强力的 Contrast 增强 (原代码 0.8 + strength * 0.6 可能导致高光死白、暗部死黑)
        contrast_amount = 0.95 + (strength * 0.05)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast_amount)
        
        # 【修改说明 7】极轻的饱和度调整，让画面色彩看起来不那么干瘪
        saturation_amount = 0.95 + (strength * 0.05)
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(saturation_amount)
        
        img.save(output_path, quality=95)
        
        return {
            "status": "success",
            "output_path": output_path,
            "method": "cpu",
            "deblur_level": deblur_level,
            "strength": strength,
            "type": "image",
            "note": "使用 PIL 回退方案 (轻量去噪)"
        }
        
    def _process_video_cpu(self, input_path: str, output_path: str,
                           deblur_level: str, strength: float = 0.7) -> Dict:
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            return {"status": "error", "error": "无法打开视频"}
        
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        denoise_h = int(5 + strength * 10)
        clahe_clip = 1.5 + strength * 1.5
        sharpen_kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]]) if deblur_level == "high" else None
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = cv2.fastNlMeansDenoisingColored(frame, None, denoise_h, denoise_h, 7, 21)
            
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=clahe_clip, tileGridSize=(8, 8))
            l = clahe.apply(l)
            lab = cv2.merge((l, a, b))
            frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            if sharpen_kernel is not None:
                frame = cv2.filter2D(frame, -1, sharpen_kernel)
            
            out.write(frame)
            
            frame_count += 1
            if frame_count % 30 == 0:
                logger.info(f"  进度: {frame_count}/{total_frames} 帧")
        
        cap.release()
        out.release()
        
        return {
            "status": "success",
            "output_path": output_path,
            "method": "cpu",
            "deblur_level": deblur_level,
            "strength": strength,
            "frames": frame_count,
            "type": "video"
        }
    
    # ==================== 方案三：Jasna ====================
    
    def _method_jasna(self, input_path: str, output_path: str,
                      detection_model: str = "rfdetr-v6") -> Dict:
        logger.info(f"[方案三] Jasna (detection_model={detection_model})")
        
        if not JASNA_AVAILABLE:
            return {
                "status": "error",
                "error": "Jasna 未安装。请从 https://github.com/Kruk2/jasna 下载",
                "method": "jasna"
            }
        
        try:
            cmd = ["jasna", "--input", input_path, "--output", output_path,
                   "--detection-model", detection_model]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                return {"status": "error", "error": result.stderr, "method": "jasna"}
            return {
                "status": "success",
                "output_path": output_path,
                "method": "jasna",
                "detection_model": detection_model
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": "Jasna 处理超时", "method": "jasna"}
        except Exception as e:
            return {"status": "error", "error": str(e), "method": "jasna"}
    
    # ==================== 单文件处理 ====================
    
    def _process_single(self, input_path: Path, output_path: Optional[Path],
                        method: str, **kwargs) -> Dict:
        """处理单个文件，并自动对比"""
        if output_path is None:
            output_path = self._generate_output_path(input_path, self.output_dir)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        original_path = str(input_path)
        
        # ============================================================
        # 修复：安全获取参数，确保有默认值
        # ============================================================
        if method == "nvidia":
            scale = kwargs.get('scale')
            if scale is None:
                scale = self.config.get('default_scale', 2)
            quality = kwargs.get('quality')
            if quality is None:
                quality = self.config.get('default_quality', 'HIGH')
            result = self._method_nvidia_gpu(original_path, str(output_path), scale, quality)
            
        elif method == "jasna":
            detection_model = kwargs.get('detection_model')
            if detection_model is None:
                detection_model = 'rfdetr-v6'
            result = self._method_jasna(original_path, str(output_path), detection_model)
            
        else:  # cpu (默认)
            deblur_level = kwargs.get('deblur_level')
            if deblur_level is None:
                deblur_level = self.config.get('default_deblur_level', 'high')
            
            strength = kwargs.get('strength')
            if strength is None:
                strength = self.config.get('default_strength', 0.7)
            else:
                try:
                    strength = float(strength)
                except (ValueError, TypeError):
                    strength = 0.7
            
            result = self._method_cpu(original_path, str(output_path), deblur_level, strength)
        
        # ===== 如果是图片，自动对比 =====
        if result.get('status') == 'success' and self._is_image(input_path):
            logger.info("  🔍 对比原图与处理后的图片...")
            compare_result = compare_images(original_path, str(output_path))
            
            if compare_result.get('status') == 'success':
                result['comparison'] = {
                    'mean_diff': compare_result['mean_diff'],
                    'max_diff': compare_result['max_diff'],
                    'std_diff': compare_result['std_diff'],
                    'diff_percent': compare_result['diff_percent'],
                    'changed_pixels_percent': compare_result['changed_pixels_percent'],
                    'conclusion': compare_result['conclusion'],
                    'level': compare_result['level'],
                    'dimensions': f"{compare_result['width']}x{compare_result['height']}"
                }
                
                logger.info(f"    📊 平均差异: {compare_result['mean_diff']:.2f} | 最大差异: {compare_result['max_diff']}")
                logger.info(f"    📊 差异百分比: {compare_result['diff_percent']:.2f}% | 变化像素: {compare_result['changed_pixels_percent']:.1f}%")
                logger.info(f"    📊 结论: {compare_result['conclusion']}")
            else:
                result['comparison'] = {'status': 'error', 'error': compare_result.get('error')}
        
        return result
    
    # ==================== 批量处理 ====================
    
    def _process_batch(self, input_dir: Path, output_dir: Path,
                       method: str, recursive: bool = False,
                       overwrite: bool = False, **kwargs) -> Dict:
        """批量处理目录下的所有文件"""
        files = self._scan_files(input_dir, recursive)
        
        if not files:
            return {"status": "error", "error": f"目录中未找到支持的文件: {input_dir}"}
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📁 找到 {len(files)} 个文件")
        logger.info("=" * 60)
        
        results = []
        success_count = 0
        skip_count = 0
        fail_count = 0
        
        all_comparisons = []
        
        for idx, file_path in enumerate(files, 1):
            logger.info(f"\n[{idx}/{len(files)}] 处理: {file_path.name}")
            
            rel_path = file_path.relative_to(input_dir)
            output_path = output_dir / rel_path
            output_path = self._generate_output_path(output_path, output_path.parent)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if output_path.exists() and not overwrite:
                logger.info(f"  ⏭️ 跳过 (已存在): {output_path.name}")
                skip_count += 1
                continue
            
            result = self._process_single(file_path, output_path, method, **kwargs)
            
            if result.get('status') == 'success':
                success_count += 1
                results.append(result)
                
                if 'comparison' in result and result['comparison'].get('status') == 'success':
                    all_comparisons.append({
                        'file': file_path.name,
                        **result['comparison']
                    })
            else:
                fail_count += 1
                logger.error(f"  ❌ 失败: {result.get('error')}")
        
        if all_comparisons:
            logger.info("\n" + "=" * 60)
            logger.info("📊 批量对比汇总")
            logger.info("=" * 60)
            
            avg_diffs = [c['mean_diff'] for c in all_comparisons]
            max_diffs = [c['max_diff'] for c in all_comparisons]
            
            logger.info(f"  平均差异范围: {min(avg_diffs):.2f} ~ {max(avg_diffs):.2f}")
            logger.info(f"  平均差异均值: {sum(avg_diffs)/len(avg_diffs):.2f}")
            logger.info(f"  最大差异均值: {sum(max_diffs)/len(max_diffs):.1f}")
            
            levels = {'high': 0, 'medium': 0, 'low': 0, 'none': 0}
            for c in all_comparisons:
                levels[c.get('level', 'none')] += 1
            
            logger.info(f"  效果等级: ✅变化明显={levels['high']} | 🟡有一定变化={levels['medium']} | 🔸变化轻微={levels['low']} | ❌几乎无变化={levels['none']}")
            logger.info("=" * 60)
        
        return {
            "status": "success" if fail_count == 0 else "partial",
            "total": len(files),
            "success": success_count,
            "skipped": skip_count,
            "failed": fail_count,
            "output_dir": str(output_dir),
            "results": results,
            "method_used": method,
            "comparison_summary": {
                "total_compared": len(all_comparisons),
                "avg_mean_diff": sum([c['mean_diff'] for c in all_comparisons]) / len(all_comparisons) if all_comparisons else 0,
                "level_counts": levels if all_comparisons else {}
            } if all_comparisons else None
        }
    
    # ==================== 主执行方法 ====================
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"执行技能: {self.name} (v{self.version})")
        
        try:
            input_path = kwargs.get('input_path')
            if not input_path:
                return {"status": "error", "error": "input_path 是必填参数"}
            
            input_path = Path(input_path).absolute()
            if not input_path.exists():
                return {"status": "error", "error": f"输入路径不存在: {input_path}"}
            
            method = kwargs.get('method', self.config.get('default_method', 'cpu'))
            recursive = kwargs.get('recursive', self.config.get('recursive', False))
            overwrite = kwargs.get('overwrite', self.config.get('overwrite', False))
            output_path = kwargs.get('output_path')
            
            if input_path.is_dir():
                if output_path is None:
                    output_path = self.output_dir / input_path.name
                else:
                    output_path = Path(output_path)
                
                result = self._process_batch(
                    input_path, output_path, method,
                    recursive=recursive,
                    overwrite=overwrite,
                    scale=kwargs.get('scale'),
                    quality=kwargs.get('quality'),
                    deblur_level=kwargs.get('deblur_level'),
                    strength=kwargs.get('strength'),
                    detection_model=kwargs.get('detection_model')
                )
            else:
                if not self._is_supported(input_path):
                    return {"status": "error", "error": f"不支持的文件类型: {input_path.suffix}"}
                
                if output_path is None:
                    output_path = self._generate_output_path(input_path, self.output_dir)
                else:
                    output_path = Path(output_path)
                
                result = self._process_single(
                    input_path, output_path, method,
                    scale=kwargs.get('scale'),
                    quality=kwargs.get('quality'),
                    deblur_level=kwargs.get('deblur_level'),
                    strength=kwargs.get('strength'),
                    detection_model=kwargs.get('detection_model')
                )
            
            if isinstance(result, dict):
                result["generation_time"] = f"{time.time() - start_time:.2f}s"
                result["input_path"] = str(input_path)
                if "method_used" not in result:
                    result["method_used"] = method
            
            logger.info(f"✅ 完成! 耗时: {result.get('generation_time')}")
            return result
            
        except Exception as e:
            logger.error(f"执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}
    
    def __repr__(self):
        return f"<MosaicReducer(name={self.name}, version={self.version})>"


# ==================== 命令行入口 ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="视频/图片马赛克减轻工具 (支持目录批量处理，自动对比)",
        epilog="""
示例:
  # 单文件处理
  python skill.py -i input.jpg
  
  # 指定强度和输出
  python skill.py -i input.jpg -o output.jpg --strength 0.9
  
  # 目录批量处理
  python skill.py -i ./images -o ./output
        """
    )
    
    parser.add_argument("-i", "--input", required=True, help="输入文件或目录路径")
    parser.add_argument("-o", "--output", help="输出文件或目录路径")
    parser.add_argument("-m", "--method", default="cpu",
                        choices=["nvidia", "cpu", "jasna"],
                        help="处理方法 (默认: cpu)")
    parser.add_argument("--recursive", "-r", action="store_true",
                        help="递归扫描子目录")
    parser.add_argument("--overwrite", action="store_true",
                        help="覆盖已存在的文件")
    parser.add_argument("--strength", "-s", type=float, default=0.7,
                        help="处理强度 0.1-1.0 (默认: 0.7)")
    parser.add_argument("--scale", type=int, default=2, choices=[1, 2, 3, 4],
                        help="[nvidia] 超分倍数")
    parser.add_argument("--quality", default="HIGH",
                        choices=["LOW", "MEDIUM", "HIGH", "ULTRA"],
                        help="[nvidia] 质量等级")
    parser.add_argument("--deblur-level", default="high",
                        choices=["medium", "high"],
                        help="[cpu] 去模糊强度")
    parser.add_argument("--detection-model", default="rfdetr-v6",
                        choices=["rfdetr-v6", "rfdetr-v6-large", "lada-yolo-v4"],
                        help="[jasna] 检测模型")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    
    args = parser.parse_args()
    
    skill = MosaicReducer(config={'device': args.device})
    result = skill.execute(
        input_path=args.input,
        output_path=args.output,
        method=args.method,
        recursive=args.recursive,
        overwrite=args.overwrite,
        strength=args.strength,
        scale=args.scale,
        quality=args.quality,
        deblur_level=args.deblur_level,
        detection_model=args.detection_model
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))