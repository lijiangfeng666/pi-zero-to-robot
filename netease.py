"""
网易云音乐客户端 - NetEaseClient
===============================
搜索歌曲、获取播放链接。

需要先启动 NetEaseCloudMusicApi 服务：
  cd ~/robot/netease-server && node app.js
（服务默认跑在 3000 端口）
"""
import requests
import json
import os
import time


class NetEaseClient:
    """网易云音乐 API 客户端"""

    def __init__(self, base_url=None):
        if base_url is None:
            import config
            base_url = config.NETEASE_API_BASE
        self.base_url = base_url
        self.timeout = 10
        self.session = requests.Session()
        self.cookie_file = os.path.expanduser('~/robot/netease_cookies.txt')
        self._last_refresh = 0.0
        self._refresh_interval = 43200  # 12 hours refresh interval (cookie valid 180 days)
        self._load_cookies()
        # refresh once on init to extend validity
        if os.path.exists(self.cookie_file):
            self.refresh_login()

    def _load_cookies(self):
        try:
            with open(self.cookie_file) as f:
                for line in f:
                    line = line.strip()
                    if '=' in line:
                        n, v = line.split('=', 1)
                        self.session.cookies.set(n, v)
        except (FileNotFoundError, IOError):
            pass

    def _save_cookies(self):
        try:
            with open(self.cookie_file, 'w') as f:
                for ck in self.session.cookies:
                    f.write(f'{ck.name}={ck.value}\n')
        except IOError:
            pass

    def _get(self, path, params=None):
        """GET 请求 API 服务（auto refresh cookie）"""
        self._ensure_login()
        url = f"{self.base_url}{path}"
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError:
            print("  [错误] 连不上网易云 API 服务。确认 netease-server 已启动。")
            return None
        except Exception as e:
            print(f"  [错误] 网易云 API 请求失败: {e}")
            return None

    def search(self, keyword, limit=5):
        """
        搜索歌曲。
        返回 [{id, name, artist, album}] 或空列表。
        """
        result = self._get("/search", {"keywords": keyword, "limit": limit})
        if not result or result.get("code") != 200:
            return []

        songs = []
        for s in result.get("result", {}).get("songs", []):
            songs.append({
                "id": s["id"],
                "name": s["name"],
                "artist": " / ".join(a["name"] for a in s.get("artists", [])),
                "album": s.get("album", {}).get("name", ""),
            })
        return songs

    def get_song_url(self, song_id):
        """
        获取歌曲播放链接。
        返回 URL 字符串，失败返回 None。
        """
        result = self._get("/song/url", {"id": song_id, "br": 320000})
        if not result or result.get("code") != 200:
            return None

        data = result.get("data", [])
        if data and data[0].get("url"):
            return data[0]["url"]
        return None

    def search_and_get_url(self, keyword):
        """
        搜索并返回第一首匹配歌曲的播放链接。
        返回 (song_name, url) 或 (None, None)。
        """
        songs = self.search(keyword)
        if not songs:
            return None, None

        song = songs[0]
        url = self.get_song_url(song["id"])
        return song["name"], url

    def search_by_lyric(self, fragment):
        """根据歌词片段搜索歌曲"""
        result = self._get("/search", {"keywords": fragment, "type": 1006, "limit": 5})
        return (result or {}).get("result", {}).get("songs", [])

    def get_daily_recommend(self):
        """获取每日推荐歌曲（需已登录）"""
        result = self._get("/recommend/songs")
        songs = (result or {}).get("data", {}).get("dailySongs", [])
        # 统一格式：把 ar 转成 search 返回的 artists 格式
        out = []
        for s in songs:
            artists = [{"name": a.get("name", "?")} for a in s.get("ar", [])]
            out.append({"name": s.get("name", ""), "id": s.get("id"), "artists": artists})
        return out

    def like_song(self, song_id, like=True):
        """
        收藏/取消收藏歌曲。
        需要网易云账号已登录，否则返回 301。
        返回 True=成功, False=失败, None=需要登录。
        """
        try:
            resp = self.session.post(
                f"{self.base_url}/like",
                json={"id": song_id, "like": like},
                timeout=self.timeout,
            )
            data = resp.json()
            if data.get("code") == 200:
                return True
            if data.get("code") == 301:
                return None  # 需要登录
            return False
        except Exception as e:
            print(f"  [收藏错误] {e}")
            return False

    def refresh_login(self):
        """Refresh NetEase login cookie to extend validity (+180 days)"""
        try:
            resp = self.session.post(f"{self.base_url}/login/refresh", timeout=self.timeout)
            data = resp.json()
            if data.get("code") == 200:
                self._save_cookies()
                self._last_refresh = time.time()
                print("  [Cookie] Refresh OK, extended 180 days")
                return True
            elif data.get("code") == 301:
                print("  [Cookie] Login expired, need re-login via QR code")
            else:
                print(f"  [Cookie] Refresh failed: {data}")
            return False
        except Exception as e:
            print(f"  [Cookie] Refresh error: {e}")
            return False
        finally:
            # 无论成功失败都更新刷新时间，防止每次请求都重试
            self._last_refresh = time.time()

    def _ensure_login(self):
        """Auto-refresh cookie if interval exceeded"""
        if time.time() - self._last_refresh > self._refresh_interval:
            self.refresh_login()

    def check_login(self):
        """检查是否已登录网易云账号"""
        try:
            resp = self.session.get(f"{self.base_url}/login/status", timeout=self.timeout)
            data = resp.json()
            return data.get("data", {}).get("account") is not None
        except Exception:
            return False

    def check_health(self):
        """检查 API 服务是否可用"""
        try:
            resp = self.session.get(self.base_url, timeout=self.timeout)
            return resp.status_code < 500  # 任何非服务端错误都算可用
        except requests.exceptions.ConnectionError:
            return False


    def get_dj_programs(self, radio_id, limit=100, offset=0):
        """获取DJ电台节目列表"""
        result = self._get("/dj/program/byradio", {"rid": radio_id, "limit": limit, "offset": offset})
        if not result or result.get("code") != 200:
            return []
        return result.get("programs", [])

    def search_dj_program_by_serial(self, radio_id, serial_num):
        """按集数搜索DJ节目，返回主歌曲ID"""
        import os, json
        
        cache_path = os.path.expanduser("~/robot/.sanguo_cache.json")
        programs = []
        
        # 先尝试从缓存加载
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                for p in cached:
                    if p.get("serialNum") == serial_num:
                        return p["mainSong"]["id"], p["mainSong"]["name"]
                programs = cached  # 有缓存，直接用了
            except:
                pass
        
        # 无缓存或缓存不全，重新获取（最多5页=500集，覆盖492集）
        if not programs:
            programs = []
            for page in range(5):
                batch = self.get_dj_programs(radio_id, limit=100, offset=page*100)
                if not batch:
                    break
                programs.extend(batch)
            # 保存缓存
            try:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(programs, f, ensure_ascii=False)
            except:
                pass
        
        # 查找指定集数
        for p in programs:
            if p.get("serialNum") == serial_num:
                song_id = p["mainSong"]["id"]
                song_name = p["mainSong"]["name"]
                return song_id, song_name
        
        return None, None

    def get_dj_program_url(self, radio_id, serial_num):
        """获取指定集数的播放链接"""
        song_id, name = self.search_dj_program_by_serial(radio_id, serial_num)
        if not song_id:
            return None, None
        url = self.get_song_url(song_id)
        return url, name

if __name__ == "__main__":
    """自测：python3 netease.py [关键词]"""
    import sys
    print("=" * 30)
    print("  网易云音乐自测")
    print("=" * 30)
    keyword = sys.argv[1] if len(sys.argv) > 1 else "大海"
    c = NetEaseClient()
    songs = c.search(keyword)
    if songs:
        print(f"  搜索「{keyword}」成功：")
        for s in songs:
            print(f"    {s['name']} - {s['artist']}")
    else:
        print(f"  搜索失败，确认 netease-server 已启动（curl http://127.0.0.1:3000）")
