# pi-zero-to-robot 🎤🤖

> 喊一声 **"土豆"**，树莓派就能放歌给你听。

一个运行在树莓派上的语音助手，从零开始搭建。不需要编程经验，不需要屏幕，**30 分钟从拆快递到喊出第一句**。

[演示视频 — 待录制]

---

## 目录

- [第一步：你需要买什么](#step1)
- [第二步：准备工作](#step2)
- [第三步：烧录系统](#step3)
- [第四步：连接树莓派](#step4)
- [第五步：安装依赖](#step5)
- [第六步：配置与密钥](#step6) — config.py / .env.example
- [第七步：语音识别与合成](#step7) — voice.py
- [第八步：音乐服务](#step8) — netease.py / music_player.py
- [第九步：指令系统](#step9) — intent_parser.py / executor.py
- [第十步：主程序](#step10) — main.py
- [日常使用](#日常使用)
- [故障排查](#故障排查)

---

<a name="step1"></a>
## 第一步：你需要买什么

| 硬件 | 规格 / 型号 | 购买建议 |
|------|-------------|---------|
| **树莓派 4B** | 2GB/4GB/8GB 都行 | 别买错成 3B 或 Zero |
| **MicroSD 卡** | MicroSD 64GB，Class 10 | 闪迪或三星 |
| **USB 读卡器** | 电脑没 SD 槽就要买 | 大部分笔记本自带 |
| **电源** | 3C认证Type-c接口5V/9V/12V/24V充电器 | 搜"树莓派多电压充电器" |
| **麦克风** | 免驱USB麦克风摄像头AI视觉语音 | 搜"USB麦克风摄像头 免驱" |
| **音箱** | 免驱USB音箱Y57小扩音器 | 搜"Y57小扩音器"，即插即用 |

> ✅ 推荐免驱设备，即插即用。❌ 不推荐蓝牙音箱或需装驱动的设备。

---

<a name="step2"></a>
## 第二步：准备工作

一台电脑（Windows/Mac），用来给 SD 卡装系统和远程连接树莓派。全程不需要给树莓派接显示器。

---

<a name="step3"></a>
## 第三步：烧录系统

下载 [Raspberry Pi Imager](https://www.raspberrypi.com/software/)，选 **Raspberry Pi OS Lite (64-bit)**。

⚠️ 点齿轮图标设置：
- **Enable SSH** → 用户名 `pi`，密码 `raspberry`
- **Set WiFi** → 填你家 WiFi
- **Set timezone** → `Asia/Shanghai`

点 WRITE，等进度条走完。

---

<a name="step4"></a>
## 第四步：连接树莓派

SD 卡插入树莓派 → 插电源开机。找到树莓派的 IP 地址（路由器管理页找 `pi-zero`）。

```bash
ssh pi@192.168.x.xxx
```

密码：`raspberry`

---

<a name="step5"></a>
## 第五步：安装依赖

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-pyaudio python3-numpy python3-requests python3-lxml mpg123 pipewire pipewire-pulse wireplumber portaudio19-dev nodejs git curl
pip3 install baidu-aip python-dotenv
mkdir -p ~/robot
```

---

<a name="step6"></a>
## 第六步：配置与密钥

代码文件：[config.py](https://github.com/lijiangfeng666/pi-zero-to-robot/blob/main/config.py) / [.env.example](https://github.com/lijiangfeng666/pi-zero-to-robot/blob/main/.env.example)

在电脑上下载代码并传到树莓派：

```bash
git clone https://github.com/lijiangfeng666/pi-zero-to-robot.git
cd pi-zero-to-robot
scp *.py .env.example pi@192.168.x.xxx:~/robot/
```

需要申请两个免费 API Key：

| 服务 | 申请地址 |
|------|---------|
| 百度语音 | [console.bce.baidu.com/ai-engine/](https://console.bce.baidu.com/ai-engine/) |
| DeepSeek | [platform.deepseek.com](https://platform.deepseek.com/) |

在树莓派上：
```bash
cd ~/robot
cp .env.example .env
nano .env   # 填入你的 Key
```

---

<a name="step7"></a>
## 第七步：语音识别与合成

代码文件：[voice.py](https://github.com/lijiangfeng666/pi-zero-to-robot/blob/main/voice.py)

确认硬件：
```bash
arecord -l  # 麦克风
aplay -l    # 音箱
```

对着麦克风说话，录 3 秒回放：
```bash
arecord -d 3 -f S16_LE -r 16000 /tmp/test.wav
aplay /tmp/test.wav
```

测试语音识别（STT）：
```bash
cd ~/robot && python3 -c "
from voice import VoiceEngine
v = VoiceEngine()
audio = v.record_audio(3)
text = v.speech_to_text(audio)
print('你说的是：' + (text or '没识别到'))
"
```

测试语音合成（TTS）：
```bash
cd ~/robot && python3 -c "
from voice import VoiceEngine
v = VoiceEngine()
v.text_to_speech('你好，我是你的语音助手')
"
```

---

<a name="step8"></a>
## 第八步：音乐服务

代码文件：[netease.py](https://github.com/lijiangfeng666/pi-zero-to-robot/blob/main/netease.py) / [music_player.py](https://github.com/lijiangfeng666/pi-zero-to-robot/blob/main/music_player.py)

安装网易云 API 服务器：
```bash
cd ~/robot
git clone https://github.com/Binaryify/NeteaseCloudMusicApi.git netease-server
cd netease-server && npm install
node app.js &
```

测试搜索和播放：
```bash
cd ~/robot && python3 -c "
from netease import NetEaseClient
n = NetEaseClient()
songs = n.search('大海')
print('搜索:', songs[0]['name'] if songs else '失败')
"
```

设置开机自启：
```bash
mkdir -p ~/.config/systemd/user/
cat > ~/.config/systemd/user/netease-api.service << 'EOF'
[Unit]
Description=NetEase Cloud Music API
After=network.target
[Service]
Type=simple
WorkingDirectory=%h/robot/netease-server
ExecStart=/usr/bin/node app.js
Restart=on-failure
RestartSec=5
[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload && systemctl --user enable --now netease-api.service
loginctl enable-linger
```

---

<a name="step9"></a>
## 第九步：指令系统

代码文件：[intent_parser.py](https://github.com/lijiangfeng666/pi-zero-to-robot/blob/main/intent_parser.py) / [executor.py](https://github.com/lijiangfeng666/pi-zero-to-robot/blob/main/executor.py)

测试意图解析：
```bash
cd ~/robot && python3 -c "
from intent_parser import IntentParser
p = IntentParser()
tests = ['播放大海', '下一首', '暂停', '今天心情怎么样']
for t in tests:
    r = p.parse(t)
    print(f'{t} → {r[\"intent\"]}')
"
```

期望结果：
```
播放大海 → play_music
下一首 → next_song
暂停 → pause
今天心情怎么样 → chat
```

---

<a name="step10"></a>
## 第十步：主程序

代码文件：[main.py](https://github.com/lijiangfeng666/pi-zero-to-robot/blob/main/main.py)

手动启动：
```bash
cd ~/robot && python3 main.py
```

对着麦克风说 **"土豆放一首大海"**。

设置开机自启：
```bash
cat > ~/.config/systemd/user/robot.service << 'EOF'
[Unit]
Description=Robot Service
After=network.target sound.target netease-api.service
[Service]
Type=simple
ExecStart=/usr/bin/python3 %h/robot/main.py
WorkingDirectory=/home/pi/robot
Restart=on-failure
RestartSec=10
[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload && systemctl --user enable robot.service && systemctl --user start robot.service
```

验证：
```bash
systemctl --user status robot.service
```

---

<a name="日常使用"></a>
## 日常使用

| 操作 | 命令 |
|------|------|
| 看机器人状态 | `systemctl --user status robot.service` |
| 看运行日志 | `journalctl --user -u robot.service -n 30` |
| 重启机器人 | `systemctl --user restart robot.service` |

| 参数 | 默认值 | 作用 |
|------|--------|------|
| `VAD_THRESHOLD` | 2500 | 麦克风灵敏度，越小越灵敏 |
| `MIC_GAIN` | 3000 | 麦克风增益，越大越灵敏 |
| `VOLUME` | 1.0 | 默认音量 |

---

<a name="故障排查"></a>
## 故障排查

**说"土豆"没反应：** 靠近麦克风、调低 VAD_THRESHOLD、检查日志 `journalctl --user -u robot.service -n 20`

**播放音乐没声音：** 确认 `curl http://127.0.0.1:3000` 返回 JSON、检查音箱连接、调音量

**语音识别返回 None：** `ping baidu.com` 确认网络、检查 .env 里的百度 Key

---

## License

MIT