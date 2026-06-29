"""

指令执行器 - Executor

======================
        self.parser = parser

根据 IntentParser 解析出的意图，调用对应模块执行。



交互规则见：Obsidian → 12 - 交互规则

"""

import os

# weather 模块在 _do_weather_query 中按需导入，不影响其他功能





class Executor:

    """指令执行器：把意图变成动作"""



    def __init__(self, voice=None, music=None, netease=None, parser=None):

        self.voice = voice
        self._pending_lyric = None  # 两句式歌词搜索：先存再搜
        self.parser = parser

        self.music = music

        self.netease = netease

    def _tts(self, text):
        """播报 TTS（播报时音乐降到30%，播完恢复）"""
        need_restore = False
        if hasattr(self, "music") and self.music and self.music.is_playing:
            self.music.duck_tts()
            need_restore = True
        self.voice.text_to_speech(text)
        if need_restore:
            self.music.restore()



    def execute(self, intent):

        """

        执行一条意图。

        intent: IntentParser.parse() 返回的字典

        返回：要播报给用户的回复文字

        """

        intent_type = intent.get("intent", "chat")

        params = intent.get("params", {})

        reply = intent.get("reply", "")



        # 先播报简短回应（如果有）

        if reply and self.voice:
            self._tts(reply)



        # 根据意图类型执行

        handler = getattr(self, f"_do_{intent_type}", self._do_chat)

        result = handler(intent, params)



        # 播报执行结果

        if result and self.voice:
            self._tts(result)



        return result



    # --------------------------------------------------

    # 点歌

    # --------------------------------------------------

    def _do_play_music(self, intent, params):

        """播放指定歌曲"""

        keyword = params.get("keyword", "")

        if not keyword or len(keyword) < 2:

            return "你想听什么歌？"

        if not self.music:

            return "音乐模块没装"

        return self.music.play(keyword)

    def _do_search_lyric(self, intent, params):
        """歌词搜索"""
        if not self.music or not self.netease:
            return "音乐模块没装"
        keyword = intent.get("_original_text", "")
        for prefix in ["搜歌词", "歌词搜歌", "有一句歌词", "有一句", "歌曲的歌词", "歌词是", "搜歌曲", "搜歌", "歌词"]:
            keyword = keyword.replace(prefix, "").strip()
        keyword = keyword.strip("。，！？、")
        keyword = keyword.strip("。，！？、.,!?")
        if not keyword or len(keyword) < 2:
            self._pending_lyric = True
            return "请说出歌词片段"
        print(f"  歌词搜索: {keyword}")
        songs = self.netease.search_by_lyric(keyword)
        if not songs:
            return f"没找到包含「{keyword}」的歌曲"
        song = songs[0]
        name = song.get("name", "未知")
        artist = song.get("artists", [{}])[0].get("name", "未知")
        print(f"  匹配到: {name} - {artist}")
        return self.music.play(name)

    def _do_random_play(self, intent, params):

        """随机放歌"""

        if not self.music:

            return "音乐模块没装"

        return self.music.next()



    # --------------------------------------------------

    # 播放控制

    # --------------------------------------------------

    def _do_next_song(self, intent, params):

        """下一首"""

        if not self.music:

            return "没在放歌"

        keyword = params.get("keyword", "")

        return self.music.next(keyword if keyword else None)



    def _do_prev_song(self, intent, params):

        """上一首"""

        if not self.music:

            return "没在放歌"

        return self.music.prev()



    def _do_pause(self, intent, params):

        """暂停"""

        if not self.music:

            return "没在放歌"

        result = self.music.pause()
        return result



    def _do_resume(self, intent, params):

        """继续播放"""

        if not self.music:

            return "没在放歌"

        return self.music.resume()



    def _do_replay(self, intent, params):

        """重放"""

        if not self.music:

            return "没在放歌"

        return self.music.replay()



    def _do_stop(self, intent, params):

        """停止播放"""

        if not self.music:

            return "没在放歌"

        self.music.stop()

        return "已停止播放"



    # --------------------------------------------------

    # 音量

    # --------------------------------------------------

    def _do_volume_up(self, intent, params):

        """调大音量"""

        if self.music:

            return self.music.set_volume("大")

        import subprocess
        try:
            sink = subprocess.run(["pactl", "get-default-sink"], capture_output=True, text=True, timeout=5).stdout.strip()
            if sink:
                subprocess.run(["pactl", "set-sink-volume", sink, "+10%"], capture_output=True, timeout=5)
                subprocess.run(["pactl", "set-sink-mute", sink, "0"], capture_output=True, timeout=5)
        except Exception:
            pass
        return "音量已调大"



    def _do_volume_down(self, intent, params):

        """调小音量"""

        if self.music:

            return self.music.set_volume("小")

        import subprocess
        try:
            sink = subprocess.run(["pactl", "get-default-sink"], capture_output=True, text=True, timeout=5).stdout.strip()
            if sink:
                subprocess.run(["pactl", "set-sink-volume", sink, "-10%"], capture_output=True, timeout=5)
        except Exception:
            pass
        return "音量已调小"



    def _do_volume_set(self, intent, params):

        """设定具体音量"""

        if self.music:

            level = params.get("level", "")

            return self.music.set_volume(level)

        import subprocess
        try:
            sink = subprocess.run(["pactl", "get-default-sink"], capture_output=True, text=True, timeout=5).stdout.strip()
            if sink:
                level_str = params.get("level", "")
                if "最大声" in level_str:
                    subprocess.run(["pactl", "set-sink-volume", sink, "100%"], capture_output=True, timeout=5)
                elif "静音" in level_str:
                    subprocess.run(["pactl", "set-sink-mute", sink, "1"], capture_output=True, timeout=5)
                elif "音量" in level_str:
                    try:
                        pct = level_str.replace("音量", "").strip()
                        subprocess.run(["pactl", "set-sink-volume", sink, f"{pct}%"], capture_output=True, timeout=5)
                    except Exception:
                        pass
                elif "调到" in level_str:
                    try:
                        pct = level_str.replace("调到", "").strip()
                        subprocess.run(["pactl", "set-sink-volume", sink, f"{pct}%"], capture_output=True, timeout=5)
                    except Exception:
                        pass
                subprocess.run(["pactl", "set-sink-mute", sink, "0"], capture_output=True, timeout=5)
        except Exception:
            pass
        return "音量已调整"



    # --------------------------------------------------

    # 信息查询

    # --------------------------------------------------

    def _do_song_info(self, intent, params):

        """当前播放的歌曲信息"""

        if not self.music:

            return "没在放歌"

        return self.music.song_info()



    def _do_current_artist(self, intent, params):

        """谁唱的"""

        if not self.music:

            return "没在放歌"

        return self.music.artist_only()



    def _do_status_query(self, intent, params):

        """播放状态"""

        if not self.music:

            return "没在放歌"

        return self.music.status_query()



    # --------------------------------------------------

    # 播放模式

    # --------------------------------------------------

    def _do_loop_mode(self, intent, params):

        """单曲循环"""

        if not self.music:

            return "没在放歌"

        return self.music.set_play_mode("loop")



    def _do_shuffle_mode(self, intent, params):

        """随机播放"""

        if not self.music:

            return "没在放歌"

        return self.music.set_play_mode("shuffle")



    def _do_order_mode(self, intent, params):

        """顺序播放"""

        if not self.music:

            return "没在放歌"

        return self.music.set_play_mode("order")



    # --------------------------------------------------

    # 收藏

    # --------------------------------------------------

    def _do_favorite(self, intent, params):

        """收藏"""

        if not self.music:

            return "没在放歌"

        return self.music.favorite()



    # --------------------------------------------------

    # 天气

    # --------------------------------------------------

    def _do_weather_query(self, intent, params):
        """直接查天气，播报结果含城市+日期供用户校验"""
        import weather as weather_module
        import re as _re

        city = params.get("city", "")
        period = params.get("period", "今天")
        print(f"  [Weather] 查询城市={city}, 时段={period}")

        cities = _re.split(r"[和、]", city)
        cities = [c.strip() for c in cities if c.strip()]
        if cities:
            texts = []
            for c in cities:
                r = weather_module.query_weather(c, period)
                if r and r.get("success"):
                    texts.append(r["text"])
                else:
                    texts.append(f"{c}暂时查不到")
            result_text = "，".join(texts)
        else:
            r = weather_module.query_weather(city, period)
            result_text = r.get("text", str(r)) if isinstance(r, dict) else str(r)

        if result_text and self.voice:
            self.voice.text_to_speech(result_text)
            print(f"  [Weather] TTS已播报: {result_text[:50]}...")
        return None


    def _do_start_pomodoro(self, intent, params):
        """开启番茄钟"""
        import subprocess
        try:
            script = os.path.expanduser("~/robot/pomodoro.py")
            subprocess.Popen(["python3", script],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "番茄钟已开启"
        except Exception as e:
            return f"启动番茄钟失败: {e}"

    def _do_stop_pomodoro(self, intent, params):
        """关闭番茄钟"""
        import subprocess, signal
        try:
            pid_file = os.path.expanduser("~/robot/pomodoro.pid")
            lock_file = os.path.expanduser("~/robot/pomodoro.lock")
            if os.path.exists(pid_file):
                with open(pid_file) as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                os.unlink(pid_file)
            if os.path.exists(lock_file):
                os.unlink(lock_file)
            # 也杀其他python3 pomodoro进程
            r = subprocess.run(["pkill", "-f", "pomodoro.py"],
                               capture_output=True)
            return "番茄钟已关闭"
        except Exception as e:
            return f"关闭番茄钟失败: {e}"

    def _do_play_sanguo(self, intent, params):
        """播放三国演义（无集数，默认第一集）"""
        if not self.netease:
            return "网易云没连上"
        url, name = self.netease.get_dj_program_url(966569869, 1)
        if not url:
            return "获取三国演义失败"
        print(f"  三国演义: {name}")
        if self.music:
            self._tts(f"播放{name}")
            self.music.play_url(name, url)
        return "" 

    def _do_play_sanguo_chapter(self, intent, params):
        """播放指定集数的三国演义"""
        chapter = params.get("chapter", 0)
        try:
            chapter = int(chapter)
        except (ValueError, TypeError):
            chapter = 0
        if chapter < 1 or chapter > 492:
            return f"请输入1到492之间的集数"
        if not self.netease:
            return "网易云没连上"
        url, name = self.netease.get_dj_program_url(966569869, chapter)
        if not url:
            return f"获取第{chapter}集失败"
        print(f"  三国演义: {name}")
        if self.music:
            self._tts(f"播放{name}")
            self.music.play_url(name, url)
        return f"正在播放{name}" 

    def _do_read_homework(self, intent, params):
        """播报今日作业"""
        path = os.path.expanduser("~/robot/每日作业播报/homework.txt")
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read().strip()
            if not text:
                return "还没有记录作业内容"
            print(f"  播报作业: {text[:60]}...")
            self._tts(text)
            return "作业已播报"
        except FileNotFoundError:
            return "还没有记录作业内容"
        except Exception as e:
            return f"读取作业失败: {e}"

    def _do_chat(self, intent, params):
        """聊天：没有parser或没有文本时安静跳过，不调用API"""
        if not self.parser:
            return ""
        text = intent.get("_original_text", "")
        if not text or not text.strip():
            return ""
        return self.parser.chat(text)





if __name__ == "__main__":

    """自测：python3 executor.py"""

    import sys

    print("=" * 30)

    print("  执行器自测")

    print("=" * 30)

    e = Executor()

    # 测试不依赖外部模块的意图

