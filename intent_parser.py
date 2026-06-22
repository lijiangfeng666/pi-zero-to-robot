"""
意图解析器 - IntentParser
=========================
使用 DeepSeek 理解用户指令，提取意图和参数。

支持的意图类型：
  - play_music:   用户点歌，说出歌名或歌手名
  - random_play:  用户只说放歌/唱歌，没指定歌名
  - pause:        用户想暂停播放
  - resume:       用户想继续播放
  - next_song:    用户想切歌/下一首
  - prev_song:    用户想听上一首
  - replay:       用户想重放当前歌曲
  - volume_up:    用户想调大音量
  - volume_down:  用户想调小音量
  - volume_set:   用户指定具体音量（如"音量80"、"最大声"、"静音"）
  - song_info:    用户问正在放什么歌
  - current_artist: 用户问谁唱的
  - status_query: 用户问播放状态（怎么了/什么情况）
  - favorite:     用户想收藏当前歌曲
  - loop_mode:    用户想单曲循环
  - shuffle_mode: 用户想随机播放
  - order_mode:   用户想顺序播放
  - stop:         用户想停止播放
  - weather_query: "北京天气"、"明天会下雨吗"
  - chat:          "今天心情怎么样"、"你是谁"
  - unknown:       无法识别的指令
"""
import json
import requests

# 提供给 DeepSeek 的系统提示词
SYSTEM_PROMPT = """你是一个语音助手意图分析器。分析用户指令，返回 JSON 格式的意图。

## 意图列表
- play_music: 用户点歌，说出歌名或歌手名
- random_play: 用户只说放歌/唱歌，没指定歌名
- search_lyric: 用户想按歌词搜歌（含有歌词/歌词是等关键词）
- pause: 用户想暂停播放
- resume: 用户想继续播放
- next_song: 用户想切歌/下一首
- prev_song: 用户想听上一首
- replay: 用户想重放当前歌曲
- volume_up: 用户想调大音量
- volume_down: 用户想调小音量
- volume_set: 用户指定具体音量（如"音量80"、"最大声"、"静音"）
- song_info: 用户问正在放什么歌
- current_artist: 用户问谁唱的
- status_query: 用户问播放状态（怎么了/什么情况）
- favorite: 用户想收藏当前歌曲
- loop_mode: 用户想单曲循环
- shuffle_mode: 用户想随机播放
- order_mode: 用户想顺序播放
- stop: 用户想停止播放
- weather_query: 用户想查天气，包含城市名和时间
- chat: 用户想聊天、打招呼、问问题

## 返回格式
只返回 JSON，不要其他文字。
{
  "intent": "意图名称",
  "params": {
    "keyword": "歌曲名或歌手名（如果是play_music）",
    "city": "城市名（如果是weather_query）",
    "period": "今天/明天/后天/X号/X月X号/一周/未来一周（如果是weather_query）",
    "level": "大"/"小"/"最大声"/"静音"/"音量80"（如果是volume_set/volume_up/volume_down）
  },
  "reply": "你对用户的简短回应，自然口语化"
}

## 示例
用户：播放大海
{"intent": "play_music", "params": {"keyword": "大海"}, "reply": "好嘞，放一首大海"}

用户：放歌
{"intent": "random_play", "params": {}, "reply": "来点音乐"}

用户：歌词搜歌
{"intent": "search_lyric", "params": {}, "reply": "搜一下歌词"}

用户：搜歌
{"intent": "search_lyric", "params": {}, "reply": "搜一下歌词"}

用户：搜歌曲
{"intent": "search_lyric", "params": {}, "reply": "搜一下歌词"}

用户：有一句歌词后来
{"intent": "search_lyric", "params": {}, "reply": "搜一下歌词"}

用户：歌词是后来
{"intent": "search_lyric", "params": {}, "reply": "搜一下歌词"}

用户：歌曲的歌词后来
{"intent": "search_lyric", "params": {}, "reply": "搜一下歌词"}


用户：找点时间，找点空闲
{"intent": "play_music", "params": {"keyword": "常回家看看"}, "reply": "常回家看看，走起"}

用户：后来我总算学会了如何去爱
{"intent": "play_music", "params": {"keyword": "后来"}, "reply": "刘若英的后来，安排"}

用户：无关风月我题序等你回
{"intent": "play_music", "params": {"keyword": "兰亭序"}, "reply": "周杰伦的兰亭序"}

# 规则：用户给歌词能确定是哪首歌就返回play_music，不确定就返回chat说不知道这段歌词
用户：下一首
{"intent": "next_song", "params": {}, "reply": "换一首"}

用户：上一首
{"intent": "prev_song", "params": {}, "reply": "回到上一首"}

用户：暂停
{"intent": "pause", "params": {}, "reply": "已暂停"}

用户：别唱了
{"intent": "pause", "params": {}, "reply": "已暂停"}

用户：继续
{"intent": "resume", "params": {}, "reply": "继续播放"}

用户：大声点
{"intent": "volume_up", "params": {}, "reply": "调大音量"}

用户：小声点
{"intent": "volume_down", "params": {}, "reply": "调小音量"}

用户：音量小
{"intent": "volume_down", "params": {"level": "小"}, "reply": "调小音量"}

用户：放小声
{"intent": "volume_down", "params": {}, "reply": "调小音量"}

用户：音量80
{"intent": "volume_set", "params": {"level": "音量80"}, "reply": "好的"}

用户：调到50
{"intent": "volume_set", "params": {"level": "调到50"}, "reply": "好的"}

用户：最大声
{"intent": "volume_set", "params": {"level": "最大声"}, "reply": "最大音量"}

用户：这是什么歌
{"intent": "song_info", "params": {}, "reply": "我看一下"}

用户：谁唱的
{"intent": "current_artist", "params": {}, "reply": "查一下"}

用户：重放
{"intent": "replay", "params": {}, "reply": "放一遍"}

用户：收藏
{"intent": "favorite", "params": {}, "reply": "已收藏"}

用户：单曲循环
{"intent": "loop_mode", "params": {}, "reply": "设为单曲循环"}

用户：随机播放
{"intent": "shuffle_mode", "params": {}, "reply": "随机播放"}

用户：怎么了
{"intent": "status_query", "params": {}, "reply": "我看一下"}

用户：别放了
{"intent": "stop", "params": {}, "reply": "已停止"}

用户：停止
{"intent": "stop", "params": {}, "reply": "已停止"}

用户：停止播放
{"intent": "stop", "params": {}, "reply": "已停止"}

用户：北京明天天气
{"intent": "weather_query", "params": {"city": "北京", "period": "明天"}, "reply": "我查一下北京的天气"}

用户：上海和北京的天气
{"intent": "weather_query", "params": {"city": "上海和北京", "period": "今天"}, "reply": "我查一下上海和北京的天气"}

用户：甘谷县今天天气
{"intent": "weather_query", "params": {"city": "甘谷县", "period": "今天"}, "reply": "查一下甘谷的天气"}

用户：查天气
{"intent": "weather_query", "params": {"city": "", "period": "今天"}, "reply": "查一下天气"}

用户：天气预报
{"intent": "weather_query", "params": {"city": "", "period": "今天"}, "reply": "查一下天气"}

用户：明天天气怎么样
{"intent": "weather_query", "params": {"city": "", "period": "明天"}, "reply": "查一下明天的天气"}

用户：深圳未来一周天气
{"intent": "weather_query", "params": {"city": "深圳", "period": "未来一周"}, "reply": "查一下深圳未来一周的天气"}

用户：查上海18号的天气
{"intent": "weather_query", "params": {"city": "上海", "period": "18号"}, "reply": "查一下上海18号的天气"}

用户：北京28号天气
{"intent": "weather_query", "params": {"city": "北京", "period": "28号"}, "reply": "查一下北京28号的天气"}

用户：查甘谷6月20号的天气
{"intent": "weather_query", "params": {"city": "甘谷", "period": "6月20号"}, "reply": "查一下甘谷6月20号的天气"}

用户：甘谷未来一周的天气
{"intent": "weather_query", "params": {"city": "甘谷", "period": "未来一周"}, "reply": "查一下甘谷未来一周的天气"}

用户：查一下上海未来一周天气
{"intent": "weather_query", "params": {"city": "上海", "period": "未来一周"}, "reply": "查一下上海未来一周的天气"}

用户：播放三国演义
{"intent": "play_sanguo", "params": {}, "reply": "播放三国演义"}
用户：播放三国演义第一集
{"intent": "play_sanguo_chapter", "params": {"chapter": 1}, "reply": "播放三国演义第一集"}
用户：三国演义第5集
{"intent": "play_sanguo_chapter", "params": {"chapter": 5}, "reply": "播放三国演义第5集"}
用户：听三国第十集
{"intent": "play_sanguo_chapter", "params": {"chapter": 10}, "reply": "播放三国演义第十集"}

用户：播报作业
{"intent": "read_homework", "params": {}, "reply": "看看今天有什么作业"}
用户：今天什么作业
{"intent": "read_homework", "params": {}, "reply": "查一下作业"}
用户：作业
{"intent": "read_homework", "params": {}, "reply": "好的"}

用户：开启番茄钟
{"intent": "start_pomodoro", "params": {}, "reply": "开启番茄钟"}
用户：开始番茄钟
{"intent": "start_pomodoro", "params": {}, "reply": "好的"}
用户：关闭番茄钟
{"intent": "stop_pomodoro", "params": {}, "reply": "关闭番茄钟"}

用户：今天心情怎么样
{"intent": "chat", "params": {}, "reply": ""}"""


class IntentParser:
    """意图解析器"""

    def __init__(self, api_key=None):
        if api_key is None:
            import config
            api_key = config.DEEPSEEK_KEY
        self.api_key = api_key
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.timeout = 15

    def parse(self, text):
        """
        解析用户指令文字，返回意图字典。
        失败返回 {"intent": "chat", "reply": ""}（降级为聊天）。
        """
        if not text or not text.strip():
            return {"intent": "chat", "params": {}, "reply": ""}

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ]

        for attempt in range(2):
            try:
                resp = requests.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": messages,
                        "temperature": 0.1,
                        "max_tokens": 256,
                    },
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"].strip()

                # 尝试解析 JSON
                return self._parse_json(content)

            except json.JSONDecodeError:
                # 如果结果不是纯 JSON，原样返回作为聊天
                return {"intent": "chat", "params": {}, "reply": content}
            except requests.exceptions.Timeout:
                if attempt == 0:
                    continue
                return {"intent": "chat", "params": {}, "reply": ""}
            except Exception as e:
                print(f"  [意图解析错误] {e}")
                if attempt == 0:
                    continue
                return {"intent": "chat", "params": {}, "reply": ""}

        return {"intent": "chat", "params": {}, "reply": ""}

    def _parse_json(self, text):
        """从 DeepSeek 响应中提取 JSON"""
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试从代码块中提取 json
        import re
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试找第一个 { 和最后一个 }
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass

        # 彻底失败，降级为聊天
        return {"intent": "chat", "params": {}, "reply": ""}

    def chat(self, text):
        """
        纯聊天模式（没有匹配到具体意图时调用）。
        返回回复文字。
        """
        messages = [
            {
                "role": "system",
                "content": "你是一个树莓派上的桌面语音助手，名字叫小土豆。"
                           "回答简短自然，每次不超过 50 个字。说话口语化。",
            },
            {"role": "user", "content": text},
        ]

        try:
            resp = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 200,
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"  [聊天错误] {e}")
            return "我刚才走神了，你能再说一遍吗？"


if __name__ == "__main__":
    """自测：python3 intent_parser.py"""
    print("=" * 30)
    print("  意图解析器自测")
    print("=" * 30)
    p = IntentParser()
    tests = ["播放大海", "下一首", "北京天气", "暂停", "今天心情怎么样"]
    for t in tests:
        r = p.parse(t)
        print(f"  「{t}」→ {r['intent']}")