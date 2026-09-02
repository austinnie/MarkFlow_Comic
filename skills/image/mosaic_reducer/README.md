# Mosaic Reducer - 马赛克减轻工具

> 使用多种算法减轻视频或图片中的马赛克/压缩伪影

## 功能

- 支持三种处理方案
- 支持图片和视频
- 默认使用 CPU 方案，无需 GPU

## 使用方法

### 通过 MarkFlow CLI

```bash
# 基本调用（使用默认 strength=0.7）
python -m markflow.cli.commands execute mosaic_reducer input_path="skills/mosaic_reducer/girl_05.jpg"

# 指定 strength
python -m markflow.cli.commands execute mosaic_reducer input_path="skills/mosaic_reducer/girl_05.jpg" strength=1.0

# 指定 deblur_level
python -m markflow.cli.commands execute mosaic_reducer input_path="skills/mosaic_reducer/girl_05.jpg" deblur_level=high strength=0.9


# NVIDIA GPU 方案
python -m markflow.cli.commands execute mosaic_reducer input_path="input.mp4" output_path="output.mp4" method="nvidia" scale=2

# Jasna 专用工具
python -m markflow.cli.commands execute mosaic_reducer input_path="input.png" output_path="output.png" method="jasna"
```


### 直接调用

```bash
# 低强度（轻微处理）
python skill.py -i girl_01.jpg --strength 0.3

# 单文件处理（默认强度 0.7）
python skill.py -i girl_01.jpg

# 高强度处理
python skill.py -i girl_01.jpg --strength 1.0

# 目录批量处理+强度
python skill.py -i . -o ./output --strength 0.9

```


### 代码调用

```python
from skills.mosaic_reducer.skill import MosaicReducer

reducer = MosaicReducer()
result = reducer.execute(
    input_path="input.jpg",
    output_path="output.jpg",
    method="cpu",
    deblur_level="high"
)
```

## 三种方案对比

| 方案 | 硬件要求 | 速度 | 效果 | 适用场景 |
|------|----------|------|------|----------|
| **nvidia** | NVIDIA GPU with Tensor Cores | ⚡ 快 | ⭐ 最好 | 有高端 NVIDIA 显卡，追求最佳画质 |
| **cpu** | 无特殊要求 | 🐢 较慢 | 👍 一般 | 无独显，快速测试或轻量处理 |
| **jasna** | 推荐 NVIDIA GPU | ⏱️ 视配置 | 🎯 针对性强 | 特定场景（如 JAV 马赛克修复）效果更激进 |
