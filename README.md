# pi-zero-to-robot 🎤🤖

> 喊一声 **"土豆"**，树莓派就能放歌给你听。

一个运行在树莓派上的语音助手，从零开始搭建。不需要编程经验，不需要屏幕，**30 分钟从拆快递到喊出第一句**。

---

## 目录

- [第一步：你需要买什么](#第一步你需要买什么)
- [第二步：准备工作](#第二步准备工作)
- [第三步：烧录系统](#第三步烧录系统)
- [第四步：连接树莓派](#第四步连接树莓派)
- [第五步：安装依赖](#第五步安装依赖)
- [第六步：部署代码和配置密钥](#第六步部署代码和配置密钥)
- [第七步：测试语音](#第七步测试语音)
- [第八步：部署音乐服务](#第八步部署音乐服务)
- [第九步：启动机器人](#第九步启动机器人)
- [第十步：日常使用](#第十步日常使用)
- [第十一步：故障排查](#第十一步故障排查)

---

## 第一步：你需要买什么

| 硬件 | 规格 / 型号 | 购买建议 |
|------|-------------|---------|
| **树莓派 4B** | 2GB/4GB/8GB 都行 | 别买错成 3B、3B+ 或 Zero |
| **MicroSD 卡** | MicroSD 64GB，Class 10 | 闪迪或三星 |
| **USB 读卡器** | 电脑没 SD 卡槽就要买 | 大部分笔记本自带 |
| **电源** | 3C认证Type-c接口5V/9V/12V/24V充电器 | 搜"树莓派多电压充电器" |
| **麦克风** | 免驱USB麦克风摄像头AI视觉语音 | 搜"USB麦克风摄像头 免驱"，音频+视觉输入一体 |
| **音箱** | 免驱USB音箱Y57小扩音器 | 搜"Y57小扩音器"，即插即用 |

> ✅ 推荐免驱设备，即插即用。
> ❌ 不推荐蓝牙音箱（连接复杂、延迟高）和需要装驱动的设备（树莓派不兼容）。

**✅ 确认你收到了以上全部硬件，缺任何一样都无法继续。**

---

## 第二步：准备工作

除了树莓派的硬件，你还需要一台**电脑**（Windows 或 Mac），用来给 SD 卡装系统和远程连接树莓派。

全程不需要给树莓派接显示器——所有操作都在电脑上完成。

**✅ 确认有一台能上网的电脑（Windows/Mac）→ 继续下一步。**

---

## 第三步：烧录系统

> 把操作系统装到 SD 卡上，就像给新电脑装 Windows。

### 3.1 下载烧录工具

打开浏览器，访问 [Raspberry Pi Imager 下载页](https://www.raspberrypi.com/software/)

- Windows 用户点 "Download for Windows"
- Mac 用户点 "Download for macOS"

下载后双击安装（跟装微信一样，一路"下一步"）。

### 3.2 开始烧录

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

### 3.3 ⚠️ 最关键的一步：齿轮设置

**⑤ 点右下角齿轮图标（⚙️）**

**必须填的三项：**

| 设置项 | 填什么 |
|--------|--------|
| **Enable SSH** | 选「Use password authentication」 |
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

**✅ SD 卡烧录完成**

### 3.4 常见烧录错误

| 错误 | 解法 |
|------|------|
| Imager 不认 SD 卡 | 用 SD Card Formatter 格式化后再试 |
| 忘了设 WiFi | 树莓派连不上网 → SD 卡插回电脑重烧 |
| WiFi 密码填错 | 同上，重烧 |

---

## 第四步：连接树莓派

### 4.1 插卡 + 开机

```
① SD 卡插树莓派背面（金属触点朝上）
② 插电源线（USB-C）
   红灯亮 = 供电正常
   绿灯闪 = 读取 SD 卡（正常）
③ 等 1 分钟让树莓派启动完
```

**如果：**
- 红灯不亮 → 电源问题（需要 5V/3A）
- 绿灯不闪 → SD 卡没插好或烧录失败

### 4.2 找到树莓派的 IP（门牌号）

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

**✅ 找到 IP → 继续下一步**

### 4.3 SSH 连接

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
出现这个提示符 → SSH 成功。

> **这个窗口叫"树莓派窗口"**。后面所有标着 🟢 的命令都在这里输入。

### 4.4 SSH 连不上？排查表

| 错误 | 原因 | 解法 |
|------|------|------|
| `Connection timed out` | 找不到树莓派 | IP 错了？没开机？回 4.2 重新找 IP |
| `Connection refused` | SSH 没开 | SD 卡插回电脑重烧（记得开 SSH） |
| `Permission denied` | 密码错了 | 再输 `raspberry`（全小写） |
| `Host key verification failed` | 重装过系统 | 执行 `ssh-keygen -R IP` 再试 |

---

## 第五步：安装依赖

> 🟢 以下所有命令都在树莓派窗口执行。

### 5.1 更新系统

```bash
sudo apt update && sudo apt upgrade -y
```
跑约 2 分钟。黄字警告不用管。

### 5.2 安装系统包

**复制整段，一次执行：**
```bash
sudo apt install -y python3-pip python3-pyaudio python3-numpy python3-requests python3-lxml mpg123 pipewire pipewire-pulse wireplumber portaudio19-dev nodejs git curl
```

### 5.3 安装 Python 包

```bash
pip3 install baidu-aip python-dotenv
```

如果慢，用国内镜像：
```bash
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple baidu-aip python-dotenv
```

### 5.4 创建项目目录

```bash
mkdir -p ~/robot
```

**✅ 依赖安装完成**

---

## 第六步：部署代码和配置密钥

### 6.1 在电脑上下载代码

💻 **在你的电脑上（不是树莓派）执行：**

```bash
git clone https://github.com/lijiangfeng666/pi-zero-to-robot.git
cd pi-zero-to-robot
```

如果没装 git，点 GitHub 页面绿色「Code」按钮 → 「Download ZIP」，解压后进入文件夹。

### 6.2 传到树莓派

💻 **在电脑上执行（把 IP 换成你的）：**

```bash
scp main.py config.py voice.py music_player.py netease.py executor.py intent_parser.py .env.example pi@192.168.x.xxx:~/robot/
```

**验证文件已传到：**
```bash
ssh pi@192.168.x.xxx "ls ~/robot/"
```

**✅ 看到 7 个 .py 文件 + .env.example → 部署成功。**

### 6.3 申请百度语音 Key

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

### 6.4 申请 DeepSeek Key

💻 **打开浏览器：** [DeepSeek 平台](https://platform.deepseek.com/)

```
① 注册账号 → 登录
② 点左侧「API Keys」→ 点「创建 API Key」
③ 复制生成的 Key（以 sk- 开头）
```

⚠️ 关掉页面就看不到了，立即保存。

### 6.5 填到 .env 文件

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

### 6.6 验证 Key

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

## 第七步：测试语音

### 7.1 确认麦克风已连接

```bash
arecord -l
```

**✅ 看到 `card X: WebCamera` 或 `Microphone` → 麦克风已识别。**

**❌ `no soundcards found` → 没识别到：**
```
① 换一个 USB 口插麦克风
② 执行 lsusb 看有没有新设备
③ 重启树莓派：sudo reboot
```

### 7.2 确认音箱已连接

```bash
aplay -l
```

**✅ 看到 `card X: USB2.0 Device` 或 `USB Audio` → 音箱已识别。**

### 7.3 声卡映射

你可能会看到类似这样的声卡列表：
```
card 0: vc4hdmi0      — HDMI 输出（用不到）
card 1: vc4hdmi1      — HDMI 输出（用不到）
card 2: bcm2835       — 3.5mm 耳机口
card 3: WebCamera     — USB 麦克风（语音输入）
card 4: USB2.0 Device — USB 音箱（语音输出）
```

不同品牌的 USB 设备索引号可能不同，这不影响使用，系统会自动检测。

### 7.4 测试录音和回放

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
③ 确认音箱是默认输出：
   pactl set-default-sink "$(pactl list short sinks | head -1 | cut -f1)"
```

### 7.5 测试语音识别（STT）

你说话 → 百度语音转成文字。

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

### 7.6 测试语音合成（TTS）

文字转语音，从音箱播出来。

```bash
cd ~/robot && python3 -c "
from voice import VoiceEngine
v = VoiceEngine()
v.text_to_speech('你好，我是你的语音助手')
v.pa.terminate()
"
```

**✅ 音箱出声 → TTS 正常。**

### 7.7 语音快速自检

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

## 第八步：部署音乐服务

### 8.1 安装网易云 API 服务器

```bash
cd ~/robot && git clone https://github.com/Binaryify/NeteaseCloudMusicApi.git netease-server && cd netease-server && npm install
```

等 1-2 分钟。看到绿色文字就对了。

**如果很慢（国内网络）：**
```bash
cd ~/robot && rm -rf netease-server && git clone https://github.com/Binaryify/NeteaseCloudMusicApi.git netease-server && cd netease-server && npm config set registry https://registry.npmmirror.com && npm install
```

### 8.2 启动并测试

```bash
cd ~/robot/netease-server && node app.js &
```

```bash
curl http://127.0.0.1:3000
```

**✅ 返回 JSON 数据 → 服务器跑起来了。**

### 8.3 测试音乐搜索

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

### 8.4 测试音乐播放

准备好音箱，执行：
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

### 8.5 音乐服务开机自启

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

**验证：**
```bash
systemctl --user status netease-api.service
```

**✅ 看到 `active (running)` → 自启生效。**

---

## 第九步：启动机器人

### 9.1 测试意图解析

先确认机器人能听懂指令。

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

### 9.2 手动启动机器人

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

### 9.3 喊出第一声

对着麦克风说：**"土豆放一首大海"**

你会经历：
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

测试完按 `Ctrl+C` 停止。

### 9.4 其他指令试一下

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

### 9.5 机器人开机自启

让机器人开机自动运行。

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

启用并启动：
```bash
systemctl --user daemon-reload
systemctl --user enable robot.service
systemctl --user start robot.service
```

验证：
```bash
systemctl --user status robot.service
```

**✅ 看到 `active (running)` → 开机自启配置完成。**

### 9.6 重启验证

```bash
sudo reboot
```

等 30 秒。重新 SSH 连上：

```bash
systemctl --user status robot.service
```

**✅ 看到 `active (running)` → 🎉 全部完成！**

---

## 第十步：日常使用

### 常用命令

| 操作 | 命令 |
|------|------|
| 看机器人状态 | `systemctl --user status robot.service` |
| 看运行日志 | `journalctl --user -u robot.service -n 30` |
| 实时看日志 | `tail -f /tmp/minimal.log \| grep -vE "ALSA\|Cannot\|Jack"` |
| 重启机器人 | `systemctl --user restart robot.service` |
| 停止机器人 | `systemctl --user stop robot.service` |

### 常用参数调优

在 `~/robot/.env` 文件中修改，改完重启机器人生效：

| 参数 | 默认值 | 作用 |
|------|--------|------|
| `WAKE_WORD` | 土豆 | 唤醒词，可改成你喜欢的 |
| `VAD_THRESHOLD` | 2500 | 麦克风灵敏度，越小越灵敏 |
| `MIC_GAIN` | 3000 | 麦克风增益，越大越灵敏 |
| `VOLUME` | 1.0 | 默认音量（0.0~1.0） |
| `WAKE_RECORD_SECONDS` | 1.5 | 唤醒后录音时长（秒） |
| `RECORD_SECONDS` | 2.0 | 普通指令录音时长（秒） |
| `COMMAND_TIMEOUT` | 4 | 指令超时（秒），超时后重新唤醒 |

**✅ 改完 `.env` → 运行 `systemctl --user restart robot.service` 生效。**

### 更新代码

```bash
# 在电脑上改好文件后传到树莓派
scp main.py pi@192.168.x.xxx:~/robot/
# 传完重启
ssh pi@192.168.x.xxx "systemctl --user restart robot.service"
```

---

## 第十一步：故障排查

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

## License

MIT