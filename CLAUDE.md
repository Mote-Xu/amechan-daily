# amechan-daily — 超天酱日常推文小站

> DeepSeek V4 驱动的超天酱模拟账号，自动生成双人格推文。
> 最后更新：2026-06-17 (v2.7.2)

## 启动

```bash
conda activate deepseek_v4_api
cd /mnt/e/Desktop/Deepseek_V4_API/amechan-daily
python server.py
# → http://127.0.0.1:8930
```

## 架构

```
amechan-daily/
  prompts.py               # JINE_REPLY/JINE_TEXT/JINE_RELEASE + 铁律
  generator.py             # DeepSeek API + 重试 + JSON解析
  feed.py                  # timeline/hidden_pool/JINE chat CRUD
  server.py                # HTTP API (后台线程生成首条)
  static/index.html        # 前端单文件 ~2300行
  data/feed.json           # 持久化
```

## 核心机制

- **L1 Poketter**: 超天酱公开推文，绝口不提阿P
- **L2 Diary**: 糖糖私密日记
- **L3 JINE**: 糖糖→阿P 私信，统一聊天流
- **回复队列**: `_startReplyCycle()` 合并多条玩家消息→一次 API→一条回复
- **Webcam**: Canvas 18状态, rAF, 发型稀有池(10%)

## v2.7.2 改动记录

| 日期 | 改动 |
|------|------|
| 6/17 | fetchTimeline: 空数据不消费 firstLoad; 内部轮询 |
| 6/17 | _startReplyCycle: abort 旧请求合并重发; AbortError 不插降级回复 |
| 6/17 | _replyPending 移到 .then() 第一行释放; checkTriggerWords try/catch |
| 6/17 | 贴图路由到 /api/jine/send; 最小打字延迟 2.5s |
| 6/17 | 玩家消息立刻持久化到 SaveManager |
| 6/17 | 弹幕: animation 简写→animationDuration 单独设 |
| 6/17 | server.py 首条生成→后台线程; JINE prompt 严禁 meta+高频限制 |

## 已知问题

| # | 问题 | 状态 |
|---|------|:--:|
| 1 | 弹幕看不到 | 🔴 |
| 2 | JINE 贴图回复质量低 | 🟡 |
| 3 | 回复太快不自然 | 🟡 |
| 4 | 部分 CSS 细节 (v2.3 遗留) | 🟡 |
