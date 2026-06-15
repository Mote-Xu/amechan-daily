# amechan-daily — 超天酱日常推文小站

> DeepSeek V4 驱动的超天酱模拟账号。
> 最后更新：2026-06-16 (v3.0.0)

## 启动

```bash
conda activate deepseek_v4_api
python server.py  # → http://127.0.0.1:8930
```

## 核心功能

| 功能 | 状态 | 备注 |
|------|:--:|------|
| F7 戳一戳 | 🟢 | 水位线后台补池，前端 O(1) 瞬间释放 |
| JINE 聊天 | 🟢 | v3: 微聚合窗口 + 打断重发 + 上下文回复 |
| 推博 Feed | ✅ | 每存档独立+排序 |
| 弹幕 | 🟡 | 72px/3轨/12条 |
| 多存档 | ✅ | 独立 timeline+JINE+stats |

## 架构

### F7 戳一戳
- `feed.py`: `_trigger_background_generate()` 后台线程，剩余对 < 2 时自动补池
- 前端 `doRelease()`: 单 POST，本地缓存渲染，无竞态

### JINE 聊天回复引擎 (v3)

**核心原则**：像真人微信聊天，不是 AI 问答。

**微聚合窗口**：
- 用户发消息 → 开始 300-1200ms 随机窗口
- 持续输入时不断刷新窗口
- 停止输入后立即收集**所有未回复消息** → 一次 API 请求
- 回复插入聊天末尾（不是逐条回复）

**打断重发**：
- API 生成期间用户继续发消息 → abort 当前请求 → 重新开窗 → 合并新旧消息重发

**高频保护**：
- 短时间大量消息仍然只生成一次回复，不会逐条对应

**前端实现**：
- `_scheduleReply(isNewMsg)` — 窗口调度
- `_executeReply()` — 收集所有未回复 → 一次 API → 插入末尾
- `_pendingController` (AbortController) — 打断机制

### 后端
- `/api/jine/chat` 统一端点，无状态（不读写 feed.json）
- `generate_jine_chat(text, sticker, history)` — 接收前端传来的完整 history
- 文字回复温度 0.7，贴图回复温度 0.85

## 已知问题

1. 弹幕偶尔消失
2. 刷新后偶发发不了消息

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/timeline` | 获取时间线 |
| POST | `/api/generate` | 生成新批次 |
| POST | `/api/release` | F7 释放 hidden_pool (O(1)) |
| POST | `/api/jine/chat` | F8 JINE 统一回复 (无状态) |
| GET | `/api/jine/chat` | 获取 JINE 聊天记录 |
| POST | `/api/clear` | 清空数据 |
