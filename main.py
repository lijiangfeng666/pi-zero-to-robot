"""
主程序 - Main
=============
唤醒词循环 + 指令处理。系统的入口。

工作流程：
  ① 循环监听 → 检测到声音 → 录音 → 百度 STT
  ② 识别到唤醒词（"土豆"）→ 播放提示音
  ③ 录音等待指令 → 百度 STT → DeepSeek 解析意图
  ④ 执行指令 → 播报结果 → 回到 ①

启动方式：
  cd ~/robot && python3 main.py
"""
import sys
import subprocess, re
import time
import signal
import config
import re

# --------------------------------------------------
# 各模块独立导入
# 一个模块出问题不影响其他模块的加载
# --------------------------------------------------
try:
    from voice import VoiceEngine
except Exception:
    VoiceEngine = None

try:
    from intent_parser import IntentParser
except Exception:
    IntentParser = None

try:
    from executor import Executor
except Exception:
    Executor = None

try:
    from alarm import AlarmScheduler
except Exception:
    AlarmScheduler = None

# 全局变量，用于优雅退出
running = True


def signal_handler(sig, frame):
    """Ctrl+C 优雅退出"""
    global running
    print("\n正在关闭机器人...")
    running = False


def _is_garbage(text):
    """判断是否环境噪音误识别，是则跳过不回复"""
    if not text:
        return True
    t = text.strip().rstrip("，。！？,.!?")
    _garbage = {"我","啊","嗯","哦","呀","哇","咦","唔","哈","哼","咯","喂","嘿",
                "我不知道","我想知道","我知道","我想听","我不知道啊","知道了",
                "不知道","我想","我知道啊","我知道啦","好啦","好","是","对",
                "嗯嗯","啊啊","哦哦","哈哈","好的","是的","对的","对呀",
                "干啥","干嘛","怎么了","怎么啦","什么","啥","哪个","哪個"}
    if t in _garbage or len(t) <= 1:
        return True
    return False

def _fix_asr_text(text):
    """修正百度 ASR 常见识别错误"""
    if not text:
        return text
    # 去掉末尾标点符号
    text = text.rstrip("，。,．.!！？?；;：: ")
    # 常见误识别修正（音乐场景）
    fixes = {
        "过": "歌",   # 播放春天的过 → 播放春天的歌
    }
    # 只修正"放X过"模式（动词+名词+过 → 歌）
    if text.endswith("过") and any(text.startswith(p) for p in ["放", "唱", "听", "点", "来一首", "来"]):
        text = text[:-1] + "歌"
    return text




def _find_wake_word(text):
    if not text:
        return -1
    idx = text.find(config.WAKE_WORD)
    if idx >= 0:
        return idx
    variants = ["图豆","土逗","吐豆","图斗","土头","呼叫土豆","呼喊土豆",
                 "兔都","土都","兔豆","图都","土躲","途豆","土到",
                 "土多","图多","土豆的","土dou","图dou","兔斗",
                 "大豆","大斗","大逗","大兜","大图","大吐","大兔",
                 "大豆瓣","大图都","大吐豆",
                 "一一","也有","都已","都斗","图斗","通通","通透","统统",
                 "都有","兜兜","都有豆","透豆","偷豆","投豆",
                 "土豆播放","土豆放","土播放","图播放","透播放","头播放"]
    for v in variants:
        idx = text.find(v)
        if idx >= 0:
            return idx
    return -1


def main():
    global running

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("=" * 40)
    print("  树莓派语音机器人 v2")
    print("  说「{}」唤醒我".format(config.WAKE_WORD))
    print("=" * 40)

    # --------------------------------------------------
    # 初始化所有模块
    # --------------------------------------------------
    print("\n[1/4] 初始化语音引擎...")
    if VoiceEngine is None:
        print("  ✗ voice.py 导入失败，检查文件完整性")
        sys.exit(1)
    try:
        voice = VoiceEngine()
        print("  语音引擎就绪")
    except Exception as e:
        print(f"  语音引擎初始化失败：{e}")
        print("  提示：检查 USB 麦克风是否已插入")
        sys.exit(1)

    print("[2/4] 初始化意图解析器...")
    if IntentParser is None:
        print("  ✗ intent_parser.py 导入失败，检查文件完整性")
        sys.exit(1)
    if not config.DEEPSEEK_KEY or "sk-" not in config.DEEPSEEK_KEY:
        print("  ⚠️  DEEPSEEK_KEY 未配置，请在 config.py 中填入")
        voice.text_to_speech("请先配置我的 API 密钥")
        sys.exit(1)
    parser = IntentParser()
    print("  意图解析器就绪")

    print("[3/4] 初始化执行器...")
    if Executor is None:
        print("  ✗ executor.py 导入失败，检查文件完整性")
        sys.exit(1)
    executor = Executor(voice=voice, parser=parser)
    print("  执行器就绪")

    print("[4/4] 初始化音乐模块（选装）...")
    music = None
    netease = None
    try:
        from netease import NetEaseClient
        from music_player import MusicPlayer

        netease = NetEaseClient()
        # 重试等待网易云 API 就绪（最多 30 秒）
        api_ready = False
        for i in range(15):
            if netease.check_health():
                api_ready = True
                break
            if i == 0:
                print("  等待网易云 API 就绪...")
            time.sleep(2)
        if api_ready:
            music = MusicPlayer(netease_client=netease)
            executor.music = music
            executor.netease = netease
            print("  音乐模块就绪")
        else:
            print("  音乐模块跳过（网易云 API 服务未运行）")
    except ImportError:
        print("  音乐模块跳过（未安装）")
    except Exception as e:
        print(f"  音乐模块跳过：{e}")

    # --------------------------------------------------
    # 闹钟模块初始化（依赖所有模块就绪后）
    # --------------------------------------------------
    alarm = None
    if AlarmScheduler is not None and music is not None:
        try:
            alarm = AlarmScheduler(voice=voice, music_player=music, netease_client=netease)
            alarm.start()
        except Exception as e:
            print(f"  闹钟模块跳过：{e}")

    print("\n" + "=" * 40)
    print("  说「{}」开始使用".format(config.WAKE_WORD))
    print("=" * 40 + "\n")

    # --------------------------------------------------
    # 主循环
    # --------------------------------------------------
    sleep_seconds = 0.3  # 每轮检测间隔
    last_vad_time = 0    # 上次触发 VAD 的时间戳
    vad_cooldown = 0.3     # VAD 触发后的冷却秒数，防背景噪音反复触发
    _last_music_record = 0   # 上次音乐中录音的时间戳，防频繁录音
    last_wake_time = 0   # 上次唤醒时间戳，用于免唤醒词窗口
    wake_window = 0     # 强制每次必须说唤醒词（避免背景噪音误触发）

    has_cmd = False
    while running:
        try:
            # 冷却期内跳过检测（音乐播放时冷却加倍，减少误触发）
            now = time.time()
            cooldown = vad_cooldown * 2 if (music and music.is_playing) else vad_cooldown
            if now - last_vad_time < cooldown:
                time.sleep(sleep_seconds)
                continue

            # 第1步：播放音乐时 → 独立关键词检测（5秒间隔，不与VAD交互）
            if music and music.is_playing:
                _now = time.time()
                if _now - _last_music_record >= 5.0:
                    _last_music_record = _now
                    _audio = voice.record_audio(duration=1.5)
                    if _audio:
                        _text = voice.speech_to_text(_audio)
                        if _text:
                            print(f"  [音乐检测]{_text}")
                            # 两步式歌词优先
                            if executor._pending_lyric:
                                executor._pending_lyric = None
                                _intent = {"intent": "search_lyric", "params": {}, "_original_text": _text}
                                _result = executor.execute(_intent)
                                if _result: print(f"  结果：{_result}")
                                continue
                            # 关键词检测
                            _kw_list = ["暂停","下一首","上一首","继续","停止","停止播放",
                                       "别唱了","停一下","别放了",
                                       "大声点","小声点","音量大","音量小","放大声","放小声",
                                       "单曲循环","随机播放","顺序播放","这是什么歌","谁唱的","怎么了"]
                            if any(k in _text for k in _kw_list):
                                print(f"  [音乐指令]{_text}")
                                # 音量命令：直接调PipeWire（不重启mpg123，不走DeepSeek）
                                if any(v in _text for v in ["大声点","音量大","放大声"]):
                                    music.volume = min(1.0, music.volume + 0.05)
                                    music._apply_pipewire_volume()
                                    continue
                                elif any(v in _text for v in ["小声点","音量小","放小声"]):
                                    music.volume = max(0.0, music.volume - 0.05)
                                    music._apply_pipewire_volume()
                                    continue
                                _exact = _text.strip().rstrip("，。！？")
                                _local_rules = {
                                    "暂停": {"intent": "pause", "params": {}, "reply": "已暂停"},
                                    "别唱了": {"intent": "pause", "params": {}, "reply": "已暂停"},
                                    "停止": {"intent": "stop", "params": {}, "reply": "已停止"},
                                    "停止播放": {"intent": "stop", "params": {}, "reply": "已停止"},
                                }
                                if _exact in _local_rules:
                                    _intent = _local_rules[_exact]
                                else:
                                    _intent = parser.parse(_text)
                                _intent["_original_text"] = _text
                                executor.execute(_intent)
                                continue
                time.sleep(sleep_seconds)
                continue  # ← 跳过后续VAD门控，不走非音乐流程

            # VAD门控：音乐播放时阈值5000（避免音乐误触发），安静时2500
            vad_th = 5000 if (music and music.is_playing) else 2500
            # 使用listen_and_record：环状缓冲区保留触发前400ms音频，不丢首字
            audio, detected = voice.listen_and_record(
                duration=config.WAKE_RECORD_SECONDS,
                timeout=4,
                threshold_override=vad_th
            )
            if not detected or not audio:
                time.sleep(sleep_seconds)
                continue

            last_vad_time = time.time()

            # 音乐播放时加录音冷却（2秒），防频繁触发导致音频卡顿
            if music and music.is_playing:
                if time.time() - _last_music_record < 2.0:
                    time.sleep(sleep_seconds)
                    continue
                _last_music_record = time.time()

            last_vad_time = time.time()
            text = voice.speech_to_text(audio)

            if not text:
                time.sleep(sleep_seconds)
                continue

            print(f"  听到：{text}")

            # 第3步：检查是否包含唤醒词（含模糊匹配）
            idx = _find_wake_word(text)
            now = time.time()
            # 音乐播放时禁用免唤醒词窗口，必须说"土豆"
            in_window = (now - last_wake_time) < wake_window and not (music and music.is_playing)

            if idx < 0 and not in_window:
                # 未检测到唤醒词时，检查是否包含已知命令关键词（弥补ASR句首丢字）
                cmd_keywords = ["三国演义","作业","做业","作页","左叶","坐夜",
                             "番茄","天气","放歌","播放","暂停","下一首","上一首","继续","有一句","歌词","歌词搜歌","搜歌","搜歌曲","搜歌词"]
                has_cmd = any(k in text for k in cmd_keywords)
                if has_cmd or executor._pending_lyric:
                    print(f"  [关键词指令]{text}")
                    if executor._pending_lyric:
                        executor._pending_lyric = None
                        print(f"  [pending歌词执行]{text}")
                        # 两步式歌词：绕过DeepSeek，直接搜歌词
                        intent = {"intent": "search_lyric", "params": {}, "_original_text": text}
                        result = executor.execute(intent)
                        if result:
                            print(f"  结果：{result}")
                        # 继续下一个循环
                        time.sleep(sleep_seconds)
                        continue
                    need_cmd = False
                    cmd_text = text
                    last_wake_time = time.time()
                    print(f"  直接执行：{cmd_text}")
                else:
                    # 音乐播放时如果 VAD 频繁触发（音乐底噪），跳过本次
                    if idx < 0 and music and music.is_playing:
                        print(f"  [音乐底噪跳过]{text}")
                    else:
                        print(f"  [非唤醒]{text}")
                    continue

            # 唤醒或窗口期内 → 获取指令文本
            elif idx >= 0:
                last_wake_time = time.time()
                print(f"  唤醒！({config.WAKE_WORD})")
                # 联合指令（"土豆播放大海" 一步到位")
                cmd_from_wake = text[idx + len(config.WAKE_WORD):].strip()
                if cmd_from_wake and not all(c in "，。,．.!！？?；;：:" for c in cmd_from_wake):
                    cmd_text = cmd_from_wake
                    print(f"  联合指令：{cmd_text}")
                    need_cmd = False
                else:
                    # 如果唤醒词在句尾且其后无有效指令，取唤醒词前的文本
                    before_wake = text[:idx].strip()
                    if before_wake and len(cmd_from_wake) <= 2:
                        cmd_text = before_wake
                        print(f"  前置指令：{cmd_text}")
                        need_cmd = False
                    else:
                        need_cmd = True
            else:
                # 免唤醒词窗口内
                last_wake_time = time.time()
                print(f"  [续对话]{text}")
                cmd_text = text
                need_cmd = False

            if need_cmd:
                # 先 duck 再播 TTS（播完恢复），录音时再 duck 一次确保干净
                if music and music.is_playing:
                    music.duck()
                voice.text_to_speech("主人，在呢")
                if music and music.is_playing:
                    music.restore()
                time.sleep(1.0)  # 等自己的TTS播完再听，防回授
                # 第4步：等待指令（一体化VAD+录音，环状缓冲防吞首字）
                cmd_text = None
                for retry in range(3):
                    cmd_audio = voice.record_audio()
                    if not cmd_audio:
                        if retry < 2:
                            continue
                        break
                    cmd_text = voice.speech_to_text(cmd_audio)
                    if cmd_text:
                        break
                if not cmd_text:
                    continue
                if _is_garbage(cmd_text):
                    print(f"  [环境噪音跳过]{cmd_text}")
                    continue
                print(f"  指令：{cmd_text}")

            # 第5步：过滤垃圾指令 + 修正 ASR 识别错误
            if _is_garbage(cmd_text):
                print(f"  [垃圾指令跳过]{cmd_text}")
                if 'need_cmd' in dir() and need_cmd:
                    continue
                else:
                    # 联合指令带垃圾（"土豆啊"），退化为纯唤醒
                    print("  退化到纯唤醒")
                    need_cmd = True
                    if music and music.is_playing:
                        music.duck()
                    voice.text_to_speech("主人，在呢")
                    if music and music.is_playing:
                        music.restore()
                    time.sleep(1.0)
                    continue
            cmd_text = _fix_asr_text(cmd_text)

            # 本地规则映射（跳过DeepSeek，防"暂停"→stop等误解析）
            _rule_map = {
                "暂停": {"intent": "pause", "params": {}, "reply": "已暂停"},
                "别唱了": {"intent": "pause", "params": {}, "reply": "已暂停"},
                "停止": {"intent": "stop", "params": {}, "reply": "已停止"},
                "停止播放": {"intent": "stop", "params": {}, "reply": "已停止"},
            }
            _exact = cmd_text.strip().rstrip("，。！？")
            if _exact in _rule_map:
                intent = _rule_map[_exact]
                print(f"  [本地规则]{_exact} → {intent['intent']}")
            else:
                intent = parser.parse(cmd_text)
            intent["_original_text"] = cmd_text
            print(f"  意图：{intent.get('intent')}")

            # 第6步：执行
            result = executor.execute(intent)
            if result:
                if intent.get("intent") == "chat" and len(cmd_text.strip()) <= 4:
                    result = None
                if result:
                    print(f"  结果：{result}")



            # TTS播放后冷却，避免自己的说话声被麦克风捕到形成反馈环
            time.sleep(1.5)  # 等TTS播完
            last_wake_time = time.time()  # 执行完后重置唤醒窗口
            # pending歌词搜索时不用等，下一轮录音会自动用文本内容搜
            has_cmd = False

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"  [主循环错误] {e}")
            time.sleep(2)

    # --------------------------------------------------
    # 清理退出
    # --------------------------------------------------
    print("\n清理资源...")
    if music:
        music.stop()
    voice.cleanup()
    print("机器人已关闭。再见！")


if __name__ == "__main__":
    main()