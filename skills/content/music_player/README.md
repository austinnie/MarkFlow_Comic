# music_player

> AI 智能歌单生成和音乐管理

## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 27
- **函数数**: 1

## 支持的功能

| 功能 | 说明 |
|------|------|
| 🔍 搜索音乐 | 在线搜索 YouTube 音乐 |
| ▶️ 播放音乐 | 自动选择播放器（Moo0/VLC/浏览器） |
| 🎵 智能歌单 | 根据情绪生成播放列表 |
| 💾 保存歌单 | 保存播放列表到本地 |
| 📋 歌词显示 | 显示当前歌曲歌词 |
| 📊 播放控制 | 暂停/继续/停止/上一首/下一首 |
| 🔊 音量控制 | 调节播放音量 |
| 📁 本地扫描 | 扫描本地音乐文件 |

## 播放器支持

| 播放器 | 本地文件 | 在线音乐 | 说明 |
|--------|----------|----------|------|
| Moo0 AudioPlayer | ✅ | ❌ | 轻量稳定，优先用于本地 |
| 浏览器 | ❌ | ✅ | 在线音乐主要播放方式 |
| VLC | ✅ | ⚠️ | 作为备选 |
| 系统播放器 | ✅ | ❌ | 最后备选 |
| mpv | ✅ | ✅ | 最后备选 |

## 技能描述

AI 智能歌单生成和音乐管理

## 依赖

```bash
pip install spotipy
pip install yt-dlp
pip install mutagen
pip install pygame
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `action` | string | `` | 操作 (play/search/playlist/lyrics) |
| `query` | string | `` | 搜索关键词 |
| `playlist_name` | string | `` | 播放列表名 |
| `mood` | string | `happy` | 情绪 (happy/sad/relax/energetic) |

## 输出

| 字段 | 说明 |
|------|------|
| `tracks` | 歌曲列表 |
| `playlist` | 生成的播放列表 |
| `lyrics` | 歌词内容 |

## 使用方法

```bash
python -m markflow.cli.commands execute music_player [参数]
```

### 示例

```bash
# 搜索并播放音乐
python -m markflow.cli.commands execute music_player action="play" query="周杰伦 稻香"

# 生成开心歌单
python -m markflow.cli.commands execute music_player action="playlist" mood="happy" count=5

# 保存歌单
python -m markflow.cli.commands execute music_player action="playlist" mood="relax" save=true

# 扫描本地音乐
python -m markflow.cli.commands execute music_player action="scan"

# 查看播放状态
python -m markflow.cli.commands execute music_player action="info"
```

查看完整参数说明：

```bash
python -m markflow.cli.commands info music_player
```

### 查看播放列表

```bash
python -m markflow.cli.commands execute music_player action="info"
```

## 输出位置

生成的输出保存在 `skills/music_player/output/` 目录下。

---

*文档自动生成于 2026-08-24 00:01:22*