# amechan-daily — 超天酱日常推文小站

> DeepSeek V4 驱动的超天酱模拟账号。
> 最后更新：2026-06-16 (v3.3.0)

## 启动

```bash
conda activate deepseek_v4_api
python server.py  # → http://127.0.0.1:8930
```

## 核心功能

| 功能 | 状态 | 要点 |
|------|:--:|------|
| F7 戳一戳 | 🟢 | 水位线后台补池，直接写原槽位防泄漏 |
| JINE 聊天 | 🟢 | 微聚合窗口 + 打断重发 + Menhera 地雷系 prompt |
| 推博 Feed | 🟢 | 24 事件池，日记反文艺碎片化 |
| 弹幕 | 🟢 | 应援 30 + 吐槽 39 |
| 多存档 | ✅ | 独立 timeline+JINE+stats |

## 关键人设（写 prompt 必读）
- 糖糖和阿P**同居**，同一间公寓
- 糖糖是**地雷系（Menhera）**，不是廉价傲娇。硬禁"哼""揍你哦""笨蛋"
- 超天酱公开推文**绝对不能提**阿P/男友/糖糖
- 糖糖日记：碎片化、反文艺、禁"眼泪""梦境""温暖"

## 架构

### JINE 回复引擎 (v3)
- `_scheduleReply()` → 300-1200ms 聚合窗口
- `_executeReply()` → 收集新消息 → 一次 API → 末尾插入
- `_batchSentIdx` 防重复处理
- F7 释放：`_f7Timers` 追踪 + 直接写原槽位防跨存档
- 贴图通信：发实际标签 `[好][嘤嘤]`

### Prompt 结构 (v3.3)
所有 JINE prompt 使用 XML 标签：`<system> <persona> <rules> <negative_rules> <examples>`
- 贴图回复: `JINE_REPLY_SYSTEM` (temp 0.85)
- 文字回复: `JINE_TEXT_REPLY_SYSTEM` (temp 0.85)
- F7 释放: `JINE_RELEASE_SYSTEM` (temp 0.5)

### 后端
- `/api/jine/chat` 统一无状态端点
- `generate_jine_chat(text, sticker, history)`

## 🔴 当前阶段：公共部署
见 `REQUIREMENTS.md` P2 + `GEMINI_PROMPT.md`

## 已知问题
1. 弹幕 CSS 动画偶尔消失
2. 刷新后偶发发不了消息
3. API 端点无鉴权（部署前必须解决）
