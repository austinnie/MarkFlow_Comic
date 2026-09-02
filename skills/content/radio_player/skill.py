"""
radio_player - 网络广播播放器

直接播放网络广播电台
功能:
  - 播放网络广播流
  - 支持国内外电台
  - 电台收藏
  - 音量控制
"""

import os
import json
import logging
import subprocess
import threading
import time
import webbrowser
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import re
import platform

logger = logging.getLogger(__name__)


class RadioPlayer:
    """
    网络广播播放器
    """
    
    # 内置电台列表
    DEFAULT_STATIONS = {

        # ===== 日本电台 =====
        "japan": {
            "NHK-FM": "https://radio-stream.nhk.jp/hls/nhkradioruak/now/1.m3u8",
            "NHK-R1": "https://radio-stream.nhk.jp/hls/nhkradior1/now/1.m3u8",
            "NHK-R2": "https://radio-stream.nhk.jp/hls/nhkradior2/now/1.m3u8",
            "TBS Radio": "https://radiko.jp/#!/live/TBS",
            "Nippon Broadcasting": "https://radiko.jp/#!/live/QRR",
            "J-WAVE": "https://www.j-wave.co.jp/player/player.html",
            "Tokyo FM": "https://www.tfm.co.jp/player/",
            "FM802": "https://radiko.jp/#!/live/FM802",
            "FM Yokohama": "https://radiko.jp/#!/live/YFM",
            "InterFM": "https://radiko.jp/#!/live/INT",
            # 财经电台 - 使用有效链接
            "日经CNBC": "https://www.nikkei-cnbc.co.jp/",
            "Bloomberg Japan": "https://www.bloomberg.co.jp/radio/",
            "RN1": "https://radiko.jp/#!/live/RN1",
        },
        
        # ===== 中国电台 =====
        "china": {
            "中国之声": "http://ngcdn001.cnr.cn/live/zgzs/index.m3u8",
            "经济之声": "http://ngcdn001.cnr.cn/live/jjzs/index.m3u8",
            "音乐之声": "http://ngcdn001.cnr.cn/live/yyzs/index.m3u8",
            "都市之声": "http://ngcdn001.cnr.cn/live/dszs/index.m3u8",
            "中华之声": "http://ngcdn001.cnr.cn/live/zhzs/index.m3u8",
            "华夏之声": "http://ngcdn001.cnr.cn/live/hxzs/index.m3u8",
            "文艺之声": "http://ngcdn001.cnr.cn/live/wyzs/index.m3u8",
            "经典音乐广播": "http://ngcdn001.cnr.cn/live/jdyy/index.m3u8",
            "大湾区之声": "http://ngcdn001.cnr.cn/live/dwqzs/index.m3u8",
            "香港电台第一台": "https://rthkaudio1-lh.akamaihd.net/i/radio1_1@355841/master.m3u8",
            "香港电台第二台": "https://rthkaudio2-lh.akamaihd.net/i/radio2_1@355842/master.m3u8",
            "香港电台第三台": "https://rthkaudio3-lh.akamaihd.net/i/radio3_1@355843/master.m3u8",
            "香港电台第四台": "https://rthkaudio4-lh.akamaihd.net/i/radio4_1@355844/master.m3u8",
        },
        
        # ===== 韩国电台 =====
        "korea": {
            "KBS 1FM": "http://kbsradio-stream.akamaized.net/hls/live/2040613/KBSRADIO_1FM/playlist.m3u8",
            "KBS 2FM": "http://kbsradio-stream.akamaized.net/hls/live/2040614/KBSRADIO_2FM/playlist.m3u8",
            "MBC FM4U": "http://mbcradio-stream.akamaized.net/hls/live/2040615/MBCRADIO_FM4U/playlist.m3u8",
            "SBS Power FM": "http://sbsradio-stream.akamaized.net/hls/live/2040616/SBSRADIO_POWERFM/playlist.m3u8",
            "EBS FM": "https://ebsradio-stream.akamaized.net/hls/live/2040617/EBSRADIO_FM/playlist.m3u8",
        },
        
        # ===== 国际电台 =====
        "international": {
            "BBC World Service": "http://bbcwssc.ic.llnwd.net/stream/bbcwssc_mp1_ws-eieuk",
            "BBC Radio 1": "http://stream.live.vc.bbcmedia.co.uk/bbc_radio_one",
            "BBC Radio 2": "http://stream.live.vc.bbcmedia.co.uk/bbc_radio_two",
            "BBC Radio 3": "http://stream.live.vc.bbcmedia.co.uk/bbc_radio_three",
            "BBC Radio 4": "http://stream.live.vc.bbcmedia.co.uk/bbc_radio_fourfm",
            "BBC Radio 5 Live": "http://stream.live.vc.bbcmedia.co.uk/bbc_radio_five_live",
            "NPR": "https://npr-ice.streamguys1.com/live.mp3",
            "CNN Radio": "http://cnnradio.ic.llnwd.net/stream/cnnradio",
            "Voice of America": "https://voa-news.akamaized.net/hls/live/2034963/voanews/playlist.m3u8",
            "Deutsche Welle": "http://dw-radio.streamguys1.com/dw-rus",
            "France 24": "https://stream.france24.com/radio",
            "Radio France": "https://direct.franceinter.fr/live/franceinter-midfi.mp3",
        },
        
        # ===== 音乐电台 =====
        "music": {
            "Classical FM": "https://stream.radioplayer.co.uk/classicfm",
            "Jazz FM": "https://stream.radioplayer.co.uk/jazzfm",
            "Smooth FM": "https://stream.radioplayer.co.uk/smooth",
            "Heart FM": "https://stream.radioplayer.co.uk/heart",
            "Capital FM": "https://stream.radioplayer.co.uk/capital",
        },
        
        # ===== 网页电台（在浏览器中打开） =====
        "web": {
            "Radio Garden": "https://radio.garden/",
            "TuneIn Radio": "https://tunein.com/",
            "myTuner Radio": "https://mytuner-radio.com/",
            "LiveOnlineRadio": "https://www.liveonlineradio.net/",
        }
    }
    
    # 分类名称映射
    CATEGORY_NAMES = {
        "japan": "🇯🇵 日本电台",
        "china": "🇨🇳 中国电台",
        "korea": "🇰🇷 韩国电台",
        "international": "🌍 国际电台",
        "music": "🎵 音乐电台",
        "web": "🌐 网页电台",
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "radio_player"
        self.version = "1.0.0"
        self._setup_logging()
        self._setup_config()
        
        # 播放状态
        self.current_station = None
        self.is_playing = False
        self.is_paused = False
        self.volume = self.config.get("default_volume", 80)
        
        # 播放器进程
        self.player_process = None
        self.system = platform.system()
        
        # 收藏列表
        self.favorites = []
        self._load_favorites()
        
        logger.info(f"广播播放器 初始化完成 (系统: {self.system})")
    
    def _setup_logging(self):
        log_level = self.config.get("log_level", "INFO")
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    def _setup_config(self):
        defaults = {
            # ===== 播放配置 =====
            "default_volume": 80,
            "default_category": "china",
            "default_station": "中国之声",
            
            # ===== 播放器配置 =====
            "player_type": "system",  # system: 系统播放器, browser: 浏览器
            
            # ===== 输出配置 =====
            "output_dir": "./skills/radio_player/output",
            "save_log": True,
            
            # ===== 收藏配置 =====
            "favorites_file": "favorites.json",
            
            # ===== 日志配置 =====
            "log_level": "INFO",
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
        
        Path(self.config["output_dir"]).mkdir(parents=True, exist_ok=True)
    
    def _load_favorites(self):
        """加载收藏列表"""
        fav_file = Path(self.config["output_dir"]) / self.config["favorites_file"]
        if fav_file.exists():
            try:
                with open(fav_file, 'r', encoding='utf-8') as f:
                    self.favorites = json.load(f)
                logger.info(f"加载收藏: {len(self.favorites)} 个")
            except:
                self.favorites = []
    
    def _save_favorites(self):
        """保存收藏列表"""
        fav_file = Path(self.config["output_dir"]) / self.config["favorites_file"]
        try:
            with open(fav_file, 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
            logger.info(f"保存收藏: {len(self.favorites)} 个")
        except Exception as e:
            logger.error(f"保存收藏失败: {e}")
    
    def get_stations(self, category: str = None) -> Dict[str, str]:
        """获取电台列表"""
        if category:
            return self.DEFAULT_STATIONS.get(category, {})
        
        all_stations = {}
        for cat, stations in self.DEFAULT_STATIONS.items():
            all_stations.update(stations)
        return all_stations
    
    def get_categories(self) -> List[str]:
        """获取所有分类"""
        return list(self.DEFAULT_STATIONS.keys())
    
    def search_station(self, keyword: str) -> Dict[str, str]:
        """搜索电台"""
        results = {}
        keyword_lower = keyword.lower()
        
        for category, stations in self.DEFAULT_STATIONS.items():
            for name, url in stations.items():
                if keyword_lower in name.lower() or keyword_lower in category.lower():
                    results[name] = url
        
        return results
    
    def _is_web_url(self, url: str) -> bool:
        """判断是否是网页URL"""
        web_indicators = [
            ".html", ".htm",
            "radio.garden", "tunein.com", 
            "mytuner-radio.com", "liveonlineradio.net",
            "radiko.jp", "j-wave.co.jp", "tfm.co.jp"
        ]
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in web_indicators)
    
    def _play_with_system_player(self, url: str) -> bool:
        """使用系统默认播放器播放"""
        try:
            # 停止之前的播放
            self._stop_player()
            
            if self.system == "Windows":
                # Windows: 使用默认播放器
                os.startfile(url)
                self.is_playing = True
                logger.info(f"使用Windows默认播放器打开: {url}")
                return True
                
            elif self.system == "Darwin":  # macOS
                # macOS: 使用open命令
                subprocess.Popen(["open", url])
                self.is_playing = True
                logger.info(f"使用macOS默认播放器打开: {url}")
                return True
                
            else:  # Linux
                # Linux: 使用xdg-open
                subprocess.Popen(["xdg-open", url])
                self.is_playing = True
                logger.info(f"使用Linux默认播放器打开: {url}")
                return True
                
        except Exception as e:
            logger.error(f"系统播放器打开失败: {e}")
            return False
    
    def _play_with_browser(self, url: str) -> bool:
        """在浏览器中打开"""
        try:
            webbrowser.open(url)
            self.is_playing = True
            logger.info(f"在浏览器中打开: {url}")
            return True
        except Exception as e:
            logger.error(f"浏览器打开失败: {e}")
            return False
    
    def _stop_player(self):
        """停止播放器进程"""
        if self.player_process:
            try:
                self.player_process.terminate()
                self.player_process.wait(timeout=2)
            except:
                try:
                    self.player_process.kill()
                except:
                    pass
            self.player_process = None
        
        self.is_playing = False
    
    def play(self, station_name: str = None, category: str = None, url: str = None) -> bool:
        """
        播放电台
        """
        # 如果指定了URL，直接播放
        if url:
            return self._play_url(url, station_name or "自定义电台")
        
        # 根据名称和分类查找
        if station_name:
            # 先在当前分类查找
            if category:
                stations = self.DEFAULT_STATIONS.get(category, {})
                if station_name in stations:
                    return self._play_url(stations[station_name], station_name)
            
            # 在所有分类中查找
            for cat, stations in self.DEFAULT_STATIONS.items():
                if station_name in stations:
                    return self._play_url(stations[station_name], station_name)
            
            # 搜索
            results = self.search_station(station_name)
            if results:
                first_name = list(results.keys())[0]
                return self._play_url(results[first_name], first_name)
            
            logger.warning(f"未找到电台: {station_name}")
            return False
        
        # 使用默认电台
        default_category = category or self.config.get("default_category", "china")
        default_station = self.config.get("default_station", "中国之声")
        
        stations = self.DEFAULT_STATIONS.get(default_category, {})
        if default_station in stations:
            return self._play_url(stations[default_station], default_station)
        
        # 使用分类中第一个电台
        if stations:
            first_name = list(stations.keys())[0]
            return self._play_url(stations[first_name], first_name)
        
        logger.error("没有可播放的电台")
        return False
    
    def _play_url(self, url: str, name: str) -> bool:
        """播放URL"""
        self.current_station = {
            "name": name,
            "url": url,
            "started_at": datetime.now().isoformat()
        }
        
        logger.info(f"播放电台: {name} ({url})")
        
        # 判断播放方式
        player_type = self.config.get("player_type", "system")
        
        # 如果是网页电台，强制在浏览器中打开
        if self._is_web_url(url):
            logger.info("检测到网页电台，在浏览器中打开")
            return self._play_with_browser(url)
        
        # 根据配置选择播放方式
        if player_type == "browser":
            return self._play_with_browser(url)
        else:
            return self._play_with_system_player(url)
    
    def stop(self):
        """停止播放"""
        self._stop_player()
        logger.info("停止播放")
    
    def pause(self):
        """暂停/继续（仅VLC支持，系统播放器不支持）"""
        logger.warning("系统播放器不支持暂停功能")
        self.is_paused = not self.is_paused
    
    def set_volume(self, volume: int):
        """设置音量（系统播放器不支持）"""
        self.volume = max(0, min(100, volume))
        logger.info(f"设置音量: {self.volume} (系统播放器需手动调节)")
    
    def toggle_favorite(self, station_name: str) -> bool:
        """切换收藏状态"""
        if station_name in self.favorites:
            self.favorites.remove(station_name)
            self._save_favorites()
            return False
        else:
            self.favorites.append(station_name)
            self._save_favorites()
            return True
    
    def get_favorites(self) -> List[str]:
        """获取收藏列表"""
        return self.favorites
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            "is_playing": self.is_playing,
            "is_paused": self.is_paused,
            "volume": self.volume,
            "current_station": self.current_station,
            "favorites_count": len(self.favorites),
        }
    
    def list_stations(self, category: str = None) -> List[Dict]:
        """列出电台"""
        stations = []
        
        if category:
            categories = [category]
        else:
            categories = self.get_categories()
        
        for cat in categories:
            if cat in self.DEFAULT_STATIONS:
                for name, url in self.DEFAULT_STATIONS[cat].items():
                    stations.append({
                        "name": name,
                        "url": url,
                        "category": cat,
                        "category_name": self.CATEGORY_NAMES.get(cat, cat),
                        "favorite": name in self.favorites,
                        "is_web": self._is_web_url(url),
                    })
        
        return stations
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行广播播放"""
        logger.info(f"执行技能: {self.name} (v{self.version})")
        
        try:
            action = kwargs.get("action", "play")
            
            # 列表操作
            if action == "list":
                category = kwargs.get("category")
                stations = self.list_stations(category)
                
                # 打印列表到控制台
                print("\n" + "="*60)
                if category:
                    category_name = self.CATEGORY_NAMES.get(category, category)
                    print(f"📻 {category_name} ({len(stations)} 个电台)")
                else:
                    print(f"📻 全部电台 ({len(stations)} 个)")
                print("="*60)
                
                if stations:
                    current_category = None
                    for i, station in enumerate(stations, 1):
                        # 分类分组显示
                        if station["category"] != current_category:
                            current_category = station["category"]
                            cat_name = self.CATEGORY_NAMES.get(current_category, current_category)
                            print(f"\n【{cat_name}】")
                        
                        fav_mark = "⭐" if station["favorite"] else "  "
                        web_mark = "🌐" if station.get("is_web", False) else "📻"
                        print(f"  {fav_mark} {i}. {web_mark} {station['name']}")
                else:
                    print("❌ 没有找到电台\n")
                
                print("\n" + "="*60 + "\n")
                
                return {
                    "status": "success",
                    "action": "list",
                    "stations": stations,
                    "count": len(stations),
                    "timestamp": datetime.now().isoformat()
                }
            
            # 搜索操作
            if action == "search":
                keyword = kwargs.get("keyword")
                if not keyword:
                    return {"status": "error", "error": "请指定搜索关键词"}
                results = self.search_station(keyword)
                
                # 打印搜索结果到控制台
                print("\n" + "="*60)
                print(f"🔍 搜索关键词: {keyword}")
                print("="*60)
                
                if results:
                    print(f"找到 {len(results)} 个电台:\n")
                    for i, (name, url) in enumerate(results.items(), 1):
                        print(f"  {i}. {name}")
                        print(f"     URL: {url}\n")
                else:
                    print("❌ 未找到匹配的电台\n")
                
                print("="*60 + "\n")
                
                return {
                    "status": "success",
                    "action": "search",
                    "keyword": keyword,
                    "results": results,
                    "count": len(results),
                    "timestamp": datetime.now().isoformat()
                }
            
            # 状态操作
            if action == "status":
                return {
                    "status": "success",
                    "action": "status",
                    "status": self.get_status(),
                    "timestamp": datetime.now().isoformat()
                }
            
            # 停止操作
            if action == "stop":
                self.stop()
                return {
                    "status": "success",
                    "action": "stop",
                    "message": "已停止播放",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 暂停操作
            if action == "pause":
                self.pause()
                return {
                    "status": "success",
                    "action": "pause",
                    "is_paused": self.is_paused,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 音量操作
            if action == "volume":
                volume = kwargs.get("volume")
                if volume is not None:
                    self.set_volume(volume)
                return {
                    "status": "success",
                    "action": "volume",
                    "volume": self.volume,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 收藏操作
            if action == "favorite":
                station = kwargs.get("station")
                if not station:
                    return {"status": "error", "error": "请指定电台名称"}
                
                is_favorite = self.toggle_favorite(station)
                return {
                    "status": "success",
                    "action": "favorite",
                    "station": station,
                    "is_favorite": is_favorite,
                    "favorites": self.favorites,
                    "timestamp": datetime.now().isoformat()
                }
            
            if action == "favorites":
                return {
                    "status": "success",
                    "action": "favorites",
                    "favorites": self.get_favorites(),
                    "count": len(self.favorites),
                    "timestamp": datetime.now().isoformat()
                }
            
            # 播放操作 (默认)
            if action == "play":
                station = kwargs.get("station")
                category = kwargs.get("category")
                url = kwargs.get("url")
                
                # 如果指定了URL，直接播放
                if url:
                    success = self._play_url(url, kwargs.get("name", "自定义电台"))
                    return {
                        "status": "success" if success else "error",
                        "action": "play",
                        "message": "播放中" if success else "播放失败",
                        "url": url,
                        "timestamp": datetime.now().isoformat()
                    }
                
                success = self.play(station, category)
                
                if success:
                    return {
                        "status": "success",
                        "action": "play",
                        "station": self.current_station["name"] if self.current_station else station,
                        "url": self.current_station["url"] if self.current_station else None,
                        "message": "播放中",
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "status": "error",
                        "action": "play",
                        "error": f"无法播放: {station or '默认电台'}",
                        "timestamp": datetime.now().isoformat()
                    }
            
            return {
                "status": "error",
                "error": f"未知操作: {action}",
                "timestamp": datetime.now().isoformat()
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
        return f"<RadioPlayer(name={self.name}, version={self.version})>"


# 便捷函数
def play_radio(station: str = None, category: str = None):
    """快速播放电台"""
    player = RadioPlayer()
    return player.play(station, category)


if __name__ == "__main__":
    # 测试
    player = RadioPlayer()
    
    # 列出中国电台
    print("中国电台:")
    for station in player.list_stations("china"):
        print(f"  {station['name']}")