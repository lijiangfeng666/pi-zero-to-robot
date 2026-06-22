"""
语音模块 - VoiceEngine
======================
功能：录音（麦克风） + 播放（音响） + 百度 STT/TTS

核心变更：常开流模式
- 不再每次 VAD/录音都开/关 PyAudio 流
- 初始化时打开一次输入流，持续复用
- 流异常时自动重连
"""
import io
import os
import wave
import json
import time
import tempfile
import math
import struct
import pyaudio
from aip import AipSpeech


class VoiceEngine:
    """语音引擎：录音 → 百度识别 → 文字 / 文字 → 百度合成 → 播放"""

    def __init__(self):
        import config
        self.client = AipSpeech(
            config.BAIDU_APP_ID,
            config.BAIDU_API_KEY,
            config.BAIDU_SECRET_KEY,
        )
        self.pa = pyaudio.PyAudio()
        self.mic_index = self._resolve_mic_index(config.MIC_INDEX)
        self.sample_rate = 16000
        self._record_seconds = config.RECORD_SECONDS
        self._vad_threshold = config.VAD_THRESHOLD
        self._vad_chunk_ms = 200
        self._init_mic_gain()

        # 常开输入流：初始化时打开一次，持续复用
        # 录音和 VAD 都从这个流读取
        self._input_stream = None
        self._open_persistent_stream()

    def _open_persistent_stream(self):
        """打开持久输入流（初始化时和异常重连时调用）"""
        self._close_persistent_stream()
        try:
            stream = self.pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.mic_index,
                frames_per_buffer=1024,
                start=False,
            )
            stream.start_stream()
            self._input_stream = stream
            return True
        except OSError as e:
            print(f"  [Audio] 打开麦克风流失败: {e}")
            self._input_stream = None
            return False
        except Exception as e:
            print(f"  [Audio] 打开麦克风流异常: {e}")
            self._input_stream = None
            return False

    def _close_persistent_stream(self):
        """关闭持久输入流"""
        if self._input_stream is not None:
            try:
                self._input_stream.stop_stream()
                self._input_stream.close()
            except Exception:
                pass
            self._input_stream = None

    def _ensure_stream(self):
        """确保持久流可用，不可用时尝试重连"""
        if self._input_stream is not None:
            return True
        print("  [Audio] 流已断开，尝试重连...")
        return self._open_persistent_stream()

    # --------------------------------------------------
    # 麦克风检测
    # --------------------------------------------------
    def _resolve_mic_index(self, preferred=-1):
        """按优先级查找可用的麦克风设备"""
        if preferred >= 0:
            return preferred
        name_keywords = ["WebCamera", "USB Camera", "USB Audio"]
        for kw in name_keywords:
            for i in range(self.pa.get_device_count()):
                info = self.pa.get_device_info_by_index(i)
                if info["maxInputChannels"] > 0 and kw in info["name"]:
                    print(f"  麦克风: [{i}] {info['name']}")
                    return i
        for i in range(self.pa.get_device_count()):
            info = self.pa.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0 and "pulse" in info["name"].lower():
                print(f"  麦克风: [{i}] {info['name']} (pulse)")
                return i
        for i in range(self.pa.get_device_count()):
            info = self.pa.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0:
                print(f"  麦克风: [{i}] {info['name']} (fallback)")
                return i
        raise RuntimeError("找不到可用的麦克风！")

    def _init_mic_gain(self):
        """设置 USB 麦克风增益（重启后失效，需每次初始化时设置）"""
        try:
            import config as cfg
            import subprocess
            gain = getattr(cfg, "MIC_GAIN", "4000")
            subprocess.run(
                ["amixer", "-c", "3", "cset", "numid=3", gain],
                capture_output=True, timeout=5,
            )
        except Exception:
            pass

    def list_mics(self):
        print("可用的麦克风设备：")
        for i in range(self.pa.get_device_count()):
            info = self.pa.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0:
                print(f"  [{i}] {info['name']}")

    # --------------------------------------------------
    # 录音（从持久流读取）
    # --------------------------------------------------
    def record_audio(self, duration=None):
        """从持久流录音，返回 WAV 格式的二进制数据。"""
        if not self._ensure_stream():
            return b""

        if duration is None:
            duration = self._record_seconds

        frames = []
        chunks = int(self.sample_rate / 1024 * duration)
        for _ in range(chunks):
            try:
                data = self._input_stream.read(1024, exception_on_overflow=False)
                frames.append(data)
            except OSError:
                print("  [Audio] 录音读取出错，尝试重连...")
                self._close_persistent_stream()
                return b""
            except Exception:
                self._close_persistent_stream()
                return b""

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(b"".join(frames))
        return buf.getvalue()

    # --------------------------------------------------
    # 语音活动检测（从持久流读取）
    # --------------------------------------------------

    def listen_and_record(self, duration=None, timeout=4, threshold_override=None):
        """
        一体化监听+录音：从持久流持续读取，检测到说话后继续录满duration。
        使用环状缓冲区保留说话前400ms音频，保证语音开头不被吞。
        返回 (wav_bytes, detected)
        """
        if not self._ensure_stream():
            return b"", False

        if duration is None:
            duration = self._record_seconds

        chunk_size = int(self.sample_rate * self._vad_chunk_ms / 1000)
        threshold = threshold_override if threshold_override else self._vad_threshold

        preroll_chunks = 2
        ring_buffer = []
        frames = []
        speaking = False
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                data = self._input_stream.read(chunk_size, exception_on_overflow=False)
            except OSError:
                print("  [Audio] VAD 读取出错，尝试重连...")
                self._close_persistent_stream()
                return b"", False

            samples = struct.unpack("<{}h".format(len(data) // 2), data)
            sum_sq = sum(s * s for s in samples)
            rms = int(math.sqrt(sum_sq / len(samples)))

            if rms > threshold:
                if not speaking:
                    print(f"  [VAD] RMS={rms} > {threshold} -> SPEECH DETECTED")
                    frames = list(ring_buffer)
                    speaking = True
                frames.append(data)
            else:
                if speaking:
                    frames.append(data)
                    if len(frames) * chunk_size / self.sample_rate >= duration:
                        break
                else:
                    ring_buffer.append(data)
                    if len(ring_buffer) > preroll_chunks:
                        ring_buffer.pop(0)

        if not speaking:
            return b"", False

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(b"".join(frames))
        return buf.getvalue(), True

    def voice_detected(self, threshold_override=None):
        """
        检测是否有人说话。
        从持久流读取一段短音频，计算 RMS，超过阈值返回 True。
        """
        if not self._ensure_stream():
            return False

        chunk_size = int(self.sample_rate * self._vad_chunk_ms / 1000)

        try:
            data = self._input_stream.read(chunk_size, exception_on_overflow=False)
        except OSError:
            print("  [Audio] VAD 读取出错，尝试重连...")
            self._close_persistent_stream()
            return False

        samples = struct.unpack("<{}h".format(len(data) // 2), data)
        sum_sq = sum(s * s for s in samples)
        rms = int(math.sqrt(sum_sq / len(samples)))
        threshold = threshold_override if threshold_override else self._vad_threshold

        if rms > threshold:
            print(f"  [VAD] RMS={rms} > {threshold} -> WAKE")
        else:
            print(f"  [VAD] RMS={rms} <= {threshold} -> sleep")
        return rms > threshold

    # --------------------------------------------------
    # 语音 → 文字（百度 STT）
    # --------------------------------------------------
    def speech_to_text(self, audio_data):
        if not audio_data:
            return None
        for attempt in range(3):
            try:
                result = self.client.asr(
                    audio_data, "wav", self.sample_rate, {"dev_pid": 1537}
                )
                if result.get("err_no") == 0:
                    return result["result"][0]
                if result.get("err_no") in (3301, 3302):
                    return None
            except Exception as e:
                if attempt < 2:
                    continue
                print(f"  [STT 错误] {e}")
                return None
        return None

    # --------------------------------------------------
    # 文字 → 语音（百度 TTS）
    # --------------------------------------------------
    def text_to_speech(self, text, **overrides):
        if not text:
            return
        if len(text) > 500:
            for i in range(0, len(text), 500):
                self._speak_segment(text[i : i + 500], overrides)
        else:
            self._speak_segment(text, overrides)

    def _speak_segment(self, text, overrides=None):
        try:
            params = {"vol": 15, "spd": 5, "pit": 5, "per": 0}
            if overrides:
                params.update(overrides)
            result = self.client.synthesis(text, "zh", 1, params)
        except Exception as e:
            print(f"  [TTS 错误] {e}")
            return

        if isinstance(result, dict):
            print(f"  [TTS 失败] {result.get('err_msg', result)}")
            return

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(result)
            tmp_path = f.name

        os.system(f"mpg123 -q {tmp_path} 2>/dev/null")
        os.unlink(tmp_path)

    # --------------------------------------------------
    # 提示音（唤醒反馈）
    # --------------------------------------------------
    def play_beep(self):
        try:
            import numpy as np

            rate = 48000
            duration = 0.15
            t = np.linspace(0, duration, int(rate * duration), False)
            tone = np.sin(2 * np.pi * 880 * t) * 0.3
            audio = (tone * 32767).astype(np.int16).tobytes()

            stream = self.pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=rate,
                output=True,
            )
            stream.write(audio)
            stream.stop_stream()
            stream.close()
        except Exception:
            pass

    # --------------------------------------------------
    # 释放资源
    # --------------------------------------------------
    def cleanup(self):
        self._close_persistent_stream()
        try:
            self.pa.terminate()
        except Exception:
            pass


if __name__ == "__main__":
    """自测：python3 voice.py"""
    import sys
    print("=" * 30)
    print("  语音引擎自测")
    print("=" * 30)
    try:
        v = VoiceEngine()
        v.list_mics()
        print(f"  当前使用麦克风索引: {v.mic_index}")
        print("  ✅ 语音引擎初始化成功")
    except Exception as e:
        print(f"  ❌ 语音引擎初始化失败: {e}")
        print("  提示：检查 USB 麦克风是否已插入")
        sys.exit(1)
