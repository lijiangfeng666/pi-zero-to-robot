# pi-zero-to-robot 🎤🤖

> 喊一声 **"土豆"**，树莓派就能放歌给你听。

一个运行在树莓派上的语音助手，从零开始搭建。不需要编程经验，不需要屏幕，**30 分钟从拆快递到喊出第一句**。

[演示视频 — 待录制]

---

## 目录

- [你需要买什么](#你需要买什么)
- [准备工作](#准备工作)
- [第一步：烧录系统](#第一步烧录系统)
- [第二步：连接树莓派](#第二步连接树莓派)
- [第三步：安装依赖](#第三步安装依赖)
- [第四步：部署代码](#第四步部署代码) ← 所有 .py 文件
- [第五步：申请 API Key](#第五步申请-api-key) ← .env.example
- [第六步：测试语音](#第六步测试语音) ← voice.py
- [第七步：部署音乐服务](#第七步部署音乐服务) ← netease.py / music_player.py
- [第八步：启动机器人](#第八步启动机器人) ← main.py / intent_parser.py / executor.py
- [验收清单](#验收清单)
- [日常使用](#日常使用)
- [故障排查](#故障排查)
- [项目结构](#项目结构)
- [License](#license)

---

## 你需要买什么

| 硬件 | 规格 / 型号 | 购买建议 |
|------|-------------|---------|
| **树莓派 4B** | 2GB/4GB/8GB 都行 | 别买错成 3B 或 Zero |
| **MicroSD 卡** | MicroSD 64GB，Class 10 | 闪迪或三星 |
| **USB 读卡器** | 电脑没 SD 槽就要买 | 大部分笔记本自带 |
| **电源** | 3C认证Type-c接口5V/9V/12V/24V充电器 | 搜"树莓派多电压充电器" |
| **麦克风** | 免驱USB麦克风摄像头AI视觉语音 | 搜"USB麦克风摄像头 免驱"，音频+视觉输入一体|
| **音箱** | 免驱USB音箱Y57小扩音器 | 搜"Y57小扩音器"，即插即用 |

### 麦克风和音响注意事项

```
✅ 推荐：免驱USB麦克风摄像头AI视觉语音 + 免驱USB音箱（即插即用）
❌ 不推荐：蓝牙音箱（连接复杂、延迟高）
❌ 不推荐：需要装驱动的设备（树莓派不兼容）
```

### 淘宝搜索关键词

| 你要买 | 搜什么 |
|--------|--------|
| 树莓派 | `树莓派 4B 2GB 套餐`（带电源+散热片更省事） |
| SD 卡 | `闪迪 MicroSD 64G Class10` |
| 麦克风 | `USB麦克风摄像头 免驱` |
| 音箱 | `Y57小扩音器` |

---

## 准备工作

除了树莓派的硬件，你还需要一台**电脑**（Windows 或 Mac），用来给 SD 卡装系统和远程连接树莓派。

全程不需要给树莓派接显示器——所有操作都在电脑上完成。

---

## 第一步：烧录系统

> 把操作系统装到 SD 卡上，就像给新电脑装 Windows。

### 1.1 下载烧录工具

打开浏览器，访问 [Raspberry Pi Imager 下载页](https://www.raspberrypi.com/software/)

- Windows 用户点 "Download for Windows"
- Mac 用户点 "Download for macOS"

下载后双击安装（跟装微信一样，一路"下一步"）。

### 1.2 开始烧录

```
① SD 卡插到读卡器 → 插电脑 USB
② 打开 Raspberry Pi Imager
```

**选择系统：**
```
③ 点「Choose OS」→ Raspberry Pi OS (other)
   → Raspberry Pi OS Lite (64-bit)
   ⚠️ 选 Lite 版！不是 Desktop！
```

**选择 SD 卡：**
```
④ 点「Choose Storage」→ 选中你的 SD 卡
```

### 1.3 ⚠️ 最关键的一步：齿轮设置

**⑤ 点右下角齿轮图标（⚙️）**

**必须填的三项：**

| 设置项 | 填什么 |
|--------|--------|
| **Enable SSH** | 选「Use password authentication」|
| | 用户名：`pi`，密码：`raspberry` |
| **Set WiFi** | 填你家 WiFi 名字和密码 |
| | 国家选 `CN`（中国） |
| **Set timezone** | `Asia/Shanghai` |

**可选（方便找树莓派）：**
```
Set hostname: pi-zero
```

```
⑥ 点「SAVE」→ 点「WRITE」
⑦ 等进度条走完（3-5 分钟）
⑧ 弹出 SD 卡 → 拔下来
```

### 1.4 常见烧录错误

| 错误 | 解法 |
|------|------|
| Imager 不认 SD 卡 | 用 SD Card Formatter 格式化后再试 |
| 忘了设 WiFi | 树莓派连不上网 → SD 卡插回电脑重烧 |
| WiFi 密码填错 | 同上，重烧 |

---

## 第二步：连接树莓派

### 2.1 插卡 + 开机

```
① SD 卡插树莓派背面（金属触点朝上）
② 插电源线（USB-C）
   红灯亮 = 供电正常
   绿灯闪 = 读取 SD 卡（正常）
③ 等 1 分钟让树莓派启动
```

**如果：**
- 红灯不亮 → 电源线问题（需要 5V/3A）
- 绿灯不闪 → SD 卡没插好或烧录失败

### 2.2 找到树莓派的 IP（门牌号）

**方法 A：从路由器看（推荐）**
```
① 打开浏览器
② 输入 192.168.1.1 或 192.168.0.1
   打不开？看路由器背面贴纸上的地址
③ 输入路由器账号密码（也在背面）
④ 找「已连接设备」
⑤ 找名字 "pi-zero" 或 "raspberrypi" → 记下 IP
```

**方法 B：手机 Fing App**
```
① 手机下载「Fing」
② 连你家 WiFi
③ 点扫描 → 找 pi-zero → 记下 IP
```

### 2.3 SSH 连接

打开电脑的终端：

- **Windows**：`Win+R` → 输入 `powershell` → 回车
- **Mac**：打开「终端」应用

```bash
ssh pi@192.168.x.xxx
```
> 把 `192.168.x.xxx` 换成你记下的 IP。

**第一次连接会看到：**
```
Are you sure... (yes/no)?
→ 输入 yes → 回车
```

**输入密码：**
```
pi@192.168.x.xxx's password:
→ 输入 raspberry → 回车
```
（打字不显示是正常的）

**✅ 连上的标志：**
```
pi@pi-zero:~ $
```

> **这个窗口叫"树莓派窗口"**。后面所有标着 🟢 的命令都在这里输入。

### SSH 连不上？排查表

| 错误 | 原因 | 解法 |
|------|------|------|
| `Connection timed out` | 找不到树莓派 | IP 错了？没开机？回 Step 2.2 |
| `Connection refused` | SSH 没开 | SD 卡插回电脑重烧（记得开 SSH）|
| `Permission denied` | 密码错了 | 再输 `raspberry`（全小写）|
| `Host key verification failed` | 重装过系统 | 执行 `ssh-keygen -R IP` 再试 |

---

## 第三步：安装依赖

### 3.1 更新系统

🟢 **在树莓派窗口执行：**

```bash
sudo apt update && sudo apt upgrade -y
```

跑约 2 分钟。黄字警告不用管。

### 3.2 安装系统包

🟢 **复制整段，一次执行：**

```bash
sudo apt install -y python3-pip python3-pyaudio python3-numpy python3-flask python3-requests python3-lxml mpg123 pipewire pipewire-pulse wireplumber portaudio19-dev nodejs git curl
```

### 3.3 安装 Python 包

🟢 **执行：**

```bash
pip3 install baidu-aip python-dotenv
```

如果慢，用国内镜像：
```bash
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple baidu-aip python-dotenv
```

### 3.4 创建项目目录

🟢 **执行：**

```bash
mkdir -p ~/robot
```

---

## 第四步：部署代码

### 4.1 在电脑上下载代码

💻 **在你的电脑上（不是树莓派）：**

```bash
# 方法一：直接 git clone（推荐）
git clone https://github.com/lijiangfeng666/pi-zero-to-robot.git
cd pi-zero-to-robot

# 方法二：下载 ZIP
# 打开 https://github.com/lijiangfeng666/pi-zero-to-robot
# 点绿色「Code」按钮 → 「Download ZIP」
# 解压后进入文件夹
```

### 4.2 传到树莓派

💻 **在电脑上执行（把 IP 换成你的）：**

```bash
scp main.py config.py voice.py music_player.py netease.py executor.py intent_parser.py .env.example pi@192.168.x.xxx:~/robot/
```

**验证文件已传到：**
```bash
ssh pi@192.168.x.xxx "ls ~/robot/"
```

**✅ 看到 7 个 .py 文件 + .env.example → 部署成功。**

---

## 第五步：申请 API Key

机器人需要两个免费的 API Key 才能工作：

| 服务 | 用途 | 费用 |
|------|------|------|
| **百度语音** | 听懂你说话（语音识别）+ 说话给你听（语音合成） | 免费额度够用 |
| **DeepSeek** | 理解你的指令（播放大海→搜索播放） | 注册送额度 |

### 5.1 申请百度语音 Key

💻 **打开浏览器：** [百度语音控制台](https://console.bce.baidu.com/ai-engine/)

```
① 注册/登录百度账号
② 点「语音技术」→ 点「创建应用」
③ 名称填「语音机器人」→ 勾选语音识别 + 语音合成
④ 创建完成 → 复制以下三项：

   AppID:       12345678
   API Key:     abcdefghijklmn
   Secret Key:  1234567890abcdef
```

⚠️ 三个都要保存，后面要用。

### 5.2 申请 DeepSeek Key

💻 **打开浏览器：** [DeepSeek 平台](https://platform.deepseek.com/)

```
① 注册账号 → 登录
② 点左侧「API Keys」→ 点「创建 API Key」
③ 复制生成的 Key（以 sk- 开头）
```

⚠️ 关掉页面就看不到了，立即保存。

### 5.3 填到 .env 文件

🟢 **在树莓派窗口执行：**

```bash
cd ~/robot
cp .env.example .env
nano .env
```

用方向键移动光标，把 `你的APP_ID` 等替换成你刚申请的 Key：

```
BAIDU_APP_ID=12345678
BAIDU_API_KEY=abcdefghijklmn
BAIDU_SECRET_KEY=1234567890abcdef
DEEPSEEK_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**保存：** `Ctrl+X` → `Y` → `回车`

### 5.4 验证 Key

🟢 **执行：**

```bash
cd ~/robot && python3 -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('百度 AppID:', os.getenv('BAIDU_APP_ID') or '❌ 没配置')
print('DeepSeek Key:', '配置了 ✅' if os.getenv('DEEPSEEK_KEY') else '❌ 没配置')
"
```

**✅ 看到两个都有值 → API Key 配置完成。**

---

## 第六步：测试语音

### 6.1 确认麦克风已连接

🟢 **执行：**

```bash
arecord -l
```

**✅ 看到 `card X: Microphone` → 麦克风已识别。**

**❌ `no soundcards found` → 没识别到：**
```
① 换一个 USB 口插麦克风
② 执行 lsusb 看有没有新设备
③ 重启树莓派：sudo reboot
```

### 6.2 确认音箱已连接

🟢 **执行：**

```bash
aplay -l
```

**✅ 看到 `card X: USB Audio` → 音箱已识别。**

### 声卡映射（了解你的设备）

```
card 0: vc4hdmi0      — HDMI 输出（用不到）
card 1: vc4hdmi1      — HDMI 输出（用不到）
card 2: bcm2835       — 3.5mm 耳机口
card 3: WebCamera     — 免驱USB麦克风摄像头AI视觉语音（语音输入）
card 4: USB2.0 Device — 免驱USB音箱Y57小扩音器（语音输出）
```

> 不同品牌的 USB 麦克风和音箱索引号可能不同，这不影响使用，系统会自动检测。

### 6.3 测试录音和回放

对着麦克风说话，录 3 秒：

```bash
arecord -d 3 -f S16_LE -r 16000 /tmp/test.wav
```

回放：

```bash
aplay /tmp/test.wav
```

**✅ 能听到自己说话 → 麦克风和音箱都正常。**

**❌ 回放没声音：**
```
① 检查音箱是否通电、音量是否打开
② 执行 alsamixer 调音量（方向键控制，Esc 退出）
③ 确认 USB 音箱是默认输出：
   pactl set-default-sink "$(pactl list short sinks | head -1 | cut -f1)"
```

### 6.4 测试语音识别（STT）

你说话 → 百度语音转成文字。

🟢 **执行：**

```bash
cd ~/robot && python3 -c "
from voice import VoiceEngine
v = VoiceEngine()
print('录音中，说句话...')
audio = v.record_audio(3)
text = v.speech_to_text(audio)
print('你说的是：' + (text or '没识别到'))
v.pa.terminate()
"
```

对着麦克风说 **"你好"**。

**✅ 看到 `你说的是：你好` → STT 正常。**

**❌ 没识别到：**
```
① 靠近麦克风说
② ping baidu.com 确认网络通
③ 检查 .env 里的百度 Key 是否正确
```

### 6.5 测试语音合成（TTS）

文字转语音从音箱播出来。

🟢 **执行：**

```bash
cd ~/robot && python3 -c "
from voice import VoiceEngine
v = VoiceEngine()
v.text_to_speech('你好，我是你的语音助手')
v.pa.terminate()
"
```

**✅ 音箱出声 → TTS 正常。**

### 6.6 语音快速自检

```bash
cd ~/robot && python3 -c "
from aip import AipSpeech
from dotenv import load_dotenv
import os
load_dotenv()
c = AipSpeech(os.getenv('BAIDU_APP_ID'), os.getenv('BAIDU_API_KEY'), os.getenv('BAIDU_SECRET_KEY'))
r = c.synthesis('测试', 'zh', 1, {'vol': 5})
print('百度语音 Key', '✅' if not isinstance(r, dict) else '❌ 无效')
"
```

---

## 第七步：部署音乐服务

### 7.1 安装网易云 API 服务器

🟢 **在树莓派窗口执行：**

```bash
cd ~/robot && git clone https://github.com/Binaryify/NeteaseCloudMusicApi.git netease-server && cd netease-server && npm install
```

等 1-2 分钟。看到绿色文字就对了。

**如果很慢（国内网络）：**

```bash
cd ~/robot && rm -rf netease-server && git clone https://github.com/Binaryify/NeteaseCloudMusicApi.git netease-server && cd netease-server && npm config set registry https://registry.npmmirror.com && npm install
```

### 7.2 启动并测试

🟢 **启动：**

```bash
cd ~/robot/netease-server && node app.js &
```

🟢 **测试：**

```bash
curl http://127.0.0.1:3000
```

**✅ 返回 JSON 数据 → 服务器跑起来了。**

### 7.3 测试音乐搜索

🟢 **执行：**

```bash
cd ~/robot && python3 -c "
from netease import NetEaseClient
n = NetEaseClient()
songs = n.search('大海')
if songs:
    print(f'搜索 ✅: {songs[0][\"name\"]} - {songs[0].get(\"artist\", \"\")}')
else:
    print('搜索失败，API 服务没启动？')
"
```

**✅ 看到 `搜索 ✅: 大海` → 正常。**

### 7.4 测试音乐播放

🟢 **执行（准备好音箱）：**

```bash
cd ~/robot && python3 -c "
from netease import NetEaseClient
from music_player import MusicPlayer
n = NetEaseClient()
m = MusicPlayer(netease_client=n)
print(m.play('大海'))
import time
time.sleep(10)
m.stop()
"
```

**✅ 听到歌 → 音乐模块完整可用。**

### 7.5 设置开机自启

音乐服务需要一直在后台运行。设置开机自动启动：

🟢 **复制整段一次执行：**

```bash
mkdir -p ~/.config/systemd/user/ && cat > ~/.config/systemd/user/netease-api.service << 'EOF'
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

systemctl --user daemon-reload
systemctl --user enable --now netease-api.service
loginctl enable-linger
```

🟢 **验证：**

```bash
systemctl --user status netease-api.service
```

**✅ 看到 `active (running)` → 自启生效。**

---

## 第八步：启动机器人

### 8.1 测试意图解析

先确认机器人能听懂指令。

🟢 **执行：**

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

**✅ 看到：**
```
播放大海 → play_music
下一首 → next_song
暂停 → pause
今天心情怎么样 → chat
```

### 8.2 手动启动机器人

🟢 **在树莓派窗口执行：**

```bash
cd ~/robot && python3 main.py
```

**✅ 看到：**
```
[1/3] 初始化语音...
  语音 ✅
[2/3] 初始化意图...
  意图 ✅
[3/3] 初始化执行器...
说「土豆」开始使用
```

### 8.3 喊出第一声

对着麦克风说：**"土豆放一首大海"**

**你会经历：**
```
① 你说"土豆放一首大海"
② 机器人检测到声音 → 录音
③ 百度语音识别 → "土豆放一首大海"
④ 分离唤醒词 → 提取指令"放一首大海"
⑤ DeepSeek 理解意图 → {"intent":"play_music", "params":{"keyword":"大海"}}
⑥ 执行器调用搜索 → 搜索到"大海"
⑦ 音箱播放音乐 🎵
```

**✅ 听到音乐 → 成功了！**

### 8.4 其他指令试一下

| 你说 | 机器人做什么 |
|------|------------|
| `土豆下一首` | 切到下一首歌 |
| `土豆暂停` | 暂停播放 |
| `土豆继续` | 恢复播放 |
| `土豆大声点` | 音量调高 |
| `土豆小声点` | 音量调低 |
| `土豆音量80` | 音量精确调到 80% |
| `土豆这是什么歌` | 告诉你当前歌名 |
| `土豆查北京天气` | 播报天气 |

测试完按 `Ctrl+C` 停止。

### 8.5 开机自启

让机器人开机自动运行。

🟢 **创建服务：**

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
```

🟢 **启用并启动：**

```bash
systemctl --user daemon-reload
systemctl --user enable robot.service
systemctl --user start robot.service
```

🟢 **验证：**

```bash
systemctl --user status robot.service
```

**✅ 看到 `active (running)` → 开机自启配置完成。**

### 8.6 重启验证

```bash
sudo reboot
```

等 30 秒。重新 SSH 连上：

```bash
systemctl --user status robot.service
```

**✅ 看到 `active (running)` → 🎉 全部完成！**

---

## 验收清单

- [ ] 树莓派通电后红灯亮、绿灯闪
- [ ] SSH 能连上树莓派
- [ ] 麦克风已识别（`arecord -l` 有输出）
- [ ] 音箱已识别（`aplay -l` 有输出）
- [ ] 录音回放能听到自己说话
- [ ] 百度语音 STT 能把说话转成文字
- [ ] 百度语音 TTS 能从音箱出声
- [ ] 网易云音乐 API 已启动（`curl 127.0.0.1:3000` 返回 JSON）
- [ ] 音乐搜索能搜到歌
- [ ] 音乐播放能听到歌
- [ ] 说"土豆放一首大海"能播放音乐
- [ ] 说"土豆暂停"能暂停
- [ ] 说"土豆继续"能继续播放
- [ ] 说"土豆下一首"能切歌
- [ ] 说"土豆大声点"音量变大
- [ ] 机器人开机自动运行

---

## 日常使用

### 常用命令

| 操作 | 命令 |
|------|------|
| 看机器人状态 | `systemctl --user status robot.service` |
| 看运行日志 | `journalctl --user -u robot.service -n 30` |
| 实时看日志 | `tail -f /tmp/minimal.log \| grep -vE "ALSA\|Cannot\|Jack"` |
| 重启机器人 | `systemctl --user restart robot.service` |
| 停止机器人 | `systemctl --user stop robot.service` |

### 常用参数调优

在 `~/robot/.env` 文件中（改完重启机器人生效）：

| 参数 | 默认值 | 作用 |
|------|--------|------|
| `WAKE_WORD` | 土豆 | 唤醒词，可改成你喜欢的 |
| `VAD_THRESHOLD` | 2500 | 麦克风灵敏度，越小越灵敏 |
| `MIC_GAIN` | 3000 | 麦克风增益，越大越灵敏 |
| `VOLUME` | 1.0 | 默认音量（0.0~1.0） |
| `WAKE_RECORD_SECONDS` | 1.5 | 唤醒后录音时长（秒） |
| `RECORD_SECONDS` | 2.0 | 普通指令录音时长（秒） |

### 更新代码

```bash
# 在电脑上改好文件后传到树莓派
scp main.py pi@192.168.x.xxx:~/robot/
# 传完重启
ssh pi@192.168.x.xxx "systemctl --user restart robot.service"
```

---

## 故障排查

### 说"土豆"没反应

```
① 靠近麦克风大声一点
② 看机器人日志：journalctl --user -u robot.service -n 20
③ 确认麦克风正常工作：arecord -d 3 /tmp/t.wav && aplay /tmp/t.wav
④ 调低 VAD_THRESHOLD（改成 300 试试）
```

### 播放音乐没声音

```
① 确认网易云 API 在运行：curl http://127.0.0.1:3000
② 确认音箱连接：aplay -l
③ 手动测试播放：mpg123 一个.mp3 文件
④ 调音量：pactl set-sink-volume 0 70%
```

### 语音识别总是返回 None

```
① ping baidu.com 确认网络通
② 检查 .env 里的百度 Key
③ 靠近麦克风说话
```

### 开机不自启

```bash
systemctl --user status robot.service
journalctl --user -u robot.service -n 20 --no-pager
```

### 快速自检命令

```bash
echo "=== 文件 ===" && ls ~/robot/*.py 2>&1 | wc -l && echo "个.py" && echo "=== 麦克风 ===" && arecord -l 2>&1 | head -2 && echo "=== 内存 ===" && free -h | grep Mem && echo "=== 服务 ===" && systemctl --user is-active robot.service 2>/dev/null || echo "未配置"
```

---

## 项目结构

```
pi-zero-to-robot/
├── main.py              # 主程序（唤醒 + 指令分发）
├── config.py            # 配置（从 .env 读取）
├── voice.py             # 百度语音识别/合成
├── music_player.py      # 音乐播放控制（mpg123 + PipeWire）
├── netease.py           # 网易云音乐 API 客户端
├── executor.py          # 指令执行器
├── intent_parser.py     # DeepSeek 意图解析
├── .env.example         # API Key 模板（复制为 .env 并填入 Key）
├── .gitignore
├── LICENSE
└── README.md
```

### 各模块职责

| 文件 | 干什么的 |
|------|---------|
| `main.py` | 主循环：检测声音 → 识别 → 理解 → 执行 |
| `config.py` | 从 `.env` 读取 API Key 和运行参数 |
| `voice.py` | 百度语音 SDK 封装：录音 → 文字（STT），文字 → 语音（TTS）|
| `netease.py` | 网易云音乐 API 搜索/歌词/歌曲 URL 获取 |
| `music_player.py` | 音乐播放控制：播放/暂停/切歌/音量（基于 mpg123 + PipeWire）|
| `intent_parser.py` | 调用 DeepSeek 把自然语言转为结构化指令 |
| `executor.py` | 根据指令类型调用对应模块 |

### 软件架构

```
麦克风 → voice.py(STT) → main.py(唤醒检测) → intent_parser.py(DeepSeek)
                                                        ↓
音箱 ← voice.py(TTS)  ← executor.py(执行)    ← 结构化指令 JSON
                            ↓
                    ┌── music_player.py → mpg123 → 音箱
                    ├── netease.py → 网易云 API → 歌曲 URL
                    └── (后续可扩展天气/闹钟等)
```

### 音频链路

```
歌曲下载 → mpg123 播放器 → PipeWire 混音 → USB 音箱 发出声音
                           ↓
                    可在播放中调音量（不影响系统其他声音）
```

---

## License

MIT
