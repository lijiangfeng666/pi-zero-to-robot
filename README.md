# pi-zero-to-robot 🎤🤖

> 树莓派Zero语音机器人 —— 喊一声"土豆"就能放歌。

一个运行在树莓派上的语音助手：说"土豆"唤醒 → 说歌名 → 放歌。做了减法，只做一件事：**语音控制音乐播放**。

[演示视频 — 待录制]

---

## 硬件清单

| 硬件 | 型号参考 | 用途 |
|------|---------|------|
| 树莓派Zero 2 W | Raspberry Pi Zero 2 W | 主板 |
| MicroSD卡 | 16GB+ Class 10 | 系统盘 |
| USB麦克风 | USB WebCamera / USB麦克风 | 语音输入 |
| USB音箱 | USB 2.0音箱 | 音频输出 |
| 电源 | 5V/2.5A Type-C | 供电 |
| 杜邦线/外壳 | 可选 | 扩展 |

---

## 快速开始（从拆快递到喊出第一句）

### 0. 准备工作

你需要一台电脑（Windows/Mac），一张MicroSD卡，一个读卡器。

### 1. 烧录系统

1. 下载 [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. 打开 Imager → 选择：**Raspberry Pi OS Lite (64-bit)**
3. 点击齿轮图标 ⚙️ → 设置：
   - 主机名：`pi-zero`
   - 启用SSH ✅
   - 设置用户名和密码
   - 配置WiFi（你的家庭WiFi名和密码）
4. 写入SD卡 → 插入树莓派 → 通电

> 全程不接显示器。树莓派开机后会自动连WiFi。

### 2. 找到树莓派的IP

```bash
# 在电脑上执行
# Windows: Win+R → powershell
ping pi-zero.local
# 或者进路由器管理页面找
```

记下显示的IP，后面替换 `<树莓派IP>`。

### 3. SSH连接

```bash
ssh 用户名@<树莓派IP>
# 输入你设置的密码
```

### 4. 安装依赖

```bash
# 系统包
sudo apt update && sudo apt install -y python3-pip python3-pyaudio mpg123 pipewire pipewire-pulse

# Python 包
pip3 install baidu-aip openai python-dotenv

# 安装网易云API服务器
git clone https://github.com/Binaryify/NeteaseCloudMusicApi.git ~/netease-api
cd ~/netease-api && npm install
```

### 5. 获取API Key

| 服务 | 用途 | 申请地址 |
|------|------|---------|
| 百度语音 | 语音识别+合成 | https://console.bce.baidu.com/ai/#/ai/speech/overview |
| DeepSeek | 意图理解 | https://platform.deepseek.com/ |

申请后填入 `.env` 文件：

```bash
cd ~/robot
cp .env.example .env
nano .env
# 粘贴你的API Key
```

### 6. 部署代码

```bash
# 在电脑上执行（不是在树莓派上）
cd pi-zero-to-robot
scp main.py config.py voice.py music_player.py netease.py executor.py intent_parser.py 用户名@<树莓派IP>:~/robot/
```

### 7. 启动

```bash
# SSH到树莓派
cd ~/robot

# 启动网易云API
cd ~/netease-api && node index.js &

# 启动机器人
cd ~/robot && python3 main.py
```

### 8. 验收

对着麦克风说：**"土豆放一首大海"**

听到「主人有什么需求」→ 然后音乐响起 → ✅ 成功了

---

## 语音指令

| 你说 | 机器人做什么 |
|------|------------|
| 土豆 | 唤醒 |
| 土豆放一首大海 | 唤醒+搜索播放 |
| 暂停 / 下一首 / 继续 | 播放控制 |
| 大声点 / 小声点 | 音量调节 |

完整指令表见 `docs/voice-commands.md`。

---

## 项目结构

```
pi-zero-to-robot/
├── main.py              # 主程序（唤醒+指令分发）
├── config.py            # 配置（从.env读取）
├── voice.py             # 百度语音识别/合成
├── music_player.py      # 音乐播放控制
├── netease.py           # 网易云音乐API
├── executor.py          # 指令执行器
├── intent_parser.py     # DeepSeek意图解析
├── .env.example         # API Key模板
├── .gitignore
├── LICENSE
└── README.md
```

---

## License

MIT
