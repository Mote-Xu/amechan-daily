# amechan-daily — 超天酱日常推文小站

> DeepSeek V4 驱动的超天酱模拟账号。
> 最后更新：2026-06-16 (v3.2.0)

## 启动

```bash
conda activate deepseek_v4_api
python server.py  # → http://127.0.0.1:8930
```

## 核心功能状态

| 功能 | 状态 | 要点 |
|------|:--:|------|
| F7 戳一戳 | 🟢 | 水位线后台补池，前端 O(1) |
| JINE 聊天 | 🟢 | 微聚合窗口 + 打断重发 + 无状态后端 |
| 推博 Feed | 🟢 | 每存档独立 |
| 弹幕 | 🟡 | 文案池需扩充 |
| 多存档 | ✅ | 独立 timeline+JINE+stats |

## 架构快照

### F7
- `feed.py` `_trigger_background_generate()` → 后台线程
- 前端 `doRelease()` → 单 POST + 本地渲染

### JINE (v3.2)
- `_scheduleReply()` → 300-1200ms 聚合窗口
- `_executeReply()` → 收集新消息 → 一次 API → 末尾插入
- `_batchSentIdx` 防重复处理
- 贴图发实际标签 `[好][嘤嘤]`，不再发 `[...]`
- 已删除硬编码触发词，100% AI 回复

### 后端
- `/api/jine/chat` 统一无状态端点
- `generate_jine_chat(text, sticker, history)` — 接收 history，文字温度 0.7

---

## 🔴 当前阶段：内容质量

架构稳定后，重心转向**内容的趣味性和活人感**。

### 需强化的三个维度

| 维度 | 文件 | 目标 |
|------|------|------|
| JINE 聊天 | `prompts.py` (JINE_REPLY_SYSTEM, JINE_TEXT_REPLY_SYSTEM) | 糖糖风格：傲娇、病娇、撒娇、身体依赖、思维跳跃 |
| 推博 | `prompts.py` (KANGEL_PERSONA, AME_DIARY_PERSONA, get_timeline_prompt) | 表里反差、故事性、真实网红/少女感 |
| 弹幕 | `static/index.html` (DANMAKU_OEN, DANMAKU_TUCAO), `prompts.py` (EVENT_POOL) | 网感、搞笑、更多样 |

### 评判标准
- 糖糖回复是否有"游戏原版"味儿 — 不是客服、不是 ChatGPT
- 推文是否有信息量 — 看完能脑补她今天经历了什么
- 弹幕是否像真实直播间 — 有梗、有节奏、有情绪

## 已知问题
1. 弹幕 CSS 动画偶尔消失
2. 刷新后偶发发不了消息
