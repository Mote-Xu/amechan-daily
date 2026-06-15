# 项目总结 — 超天酱日常推文小站

> 发给 Gemini 的完整项目总结。最后更新：2026-06-17 (v2.7.2)

---

## ⚠️ 核心功能优先级

| 优先级 | 功能 | 状态 |
|--------|------|:--:|
| **P0** | 糖糖 JINE 私信聊天 | 可用，偶有对话感泄漏 |
| **P0** | 推博 Feed 时间线 | 可用，每存档独立 |
| **P0** | 戳一戳（F7）更新动态 | 可用，单条释放+自动补池 |

---

## 启动

```bash
conda activate deepseek_v4_api
cd /mnt/e/Desktop/Deepseek_V4_API/amechan-daily
python server.py
# → http://127.0.0.1:8930
```

## 技术栈

| 组件 | 技术 |
|------|------|
| LLM | DeepSeek API (deepseek-v4-pro) |
| 前端 | 纯 HTML/CSS/JS 单文件 (~2400行)，零框架 |
| 后端 | Python `http.server` + `threading` |
| 存储 | `data/feed.json`（服务端共享池）+ `localStorage`（每存档独立） |

## 架构

```
amechan-daily/
  prompts.py        # KAngel/糖糖人设 + JINE_RELEASE/JINE_REPLY/JINE_TEXT + 铁律
  generator.py      # DeepSeek API 调用 + 重试 + JSON 解析
  feed.py           # timeline/hidden_pool/JINE chat CRUD, pop单条释放
  server.py         # HTTP API, 后台线程生成首条, JINE release不再传diary_text
  static/index.html # 前端单文件
```

---

## 当前仍存在的问题

### 问题 1: JINE 对话感泄漏 🔴

F7 release 后糖糖主动发 JINE 消息时，偶尔仍然生成对话式内容（"你在学我说话？""你念经呢？""揍你哦！""才不是特意发给你看的"）。

**已尝试**：
- `JINE_RELEASE_SYSTEM` 完全重写为格式强制模式（5种自言自语格式："发了动态……""喂""好累""想被抱""那条……"）
- 系统+用户 prompt 都明确禁止"你"字和问句
- 用户 prompt 开头第一句就是场景剥夺："这不是对话。阿P不在。你在对空气出声思考。"
- 错误示例直接包含已出现的违规内容

**当前 prompt** (prompts.py):
```python
JINE_RELEASE_SYSTEM = """你是糖糖。阿P的手机黑屏扣在桌上。房间没人。这不是对话——这是你一个人的碎碎念。

正确消息（5选1格式）：
- "发了动态……"开头的自我评价
- "喂""人呢""理我"开头的对空气喊话
- "好累""算了""烦"开头的情绪碎片
- "想被抱""手好冰""今天好冷"开头的身体感受
- "那条……"开头的自我点评

铁律：消息中不能出现"你"字。不能是问句。不能是对话。

致命错误（出现即失败）：
["你看到了？","你在学我说话？","揍你哦！","那是我发的动态","才不是特意发给你看的","你念经呢？"]
"""
```

**怀疑**：DeepSeek 模型对"短信/聊天"格式有强烈的对话先验，temperature 0.5 压不住。可能需要考虑不从 JINE 视角生成，而是先用纯叙述格式生成，再转为 JINE 消息。

### 问题 2: 弹幕偶尔消失 🟡

弹幕滚动一段时间后会全部消失再重新出现。根因是 `refreshDanmaku` 之前会重置所有动画（`animation='none'+reflow`），已改为只刷新内容。但仍需观察稳定性。

### 问题 3: JINE 贴图回复质量不稳定 🟡

贴图走 `/api/jine/send`（Few-Shot prompt），文字走 `/api/jine/text`。历史上下文从 `jineChatMsgs.slice(-8)` 传入。回复质量取决于 DeepSeek API 响应。

---

## 最近重要改动

| 改动 | 文件 |
|------|------|
| `pop_from_pool` 单条释放（不再要求成对） | feed.py |
| JINE_RELEASE prompt 格式强制重写 | prompts.py |
| JINE release 不再传 diary_text（隐私） | server.py |
| 每存档独立 timeline（createdAt 过滤跨槽泄漏） | index.html |
| 删除当前存档自动 reloadFromSlot | index.html |
| JINE tab 只显示互动聊天（不含时间线独白） | index.html |
| 已读标记只对新消息延迟显示 | index.html |
| 弹幕: 72px/3轨/12条/白色彩色/stress联动 | index.html |
| 贴图→send 端点 + 动态打字延迟 | index.html |
| 玩家消息立即持久化到 SaveManager | index.html |
| KAngel 禁提"糖糖"名字 | prompts.py |
| Webcam: 发型稀有池10% + 打字→egosearching | index.html |
| 服务器后台线程生成首条 | server.py |
