# pi-zero-to-robot 🎤🤖

> 喊一声 **"土豆"**，树莓派就能放歌给你听。

一个运行在树莓派上的语音助手，从零开始搭建。不需要编程经验，不需要屏幕，**30 分钟从拆快递到喊出第一句**。

[演示视频 — 待录制]

---

## 目录

- [你需要买什么](#你需要买什么)
- [准备工作](#准备工作)
- [烧录系统](#烧录系统)
- [连接树莓派](#连接树莓派)
- [安装依赖](#安装依赖)
- config.py / .env.example
- voice.py
- netease.py / music_player.py
- intent_parser.py / executor.py
- main.py
- [日常使用](#日常使用)
- [故障排查](#故障排查)

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

## 烧录系统

> 把操作系统装到 SD 卡上，就像给新电脑装 Windows。

### 下载烧录工具

打开浏览器，访问 [Raspberry Pi Imager 下载页](https://www.raspberrypi.com/software/)

- Windows 用户点 "Download for Windows"
- Mac 用户点 "Download for macOS"

下载后双击安装（跟装微信一样，一路"下一步"）。

### 开始烧录

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

### ⚠️ 最关键的一步：齿轮设置

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

### 常见烧录错误

| 错误 | 解法 |
|------|------|
| Imager 不认 SD 卡 | 用 SD Card Formatter 格式化后再试 |
| 忘了设 WiFi | 树莓派连不上网 → SD 卡插回电脑重烧 |
| WiFi 密码填错 | 同上，重烧 |

---

## 连接树莓派

### 插卡 + 开机

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

### 找到树莓派的 IP（门牌号）

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

### SSH 连接

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

## 安装依赖

### 更新系统

🟢 **在树莓派窗口执行：**

```bash
sudo apt update && sudo apt upgrade -y
```

跑约 2 分钟。黄字警告不用管。

### 安装系统包

🟢 **复制整段，一次执行：**

```bash
sudo apt install -y python3-pip python3-pyaudio python3-numpy python3-flask python3-requests python3-lxml mpg123 pipewire pipewire-pulse wireplumber portaudio19-dev nodejs git curl
```

### 安装 Python 包

🟢 **执行：**

```bash
pip3 install baidu-aip python-dotenv
```

如果慢，用国内镜像：
```bash
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple baidu-aip python-dotenv
```

### 创建项目目录

🟢 **执行：**

```bash
mkdir -p ~/robot
```

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

## License

MIT
