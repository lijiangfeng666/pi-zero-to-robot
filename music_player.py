"""
音乐播放器 - MusicPlayer
========================
播放、暂停、切歌、音量控制、播放模式、收藏、信息查询。
底层使用 mpg123 播放音乐。

使用前需安装：
  sudo apt install mpg123

交互规则见：Obsidian → 12 - 交互规则 → 音乐播放
"""
import os
import subprocess
import signal
import time
import threading
import requests
import config


class MusicPlayer:
    """音乐播放控制器（完整版）"""

    def __init__(self, netease_client=None):
        self.netease = netease_client
        self.process = None          # mpg123 子进程
        self.current_song = None     # 当前歌曲名
        self.current_artist = None   # 当前歌手
        self.current_url = None      # 当前播放链接
        self.volume = 1.0            # 初始 100%，PipeWire 系统音量
        # 启动时同步初始音量到 PipeWire
        self._apply_pipewire_volume()
        # 取消静音
        import subprocess
        try:
            sink = subprocess.run(["pactl", "get-default-sink"], capture_output=True, text=True, timeout=5).stdout.strip()
            if sink:
                subprocess.run(["pactl", "set-sink-mute", sink, "0"], capture_output=True, timeout=5)
        except Exception:
            pass
        print(f"  PipeWire 音量: {int(self.volume * 100)}%")
        # ALSA 硬件音量拉到最大（重启会重置，每次初始化设一次）
        try:
            subprocess.run(["amixer", "-c", "4", "cset", "numid=4", "255"], capture_output=True, timeout=5)
        except Exception:
            pass
        self.is_paused = False
        self._saved_volume = None
        self.play_mode = "order"     # order | shuffle | loop
        self.history = []            # 播放历史 [{song, artist, url}]
        self.history_index = -1      # 历史索引
        self.recommend_queue = []    # 每日推荐队列
        self.recommend_index = -1   # 队列索引
        self._play_start_time = 0.0  # 当前歌曲开始播放的时间戳
        self._retry_count = 0  # 当前歌曲重试次数，防止死循环

    @property
    def is_playing(self):
        """是否有音乐正在播放"""
        return self.process is not None and not self.is_paused
    # --------------------------------------------------
    # 播放
    # --------------------------------------------------
    def play_url(self, name, url):
        """直接通过URL播放（用于DJ电台等）"""
        self.stop()
        self.current_song = name
        self.current_url = url
        self.is_paused = False
        return self._start_mpg123()

    def play(self, keyword):
        keyword = keyword.strip().rstrip("，。,．.!！？?；;：: ")
        """搜索并播放音乐，添加历史记录"""
        if not self.netease:
            return "未连接音乐服务"

        songs = self.netease.search(keyword)
        if not songs:
            return f"没找到「{keyword}」的音乐"
        song = songs[0]
        url = self.netease.get_song_url(song["id"])
        if not url:
            return f"无法获取「{keyword}」的播放链接"

        self.stop()
        self.current_song = song["name"]
        self.current_artist = song["artist"]
        self.current_url = url
        self.is_paused = False

        # 记录历史：如果在历史中间位置，截断后面
        entry = {"song": self.current_song, "artist": self.current_artist, "url": self.current_url}
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        self.history.append(entry)
        self.history_index = len(self.history) - 1

        return self._start_mpg123()

    def _start_mpg123(self):
        """启动 mpg123 子进程，通过管道传入音频数据（带 Referer 头，避免 403）"""
        if not self.current_url:
            return
        # 音量方案：PipeWire 100%（系统），mpg123 内部音量控制
        self._apply_pipewire_volume()
        vol_arg = int(32768 * self.volume)  # mpg123 内部音量 = self.volume（默认 30%）
        try:
            self.process = subprocess.Popen(
                ["mpg123", "-q", "-f", str(vol_arg), "-"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            return "播放失败：没装 mpg123（sudo apt install mpg123）"
        except Exception as e:
            return f"播放失败：{e}"

        self._play_start_time = time.time()
        self._retry_count = 0
        self._start_audio_feeder()
        self._start_auto_next()
        return f"正在播放：{self.current_song} - {self.current_artist}"

    def _feed_audio(self):
        """后台线程：下载音频数据（带 Referer 头）并喂给 mpg123 的 stdin"""
        url = self.current_url
        proc = self.process
        if not url or not proc:
            return
        try:
            headers = {
                "Referer": "https://music.163.com",
                "User-Agent": "Mozilla/5.0 (X11; Linux) Chrome/120",
            }
            resp = requests.get(url, headers=headers, stream=True, timeout=15)
            resp.raise_for_status()
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk and proc.poll() is None:
                    proc.stdin.write(chunk)
                else:
                    break
        except (BrokenPipeError, OSError):
            pass
            pass  # mpg123 已被停止
        finally:
            try:
                proc.stdin.close()
            except Exception:
                pass

    def _start_audio_feeder(self):
        """启动音频下载线程"""
        t = threading.Thread(target=self._feed_audio, daemon=True)
        t.start()

    def _start_auto_next(self):
        """后台线程：歌曲结束后自动处理。播放<60秒视为试听/网络中断，重试当前歌曲；正常完成则播下一首"""
        def monitor():
            proc = self.process
            start = self._play_start_time
            song_name = self.current_song
            if not proc:
                return
            try:
                proc.wait()
            except Exception:
                return
            if self.process is not proc:
                return  # 已被切歌/停止，不触发
            elapsed = time.time() - start
            # 播放时间过短（试听版/网络中断）：重试当前歌曲，最多2次
            if elapsed < 60 and self._retry_count < 2:
                self._retry_count += 1
                print(f"  [auto-next] 仅播放{elapsed:.0f}秒，可能是试听版/网络中断，第{self._retry_count}次重试")
                if song_name:
                    self.play(song_name)
                return
            # 正常播完：播下一首
            if elapsed >= 60 and not self.is_paused:
                print(f"  [auto-next] 播放完成（{elapsed:.0f}秒），播下一首")
                self._play_next_from_recommend()
            elif elapsed < 60:
                print(f"  [auto-next] 重试{self._retry_count}次仍失败，停止播放")

        t = threading.Thread(target=monitor, daemon=True)
        t.start()

    def _apply_pipewire_volume(self):
        """调音量：优先调mpg123的sink-input，没有则调系统音量"""
        import subprocess
        try:
            out = subprocess.run(["pactl", "list", "sink-inputs"], capture_output=True, text=True, timeout=5).stdout
            found = False
            for block in out.split("Sink Input #")[1:]:
                if "mpg123" in block:
                    sid = block.split("\n")[0].strip()
                    subprocess.run(["pactl", "set-sink-input-volume", sid, f"{int(self.volume * 100)}%"], capture_output=True, timeout=5)
                    found = True
                    break
            if not found:
                # 无mpg123进程（初始化或未播放），直接调系统音量
                sink = subprocess.run(["pactl", "get-default-sink"], capture_output=True, text=True, timeout=5).stdout.strip()
                if sink:
                    subprocess.run(["pactl", "set-sink-volume", sink, f"{int(self.volume * 100)}%"], capture_output=True, timeout=5)
        except Exception:
            pass

    def _play_next_from_recommend(self):
        """从每日推荐队列播下一首，队列空了重新获取"""
        import subprocess
        # 队列已空或未初始化，重新获取每日推荐
        if self.recommend_index >= len(self.recommend_queue) - 1:
            print("  获取每日推荐歌曲...")
            try:
                songs = self.netease.get_daily_recommend()
                if not songs:
                    # 后备：随机歌手
                    import random
                    fallback = ["周杰伦", "林俊杰", "陈奕迅", "邓紫棋"]
                    return self.play(random.choice(fallback))
                self.recommend_queue = songs
                self.recommend_index = 0
            except Exception as e:
                print(f"  每日推荐失败: {e}")
                import random
                fallback = ["周杰伦", "林俊杰", "陈奕迅", "邓紫棋"]
                return self.play(random.choice(fallback))
        else:
            self.recommend_index += 1

        song = self.recommend_queue[self.recommend_index]
        name = song.get("name", "")
        artist = song.get("artists", [{}])[0].get("name", "")
        print(f"  每日推荐: {name} - {artist}")
        return self.play(name)

    def stop(self):
        """停止播放（先置空 process，防止 auto-next 线程误判）"""
        proc = self.process
        self.process = None
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                proc.kill()
        self.is_paused = False

    # --------------------------------------------------
    # 暂停 / 继续
    # --------------------------------------------------
    def pause(self):
        """暂停播放"""
        if not self.process and not self.is_paused:
            return "当前没有播放"
        if self.is_paused:
            return "已经是暂停状态"
        self.is_paused = True
        proc = self.process
        self.process = None  # 置空防止 auto-next 线程误判继续播下一首
        if proc:
            proc.terminate()
        return "已暂停"

    def resume(self):
        """继续播放"""
        if not self.current_url:
            return "没有播放记录"
        if not self.is_paused:
            return "已经在播放了"
        self.is_paused = False
        return self._start_mpg123()

    # --------------------------------------------------
    # 切歌
    # --------------------------------------------------
    def next(self, keyword=None):
        """下一首。指定关键词就播那首，否则从每日推荐队列播放"""
        if keyword:
            return self.play(keyword)
        if self.play_mode == "loop":
            return self.replay()
        # 默认 / shuffle 都走每日推荐队列
        return self._play_next_from_recommend()

    def prev(self):
        """上一首（历史回溯）"""
        if len(self.history) <= 1 or self.history_index <= 0:
            return "没有上一首了"
        self.history_index -= 1
        entry = self.history[self.history_index]
        self.stop()
        self.current_song = entry["song"]
        self.current_artist = entry["artist"]
        self.current_url = entry["url"]
        self.is_paused = False
        return self._start_mpg123()

    def replay(self):
        """重放当前歌曲"""
        if not self.current_url:
            return "没有播放记录"
        self.stop()
        self.is_paused = False
        return self._start_mpg123()

    # --------------------------------------------------
    # 音量
    # --------------------------------------------------
    def set_volume(self, level):
        """
        设置音量。控制 PipeWire 系统音量（影响所有声音输出）。
        支持格式：
          "大"/"大声点"/"音量大"       → +10%
          "小"/"小声点"/"音量小"       → -10%
          "最大声"                     → 100%
          "静音"                       → 0%
          "音量80"                     → 80%
          数字 (0.0~1.0)               → 直接设定
        """
        import subprocess
        if isinstance(level, str):
            if level in ("大", "大声点", "音量大"):
                self.volume = min(1.0, self.volume + 0.05)
            elif level in ("小", "小声点", "音量小"):
                self.volume = max(0.0, self.volume - 0.05)
            elif level == "最大声":
                self.volume = 1.0
            elif level == "静音":
                self.volume = 0.0
            elif level.startswith("音量") and level[2:].isdigit():
                self.volume = max(0.0, min(1.0, int(level[2:]) / 100.0))
            elif level.startswith("调到"):
                num_str = level[2:].strip()
                if num_str.isdigit():
                    self.volume = max(0.0, min(1.0, int(num_str) / 100.0))
                else:
                    return f"当前音量：{int(self.volume * 100)}%"
            elif level.isdigit():
                self.volume = max(0.0, min(1.0, int(level) / 100.0))
            else:
                return f"当前音量：{int(self.volume * 100)}%"
        else:
            self.volume = max(0.0, min(1.0, float(level)))

        # 同步设置 PipeWire 系统音量（影响所有音频输出，包括 TTS）
        pct = int(self.volume * 100)
        self._apply_pipewire_volume()






        print(f"  [音量] 音量={pct}%, cur={self.current_song}, proc={"ok" if self.process else "-"}"); return f"音量设为 {pct}%"

    def duck(self):
        """降低音量避免音乐干扰语音识别（不超过 40%，不高于当前音量）"""
        import subprocess, re
        try:
            sink = subprocess.run(["pactl", "get-default-sink"], capture_output=True, text=True, timeout=5).stdout.strip()
            if sink:
                info = subprocess.run(["pactl", "get-sink-volume", sink], capture_output=True, text=True, timeout=5).stdout
                m = re.search(r"(\d+)%", info)
                if m:
                    self._saved_volume = int(m.group(1))
                subprocess.run(["pactl", "set-sink-volume", sink, "10%"], capture_output=True, timeout=5)
                print(f"  [audio duck] volume 10%")
        except Exception:
            self._saved_volume = None
    


    def duck_tts(self):
        """TTS 播报时：降低音乐到 30%，播完恢复"""
        import subprocess
        try:
            sink = subprocess.run(["pactl", "get-default-sink"], capture_output=True, text=True, timeout=5).stdout.strip()
            if sink:
                info = subprocess.run(["pactl", "get-sink-volume", sink], capture_output=True, text=True, timeout=5).stdout
                m = re.search(r"(\d+)%", info)
                if m:
                    self._saved_volume = int(m.group(1))
                subprocess.run(["pactl", "set-sink-volume", sink, "30%"], capture_output=True, timeout=5)
                print(f"  [TTS duck] volume 30%")

        except Exception:
            self._saved_volume = None

    def restore(self):
        """录音后恢复原来音量"""
        import subprocess
        if self._saved_volume is not None:
            try:
                sink = subprocess.run(["pactl", "get-default-sink"], capture_output=True, text=True, timeout=5).stdout.strip()
                if sink:
                    subprocess.run(["pactl", "set-sink-volume", sink, f"{self._saved_volume}%"], capture_output=True, timeout=5)
                    print(f"  [audio duck] restore {self._saved_volume}%")
            except Exception:
                pass
            self._saved_volume = None
    


    # --------------------------------------------------
    # 信息查询
    # --------------------------------------------------
    def song_info(self):
        """当前播放的歌曲信息"""
        if not self.current_song:
            return "当前没有播放任何歌曲"
        status = "暂停" if self.is_paused else "播放"
        return f"正在{status}：{self.current_song} - {self.current_artist}"

    def artist_only(self):
        """谁唱的"""
        if not self.current_artist:
            return "不知道谁唱的"
        return f"这首歌是 {self.current_artist} 唱的"

    def status_query(self):
        """播放状态报告"""
        if not self.current_song:
            return "当前没有播放音乐"
        status = "暂停中" if self.is_paused else "播放中"
        mode_map = {"loop": "单曲循环", "shuffle": "随机播放", "order": "顺序播放"}
        mode = mode_map.get(self.play_mode, "顺序播放")
        return (
            f"当前{status}：{self.current_song} - {self.current_artist}，"
            f"{mode}，音量 {int(self.volume * 100)}%"
        )

    # --------------------------------------------------
    # 播放模式
    # --------------------------------------------------
    def set_play_mode(self, mode):
        """设置播放模式：loop / shuffle / order"""
        if mode in ("loop", "单曲循环"):
            self.play_mode = "loop"
            return "已设为单曲循环"
        elif mode in ("shuffle", "随机播放"):
            self.play_mode = "shuffle"
            return "已设为随机播放"
        else:
            self.play_mode = "order"
            return "已设为顺序播放"

    # --------------------------------------------------
    # 收藏
    # --------------------------------------------------
    def favorite(self):
        """收藏当前歌曲到网易云"""
        if not self.current_song:
            return "当前没有播放歌曲"
        if not self.netease:
            return "未连接音乐服务"
        # 需要先知道当前歌曲的 id，从 history 中找
        if self.history_index < 0 or self.history_index >= len(self.history):
            return "找不到当前歌曲信息"
        entry = self.history[self.history_index]
        # 从 netease 重新搜索获取 id
        songs = self.netease.search(entry["song"])
        if not songs:
            return "找不到歌曲信息"
        result = self.netease.like_song(songs[0]["id"])
        if result is True:
            return f"已收藏「{self.current_song}」"
        elif result is None:
            return "收藏需要先登录网易云账号"
        else:
            return "收藏失败"


if __name__ == "__main__":
    """自测：python3 music_player.py"""
    print("=" * 30)
    print("  音乐播放器自测")
    print("=" * 30)
    p = MusicPlayer()
    print(f"  ✅ 初始化成功（未连接网易云服务）")
    print(f"  音量+10%: {p.set_volume('大')}")
    print(f"  音量-10%: {p.set_volume('小')}")
    print(f"  最大声: {p.set_volume('最大声')}")
    print(f"  音量80: {p.set_volume('音量80')}")
    print(f"  静音: {p.set_volume('静音')}")
    print(f"  暂停: {p.pause()}")
    print(f"  继续: {p.resume()}")
    print(f"  状态: {p.status_query()}")
    print(f"  单曲循环: {p.set_play_mode('loop')}")
    print(f"  随机播放: {p.set_play_mode('shuffle')}")
    print(f"  顺序播放: {p.set_play_mode('order')}")