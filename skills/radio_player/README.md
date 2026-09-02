// README.md
# radio_player

> 网络广播播放器 - 直接播放网络电台

## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 15
- **函数数**: 1

## 支持的功能

| 功能 | 说明 |
|------|------|
| 📻 播放电台 | 直接播放网络广播流 |
| 🌍 多国电台 | 中日韩/国际/音乐等多种分类 |
| ⭐ 收藏功能 | 收藏喜欢的电台 |
| 🔊 音量控制 | 独立音量调节 |
| ⏯️ 播放控制 | 播放/暂停/停止 |
| 🔍 搜索功能 | 搜索电台 |
| 📋 电台列表 | 查看所有电台 |

## 内置电台分类

| 分类 | 说明 | 数量 |
|------|------|------|
| `japan` | 🇯🇵 日本电台 (NHK/TBS/J-WAVE等) | 10+ |
| `china` | 🇨🇳 中国电台 (央广/香港/澳门等) | 14+ |
| `korea` | 🇰🇷 韩国电台 (KBS/MBC/SBS等) | 5+ |
| `international` | 🌍 国际电台 (BBC/NPR/VOA等) | 12+ |
| `music` | 🎵 音乐电台 (Classic/Jazz等) | 5+ |
| `general` | 📻 综合电台 (Radio Garden等) | 3+ |

## 依赖

```bash
# VLC播放器 (推荐)
pip install python-vlc

# 或者使用系统播放器 (mpv/ffplay/mplayer)
sudo apt-get install mpv ffplay mplayer  # Ubuntu/Debian
brew install mpv ffmpeg mplayer          # macOS
```

## 使用方法

### 基础播放

```bash
# 播放默认电台 (中国之声)
python -m markflow.cli.commands execute radio_player

# 指定电台名称
python -m markflow.cli.commands execute radio_player station="中国之声"

# 指定分类
python -m markflow.cli.commands execute radio_player category="japan"

# 指定分类+电台
python -m markflow.cli.commands execute radio_player category="japan" station="NHK-FM"

# 直接播放URL
python -m markflow.cli.commands execute radio_player url="https://radio-stream.nhk.jp/hls/nhkradioruak/now/1.m3u8"
```

###播放控制
```bash
# 停止播放
python -m markflow.cli.commands execute radio_player action=stop

# 暂停/继续
python -m markflow.cli.commands execute radio_player action=pause

# 设置音量
python -m markflow.cli.commands execute radio_player action=volume volume=50
```

###列表和搜索
```bash
# 列出所有电台
python -m markflow.cli.commands execute radio_player action=list

# 列出指定分类
python -m markflow.cli.commands execute radio_player action=list category=japan

# 搜索电台
python -m markflow.cli.commands execute radio_player action=search keyword="NHK"
```
### 收藏功能
```bash
# 切换收藏
python -m markflow.cli.commands execute radio_player action=favorite station="中国之声"

# 查看收藏列表
python -m markflow.cli.commands execute radio_player action=favorites
```

### 查看播放状态
```bash
# 查看当前播放状态
python -m markflow.cli.commands execute radio_player action=status
```


## 示例

### 播放日本NHK电台

```bash
python -m markflow.cli.commands execute radio_player category=japan station="NHK-FM"
```

### 播放中国之声
```bash
python -m markflow.cli.commands execute radio_player category=china station="中国之声"
```

### 播放BBC国际广播
```bash
python -m markflow.cli.commands execute radio_player category=international station="BBC World Service"
```

### 搜索日本电台
```bash
python -m markflow.cli.commands execute radio_player action=search keyword=NHK
```

### 收藏喜欢的电台
```bash
# 收藏
python -m markflow.cli.commands execute radio_player action=favorite station="J-WAVE"

# 查看收藏
python -m markflow.cli.commands execute radio_player action=favorites

# 播放收藏的电台
python -m markflow.cli.commands execute radio_player station="J-WAVE"
```

### 支持的电台分类

| 分类 | 说明 | 示例电台 |
|------|------|----------|
| `japan` | 🇯🇵 日本电台 | NHK-FM, TBS Radio, J-WAVE, Tokyo FM |
| `china` | 🇨🇳 中国电台 | 中国之声, 经济之声, 香港电台第一台 |
| `korea` | 🇰🇷 韩国电台 | KBS 1FM, MBC FM4U, SBS Power FM |
| `international` | 🌍 国际电台 | BBC World Service, NPR, VOA |
| `music` | 🎵 音乐电台 | Classical FM, Jazz FM |
| `general` | 📻 综合电台 | Radio Garden, TuneIn Radio |

### 播放器说明

技能会自动检测并使用以下播放器（按优先级）：

1. **VLC** (python-vlc) - 推荐，功能最完整
2. **mpv** - 轻量级，支持广泛
3. **ffplay** - FFmpeg自带
4. **mplayer** - 经典播放器

### 安装播放器
```bash
# Ubuntu/Debian
sudo apt-get install vlc mpv ffmpeg mplayer

# macOS
brew install vlc mpv ffmpeg mplayer

# Windows
# 下载安装 VLC: https://www.videolan.org/vlc/
```


Python依赖安装
```bash
# VLC Python绑定
pip install python-vlc

# 或使用系统播放器（无需额外Python包）
```

## 输出位置

- 日志文件: `skills/radio_player/output/radio.log`
- 收藏数据: `skills/radio_player/output/favorites.json`

## 常见问题

### 1. 没有声音怎么办？

检查音量设置：

```bash
python -m markflow.cli.commands execute radio_player action=volume volume=100
```

### 2. 播放失败怎么办？

尝试使用不同的播放器：

```python
# 在配置中指定播放器类型
config = {
    "player_type": "mpv"  # 或 "vlc", "ffplay"
}
```
###  3. 如何添加自定义电台？
在 skill.py 的 DEFAULT_STATIONS 中添加：
```python
"custom": {
    "我的电台": "https://example.com/radio.mp3",
}
```

### 4. 电台无法播放怎么办？

- 检查网络连接
- 确认电台URL是否有效
- 尝试使用其他播放器
- 查看日志文件获取详细错误信息

###  5. 如何后台播放？

使用系统后台运行方式：

```bash
# Linux/macOS
nohup python -m markflow.cli.commands execute radio_player &

# Windows (使用start)
start python -m markflow.cli.commands execute radio_player
```

6. 如何查看当前播放状态？
```bash
python -m markflow.cli.commands execute radio_player action=status
```
