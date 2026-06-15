# amechan-daily — 超天酱日常推文小站

> DeepSeek V4 驱动的超天酱模拟账号，自动生成双人格推文。
> 最后更新：2026-06-17 (v2.7.2)

## 启动

```bash
conda activate deepseek_v4_api
cd e:/Desktop/Deepseek_V4_API/amechan-daily
python server.py
# → http://127.0.0.1:8930
```

## 当前状态

| 功能 | 状态 |
|------|:--:|
| F7 戳一戳 | ✅ 单条释放+自动补池 |
| JINE 互动聊天 | ✅ 回复队列+贴图专属端点+动态延迟 |
| 推博 Feed | ✅ 每存档独立 timeline |
| 弹幕 | 🟡 72px/3轨/12条/stress联动，偶有刷新闪烁 |
| JINE release 独白 | 🟡 格式强制重写，仍偶有对话泄漏 |
| Webcam | ✅ 18状态/发型稀有/打字→egosearching |
| 多存档 | ✅ 独立 timeline+JINE+stats+trash |

## 架构

```
prompts.py     # KAngel/糖糖人设 + JINE_RELEASE(格式强制)/REPLY/TEXT
generator.py   # DeepSeek API + 重试 + JSON解析
feed.py        # CRUD + pop_from_pool(单条释放)
server.py      # HTTP API + 后台线程生成首条
static/index.html  # 前端单文件 ~2400行
```

## 已知问题

| # | 问题 | 状态 |
|---|------|:--:|
| 1 | JINE release 偶有对话感泄漏 | 🔴 |
| 2 | 弹幕偶尔全部消失再出现 | 🟡 |
| 3 | 贴图回复质量不稳定 | 🟡 |
