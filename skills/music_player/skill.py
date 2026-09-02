"""
music_player - 音乐播放器

AI 智能歌单生成和音乐管理

功能:
  - AI 歌单推荐 (基于情绪/场景)
  - 音乐搜索 (本地/在线)
  - 歌词显示
  - 本地播放 (支持 mp3, wav, flac, m4a)
  - 播放列表管理
"""

import os
import time
import json
import logging
import random
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import re

logger = logging.getLogger(__name__)

# 依赖导入
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    from mutagen.mp3 import MP3
    from mutagen.flac import FLAC
    from mutagen.wave import WAVE
    from mutagen.mp4 import MP4
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    SPOTIPY_AVAILABLE = True
except ImportError:
    SPOTIPY_AVAILABLE = False


class MusicPlayer:
    """
    音乐播放器 - 智能音乐管理
    """
    
    # 支持的音乐格式
    SUPPORTED_FORMATS = ['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg']
    
    # 情绪对应的歌曲风格
    MOOD_STYLES = {
        'happy': ['pop', 'dance', 'happy', 'upbeat', 'party'],
        'sad': ['ballad', 'acoustic', 'sad', 'slow', 'emotional'],
        'relax': ['chill', 'lofi', 'acoustic', 'ambient', 'jazz'],
        'energetic': ['rock', 'electronic', 'workout', 'high energy', 'drum and bass'],
        'focus': ['classical', 'piano', 'instrumental', 'study', 'ambient'],
        'romantic': ['love', 'r&b', 'soul', 'romantic', 'slow jam'],
        'nostalgic': ['retro', '80s', '90s', 'classic', 'old school'],
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "music_player"
        self.version = "1.0.0"
        self._setup_logging()
        self._setup_config()
        self._init_player()
        
        logger.info(f"音乐播放器 初始化完成")
        if not PYGAME_AVAILABLE:
            logger.warning("pygame 未安装，播放功能不可用")
    
    def _setup_logging(self):
        log_level = self.config.get("log_level", "INFO")
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    def _setup_config(self):
        defaults = {
            "output_dir": "./skills/music_player/output",
            "music_dir": "./skills/music_player/output",  # ← 直接指向 output
            "playlist_dir": "./skills/music_player/playlists",
            "default_volume": 0.7,
            "max_search_results": 20,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
        
        # 创建必要的目录
        for key in ["output_dir", "playlist_dir"]:
            Path(self.config[key]).mkdir(parents=True, exist_ok=True)
        # music_dir 和 output_dir 是同一个目录，不需要重复创建
    
    def _init_player(self):
        """初始化播放器"""
        self.current_track = None
        self.current_playlist = []
        self.playlist_index = -1
        self.is_playing = False
        self.volume = self.config.get("default_volume", 0.7)
        self.play_history = []
        
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=2)
                pygame.mixer.music.set_volume(self.volume)
                logger.info("播放器初始化成功")
            except Exception as e:
                logger.error(f"播放器初始化失败: {e}")
    
    def _validate_inputs(self, **kwargs) -> bool:
        required = ["action"]
        for param in required:
            if param not in kwargs or not kwargs[param]:
                raise ValueError(f"缺少必需参数: {param}")
        
        action = kwargs["action"]
        valid_actions = ["play", "search", "playlist", "lyrics", "pause", "resume", 
                "stop", "next", "previous", "volume", "info", "scan", "download"]
        if action not in valid_actions:
            raise ValueError(f"不支持的操作: {action}，支持: {valid_actions}")
        
        return True
    
    def _scan_music(self, music_dir: str = None) -> List[Dict]:
        """扫描本地音乐文件"""
        music_dir = music_dir or self.config.get("music_dir")
        path = Path(music_dir)
        if not path.exists():
            return []
        
        tracks = []
        for ext in self.SUPPORTED_FORMATS:
            for file_path in path.rglob(f"*{ext}"):
                track = self._get_track_info(file_path)
                if track:
                    tracks.append(track)
        
        logger.info(f"扫描完成，找到 {len(tracks)} 首歌曲")
        return tracks
    
    def _get_track_info(self, file_path: Path) -> Dict:
        """获取歌曲信息"""
        track = {
            "path": str(file_path),
            "title": file_path.stem,
            "artist": "未知艺术家",
            "album": "未知专辑",
            "duration": 0,
            "format": file_path.suffix,
            "size": file_path.stat().st_size,
        }
        
        if MUTAGEN_AVAILABLE:
            try:
                if file_path.suffix == '.mp3':
                    audio = MP3(file_path)
                    if audio.get('TPE1'):
                        track["artist"] = str(audio.get('TPE1')[0])
                    if audio.get('TIT2'):
                        track["title"] = str(audio.get('TIT2')[0])
                    if audio.get('TALB'):
                        track["album"] = str(audio.get('TALB')[0])
                    track["duration"] = audio.info.length
                elif file_path.suffix == '.flac':
                    audio = FLAC(file_path)
                    if audio.get('artist'):
                        track["artist"] = audio.get('artist')[0]
                    if audio.get('title'):
                        track["title"] = audio.get('title')[0]
                    if audio.get('album'):
                        track["album"] = audio.get('album')[0]
                    track["duration"] = audio.info.length
            except Exception as e:
                logger.warning(f"读取标签失败: {e}")
        
        return track
    
    def _search_local(self, query: str, tracks: List[Dict]) -> List[Dict]:
        """在本地音乐中搜索"""
        results = []
        query_lower = query.lower()
        logger.info(f"搜索本地: query='{query_lower}', 本地歌曲数={len(tracks)}")
        
        for track in tracks:
            title_lower = track["title"].lower()
            artist_lower = track["artist"].lower()
            album_lower = track["album"].lower()
            
            logger.info(f"  检查: '{title_lower}' 包含 '{query_lower}'? {query_lower in title_lower}")
            
            if (query_lower in title_lower or 
                query_lower in artist_lower or
                query_lower in album_lower):
                results.append(track)
                logger.info(f"  ✅ 匹配: {track['title']}")
        
        logger.info(f"本地搜索找到 {len(results)} 个结果")
        return results
    
    def _search_online(self, query: str, limit: int = 10) -> List[Dict]:
        """在线搜索音乐（使用 yt-dlp）"""
        results = []
        
        if not YT_DLP_AVAILABLE:
            logger.warning("yt-dlp 未安装")
            return results
        
        try:
            ydl_opts = {
                'quiet': True,
                'extract_flat': False,  # ✅ 改为 False，获取完整信息
                'skip_download': True,   # ✅ 不下载
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_query = f'ytsearch{limit}:{query}'
                info = ydl.extract_info(search_query, download=False)
                if info and 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            results.append({
                                "title": entry.get('title', '未知'),
                                "artist": entry.get('uploader', '未知'),
                                "url": entry.get('webpage_url', '') or entry.get('original_url', ''),
                                "duration": entry.get('duration', 0),
                                "source": "youtube",
                            })
                    logger.info(f"在线搜索找到 {len(results)} 个结果")
                else:
                    logger.warning("未找到搜索结果")
        except Exception as e:
            logger.warning(f"在线搜索失败: {e}")
        
        return results
    
    def _generate_playlist(self, mood: str = "happy", count: int = 10) -> List[Dict]:
        """根据情绪生成播放列表"""
        tracks = self._scan_music()
        if not tracks:
            # 如果没有本地音乐，返回模拟播放列表
            return self._generate_mock_playlist(mood, count)
        
        # 根据风格筛选
        styles = self.MOOD_STYLES.get(mood, self.MOOD_STYLES['happy'])
        filtered = []
        for track in tracks:
            # 简单匹配：检查标题是否包含风格关键词
            title_lower = track["title"].lower()
            artist_lower = track["artist"].lower()
            for style in styles:
                if style in title_lower or style in artist_lower:
                    filtered.append(track)
                    break
        
        # 如果匹配太少，补充随机歌曲
        if len(filtered) < count:
            remaining = [t for t in tracks if t not in filtered]
            random.shuffle(remaining)
            filtered.extend(remaining[:count - len(filtered)])
        
        # 随机选择 count 首
        random.shuffle(filtered)
        return filtered[:count]
    
    def _generate_mock_playlist(self, mood: str, count: int) -> List[Dict]:
        """生成模拟播放列表"""
        mock_tracks = {
            'happy': [
                {"title": "Happy", "artist": "Pharrell Williams", "duration": 215},
                {"title": "Can't Stop The Feeling", "artist": "Justin Timberlake", "duration": 235},
                {"title": "Uptown Funk", "artist": "Bruno Mars", "duration": 270},
            ],
            'sad': [
                {"title": "Someone Like You", "artist": "Adele", "duration": 285},
                {"title": "Fix You", "artist": "Coldplay", "duration": 270},
            ],
            'relax': [
                {"title": "Weightless", "artist": "Marconi Union", "duration": 480},
                {"title": "Clair de Lune", "artist": "Debussy", "duration": 300},
            ],
            'energetic': [
                {"title": "Eye of the Tiger", "artist": "Survivor", "duration": 240},
                {"title": "Lose Yourself", "artist": "Eminem", "duration": 326},
            ],
            'focus': [
                {"title": "Piano Sonata No. 14", "artist": "Beethoven", "duration": 360},
                {"title": "The Four Seasons", "artist": "Vivaldi", "duration": 420},
            ],
            'romantic': [
                {"title": "Perfect", "artist": "Ed Sheeran", "duration": 263},
                {"title": "All of Me", "artist": "John Legend", "duration": 273},
            ],
            'nostalgic': [
                {"title": "Bohemian Rhapsody", "artist": "Queen", "duration": 355},
                {"title": "Hotel California", "artist": "Eagles", "duration": 390},
            ],
        }
        
        tracks = mock_tracks.get(mood, mock_tracks['happy'])
        # 复制并扩展
        result = []
        while len(result) < count:
            for t in tracks:
                if len(result) >= count:
                    break
                result.append(t.copy())
        return result
    

    def _play(self, track: Dict) -> Dict:
        """播放歌曲 - 支持多种播放方式，自动选择最佳方案"""
        try:
            url = track.get("url") or track.get("path")
            title = track.get("title", "未知歌曲")
            artist = track.get("artist", "未知艺术家")
            
            if not url:
                return {"error": "没有可播放的源", "status": "error"}
            
            # 获取可用播放器列表（按优先级排序）
            players = self._detect_players()
            logger.info(f"可用播放器: {[p[0] for p in players]}")
            
            # 尝试每种播放器
            for player_name, player_cmd in players:
                result = self._play_with_player(player_name, player_cmd, url, track)
                if result and result.get("status") == "playing":
                    return result
                elif result and result.get("status") == "error":
                    logger.warning(f"播放器 {player_name} 失败: {result.get('error', '未知错误')}")
                    continue
            
            # 所有播放器都失败
            return {"error": "所有播放器均无法播放", "status": "error"}
            
        except Exception as e:
            logger.error(f"播放失败: {e}")
            return {"error": str(e), "status": "error"}

    def _play_with_player(self, player_name: str, player_cmd: str, url: str, track: Dict) -> Optional[Dict]:
        """使用指定播放器播放"""
        import subprocess
        import sys
        import platform
        
        title = track.get("title", "未知歌曲")
        artist = track.get("artist", "未知艺术家")
        
        try:
            if player_name == "moo0":
                if not url.startswith(('http://', 'https://')):
                    subprocess.Popen([player_cmd, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.current_track = track
                    self.is_playing = True
                    self.playback_source = "moo0"
                    logger.info(f"使用 Moo0 AudioPlayer 播放: {title}")
                    return {
                        "status": "playing",
                        "track": track,
                        "source": url,
                        "player": "moo0",
                        "message": f"正在播放: {title} - {artist}"
                    }
                else:
                    return {"status": "error", "error": "Moo0 不支持网络播放"}
            
            elif player_name == "vlc":
                subprocess.Popen([player_cmd, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.current_track = track
                self.is_playing = True
                self.playback_source = "vlc"
                logger.info(f"使用 VLC 播放: {title} - {artist}")
                return {
                    "status": "playing",
                    "track": track,
                    "source": url,
                    "player": "vlc",
                    "message": f"正在播放: {title} - {artist}"
                }
            
            elif player_name == "browser":
                import webbrowser
                webbrowser.open(url)
                self.current_track = track
                self.is_playing = True
                self.playback_source = "browser"
                logger.info(f"使用浏览器播放: {title} - {artist}")
                return {
                    "status": "playing",
                    "track": track,
                    "source": url,
                    "player": "browser",
                    "message": f"正在播放: {title} - {artist}"
                }
            
            elif player_name == "system":
                system = platform.system()
                if system == 'Windows':
                    os.startfile(url)
                elif system == 'Darwin':
                    subprocess.Popen(['open', url])
                else:
                    subprocess.Popen(['xdg-open', url])
                self.current_track = track
                self.is_playing = True
                self.playback_source = "system"
                logger.info(f"使用系统播放器播放: {title}")
                return {
                    "status": "playing",
                    "track": track,
                    "source": url,
                    "player": "system",
                    "message": f"正在播放: {title} - {artist}"
                }
            
            elif player_name == "mpv":
                # mpv 放最后
                cmd = [
                    player_cmd,
                    url,
                    '--no-video',
                    '--ytdl-format=bestaudio',
                    '--ytdl',
                    '--ytdl-path=' + sys.executable
                ]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.current_track = track
                self.is_playing = True
                self.playback_source = "mpv"
                logger.info(f"使用 mpv 播放: {title} - {artist}")
                return {
                    "status": "playing",
                    "track": track,
                    "source": url,
                    "player": "mpv",
                    "message": f"正在播放: {title} - {artist}"
                }
            
            return {"status": "error", "error": f"未知播放器: {player_name}"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
        
    def _detect_players(self) -> List[tuple]:
        """检测系统中可用的播放器（按优先级排序）"""
        from pathlib import Path
        import shutil
        
        players = []
        
        # 1. Moo0 AudioPlayer（轻量稳定，仅本地文件）
        moo0_path = r"C:\Program Files (x86)\Moo0\AudioPlayer 1.58\AudioPlayer.exe"
        if Path(moo0_path).exists():
            players.append(("moo0", moo0_path))
        
        # 2. 浏览器（YouTube 在线播放，总是可用）← 移到 VLC 前面
        players.append(("browser", "browser"))
        
        # 3. VLC（支持 YouTube + 本地，但 YouTube 可能不稳定）
        vlc_paths = [
            r"C:\Program Files\VideoLAN\VLC\vlc.exe",
            r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
        ]
        for path in vlc_paths:
            if Path(path).exists():
                players.append(("vlc", path))
                break
        else:
            if shutil.which('vlc'):
                players.append(("vlc", "vlc"))
        
        # 4. 系统默认播放器（备选）
        players.append(("system", "system"))
        
        return players
    
    def _play_playlist(self, playlist: List[Dict], index: int = 0) -> Dict:
        """播放播放列表"""
        if not playlist:
            return {"error": "播放列表为空", "status": "error"}
        
        if index >= len(playlist):
            index = 0
        
        self.current_playlist = playlist
        self.playlist_index = index
        
        return self._play(playlist[index])
    
    def _pause(self) -> Dict:
        """暂停"""
        if PYGAME_AVAILABLE:
            pygame.mixer.music.pause()
            self.is_playing = False
            return {"status": "paused", "message": "已暂停"}
        return {"error": "播放器未初始化", "status": "error"}
    
    def _resume(self) -> Dict:
        """继续播放"""
        if PYGAME_AVAILABLE:
            pygame.mixer.music.unpause()
            self.is_playing = True
            return {"status": "playing", "message": "继续播放"}
        return {"error": "播放器未初始化", "status": "error"}
    
    def _stop(self) -> Dict:
        """停止播放"""
        if PYGAME_AVAILABLE:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.current_track = None
            return {"status": "stopped", "message": "已停止"}
        return {"error": "播放器未初始化", "status": "error"}
    
    def _next_track(self) -> Dict:
        """下一首"""
        if not self.current_playlist:
            return {"error": "没有播放列表", "status": "error"}
        
        if self.playlist_index + 1 < len(self.current_playlist):
            self.playlist_index += 1
            return self._play(self.current_playlist[self.playlist_index])
        else:
            return {"status": "end", "message": "播放列表已结束"}
    
    def _prev_track(self) -> Dict:
        """上一首"""
        if not self.current_playlist:
            return {"error": "没有播放列表", "status": "error"}
        
        if self.playlist_index - 1 >= 0:
            self.playlist_index -= 1
            return self._play(self.current_playlist[self.playlist_index])
        else:
            return {"error": "已是第一首", "status": "error"}
    
    def _set_volume(self, volume: float) -> Dict:
        """设置音量"""
        try:
            volume = max(0, min(1, float(volume)))
            self.volume = volume
            if PYGAME_AVAILABLE:
                pygame.mixer.music.set_volume(volume)
            return {"status": "success", "volume": volume}
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def _get_lyrics(self, track: Dict) -> Dict:
        """获取歌词（模拟）"""
        # 实际应用中可以使用 Genius API 或 LRCLIB
        title = track.get("title", "")
        artist = track.get("artist", "")
        
        mock_lyrics = f"""
[{title}]
{artist}

Verse 1:
这是 {title} 的歌词示例
实际歌词需要接入 Genius API 或 LRCLIB

Chorus:
♪ 音乐是生活的调味剂 ♪
♪ 让每一天都充满旋律 ♪

Outro:
感谢聆听
"""
        return {
            "title": title,
            "artist": artist,
            "lyrics": mock_lyrics,
            "source": "mock",
        }
    
    def _save_playlist(self, name: str, tracks: List[Dict]) -> Dict:
        """保存播放列表"""
        playlist_dir = Path(self.config.get("playlist_dir"))
        playlist_dir.mkdir(parents=True, exist_ok=True)
        
        playlist_file = playlist_dir / f"{name}.json"
        data = {
            "name": name,
            "created_at": datetime.now().isoformat(),
            "tracks": tracks,
            "count": len(tracks),
        }
        
        with open(playlist_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return {"status": "success", "file": str(playlist_file), "count": len(tracks)}
    
    def _load_playlist(self, name: str) -> List[Dict]:
        """加载播放列表"""
        playlist_dir = Path(self.config.get("playlist_dir"))
        playlist_file = playlist_dir / f"{name}.json"
        
        if not playlist_file.exists():
            return None
        
        with open(playlist_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get("tracks", [])

    def _get_status(self) -> Dict:
        """获取播放状态"""
        return {
            "is_playing": self.is_playing,
            "current_track": self.current_track,
            "playlist_index": self.playlist_index,
            "playlist_size": len(self.current_playlist),
            "volume": self.volume,
        }


    def _download(self, query: str, output_dir: str = None, format: str = "mp3") -> Dict:
        """下载音乐（使用 yt-dlp）"""
        if not YT_DLP_AVAILABLE:
            return {"error": "yt-dlp 未安装", "status": "error"}
        
        output_dir = output_dir or self.config.get("output_dir", "./skills/music_player/output/downloads")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        try:
            import yt_dlp
            
            # 先搜索找到视频 URL
            search_query = f'ytsearch1:{query}'
            ydl_opts_search = {
                'quiet': True,
                'extract_flat': False,  # ✅ 改为 False 获取完整信息
            }
            
            with yt_dlp.YoutubeDL(ydl_opts_search) as ydl:
                info = ydl.extract_info(search_query, download=False)
                if not info or not info.get('entries'):
                    return {"error": f"未找到: {query}", "status": "error"}
                entry = info['entries'][0]
                
                # ✅ 获取 URL 的多种方式
                url = entry.get('webpage_url')
                if not url:
                    url = entry.get('original_url')
                if not url:
                    url = entry.get('url')
                if not url:
                    return {"error": "无法获取视频链接", "status": "error"}
                
                title = entry.get('title', '未知歌曲')
                uploader = entry.get('uploader', '未知艺术家')
            
            # 下载音频
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': format,
                    'preferredquality': '192',
                }],
                'outtmpl': str(Path(output_dir) / f'%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # 查找下载的文件
            downloaded_files = list(Path(output_dir).glob(f"*{title}*.{format}"))
            if not downloaded_files:
                downloaded_files = list(Path(output_dir).glob(f"*{title}*"))
            
            return {
                "status": "success",
                "title": title,
                "artist": uploader,
                "url": url,
                "format": format,
                "output_dir": str(output_dir),
                "files": [str(f) for f in downloaded_files],
                "message": f"已下载: {title} - {uploader}"
            }
            
        except Exception as e:
            logger.error(f"下载失败: {e}")
            return {"error": str(e), "status": "error"}
            
 
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行音乐播放操作"""
        start_time = time.time()
        logger.info(f"执行技能: {self.name} (v{self.version})")
        
        try:
            self._validate_inputs(**kwargs)
            
            action = kwargs.get("action")
            query = kwargs.get("query", "")
            playlist_name = kwargs.get("playlist_name", "")
            mood = kwargs.get("mood", "happy")
            volume = kwargs.get("volume", None)
            
            result = {}
            
            if action == "search":
                query = query or kwargs.get("query", "")
                if not query:
                    return {"status": "error", "error": "搜索需要 query 参数"}
                
                # 先搜索本地
                local_tracks = self._scan_music()
                local_results = self._search_local(query, local_tracks)
                
                # 如果有本地结果，直接返回，不搜在线
                if local_results:
                    result = {
                        "local": local_results[:10],
                        "total_local": len(local_results),
                        "total_online": 0,
                        "source": "local"
                    }
                else:
                    # 本地没有，搜索在线
                    online_results = self._search_online(query, 10)
                    result = {
                        "local": [],
                        "online": online_results[:10],
                        "total_local": 0,
                        "total_online": len(online_results),
                        "source": "online"
                    }
            
            elif action == "playlist":
                # 生成播放列表
                if playlist_name:
                    # 加载已保存的播放列表
                    tracks = self._load_playlist(playlist_name)
                    if tracks is None:
                        return {"status": "error", "error": f"播放列表 {playlist_name} 不存在"}
                    
                    result = {
                        "name": playlist_name,
                        "tracks": tracks,
                        "count": len(tracks),
                        "action": "load_playlist",
                    }
                    
                    # 开始播放
                    play_result = self._play_playlist(tracks)
                    result["play_result"] = play_result
                else:
                    # 生成新播放列表
                    count = int(kwargs.get("count", 10))
                    tracks = self._generate_playlist(mood, count)
                    
                    result = {
                        "mood": mood,
                        "tracks": tracks,
                        "count": len(tracks),
                        "action": "generate_playlist",
                    }
                    
                    # 如果指定了保存
                    if kwargs.get("save", False):
                        save_name = playlist_name or f"playlist_{mood}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        save_result = self._save_playlist(save_name, tracks)
                        result["saved"] = save_result
            
            elif action == "play":
                query = kwargs.get("query", "")
                url = kwargs.get("url", "")
                
                if query and not url:
                    # 先搜索本地
                    local_tracks = self._scan_music()
                    local_results = self._search_local(query, local_tracks)
                    
                    if local_results:
                        track = local_results[0]
                        result = self._play(track)
                    else:
                        # 本地没有，搜索在线
                        results = self._search_online(query, 1)
                        if results:
                            track = results[0]
                            result = self._play(track)
                        else:
                            return {"status": "error", "error": f"未找到歌曲: {query}"}
                elif url:

                    # 直接播放 URL
                    track = {
                        "title": kwargs.get("title", "在线歌曲"),
                        "artist": kwargs.get("artist", "未知艺术家"),
                        "url": url,
                    }
                    result = self._play(track)
                else:
                    # 继续播放当前
                    if self.current_track:
                        result = self._resume()
                    else:
                        return {"status": "error", "error": "没有正在播放的歌曲"}
            
            elif action == "pause":
                result = self._pause()
            
            elif action == "resume":
                result = self._resume()
            
            elif action == "stop":
                result = self._stop()
            
            elif action == "next":
                result = self._next_track()
            
            elif action == "previous":
                result = self._prev_track()
            
            elif action == "volume":
                if volume is not None:
                    result = self._set_volume(volume)
                else:
                    result = {"status": "success", "volume": self.volume}
            
            elif action == "info":
                # 显示当前播放信息
                result = self._get_status()
                result["status"] = "success"
            
            elif action == "lyrics":
                # 获取歌词
                track = self.current_track or {}
                result = self._get_lyrics(track)
                result["status"] = "success"
            
            elif action == "scan":
                # 扫描本地音乐
                tracks = self._scan_music()
                result = {
                    "total": len(tracks),
                    "tracks": tracks[:20],  # 只返回前20首
                    "status": "success",
                }

            elif action == "download":
                query = kwargs.get("query", "")
                if not query:
                    return {"status": "error", "error": "下载需要 query 参数"}
                
                format = kwargs.get("format", "mp3")
                output_dir = kwargs.get("output_dir", None)
                result = self._download(query, output_dir, format)
                
            else:
                return {"status": "error", "error": f"未知操作: {action}"}
            
            # 统一格式
            return {
                "status": "success" if result.get("status") != "error" else "error",
                "result": result,
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
        return f"<MusicPlayer(name={self.name}, version={self.version})>"