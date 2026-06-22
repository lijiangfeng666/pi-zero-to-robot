# GitHub开源 - pi-zero-to-robot

## 目标
把本地仓库推到 GitHub，完成首次开源发布。

## 当前状态

### 已完成
- ✅ 源码脱敏：config.py 已清除硬编码 API Key，改为从 .env 读取
- ✅ .env.example 已创建（含API Key申请链接）
- ✅ .gitignore 已创建（排除 .env、日志、备份文件）
- ✅ LICENSE（MIT）已创建
- ✅ README.md 已重写（从拆快递到喊出第一句）
- ✅ 本地 git 已初始化，已 commit
- ✅ 仓库 `lijiangfeng666/pi-zero-to-robot` 已在 GitHub 创建
- ✅ 不含：天气、闹钟、番茄钟、cookie、日志、备份文件（最小版本）

### 最小版本包含的文件
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

## 推送步骤（WSL 终端）

### 1. 进入仓库目录
```bash
cd ~/pi-zero-to-robot
```

### 2. 设置远程地址
```bash
# 先在 GitHub 生成 Personal Access Token：
# https://github.com/settings/tokens/new
# 勾选 repo 权限，复制 token
git remote set-url origin https://用户名:你的token@github.com/lijiangfeng666/pi-zero-to-robot.git
```

### 3. 推送到 GitHub
```bash
git push -u origin main
```

### 4. 验证
浏览器打开 https://github.com/lijiangfeng666/pi-zero-to-robot 确认文件已上传。

## 推送失败的排查

| 报错 | 原因 | 解决办法 |
|------|------|---------|
| `Repository not found` | 仓库名不对或 token 没权限 | 检查仓库名是否正确，token 是否有 `repo` 权限 |
| `Authentication failed` | token 过期或无效 | 重新生成 token：https://github.com/settings/tokens/new |
| `not a git repository` | 不在仓库目录 | `cd ~/pi-zero-to-robot` 先 |

## 后续（推送成功后）
- 拍一条演示视频 → 更新 README 里的演示链接
- 发抖音：喊"土豆放首大海"的 15 秒视频
- GitHub Issues 收集用户反馈
