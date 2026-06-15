# amechan-daily — 超天酱日常推文小站

> DeepSeek V4 驱动的超天酱模拟账号。
> 最后更新：2026-06-16 (v2.8.0)

## 启动

```bash
conda activate deepseek_v4_api
python server.py  # → http://127.0.0.1:8930
```

## 核心功能

| 功能 | 状态 | 备注 |
|------|:--:|------|
| F7 戳一戳 | 🟢 | v2.8: 水位线后台补池，前端 O(1) 瞬间释放 |
| JINE 聊天 | 🟢 | v2.8: 无状态后端 + 耗时重叠，体感速度翻倍 |
| 推博 Feed | ✅ | 每存档独立+排序 |
| 弹幕 | 🟡 | 72px/3轨/12条 |
| 多存档 | ✅ | 独立 timeline+JINE+stats |

## 架构变更 (v2.8)

### F7 戳一戳
- **后端水位线自动补池**：`pop_from_pool()` 释放后检查剩余对，< 2 对时后台线程静默生成
- **前端 O(1)**：`doRelease()` 只发一个 POST，用本地缓存渲染，消除 `fetchTimeline()` 竞态
- `feed.py` 新增 `_is_generating` 全局锁 + `_trigger_background_generate()` 后台线程

### JINE 聊天
- **统一端点**：`/api/jine/send` + `/api/jine/text` → `/api/jine/chat`
- **后端无状态**：不再读写 `feed.json` 中的 JINE 数据，完全依赖前端传来的 `history`
- **耗时重叠**：`remainWait = max(0, expectedTypingTime - apiDuration)`，API 耗时抵消打字延迟
- **不再 abort**：`_startReplyCycle()` 如果有进行中的请求不取消，标记 `_hasPendingFollowup` 等当前完成后再发起
- **温度调整**：文字回复从 0.85 → 0.7，更好锁住 Few-Shot 风格
- `generator.py` 新增 `generate_jine_chat()` 统一函数

## 已知问题

1. 弹幕偶尔消失
2. 刷新后偶发发不了消息（JINE 状态恢复）

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/timeline` | 获取时间线 |
| POST | `/api/generate` | 生成新批次 |
| POST | `/api/release` | F7 释放 hidden_pool (O(1)) |
| POST | `/api/jine/chat` | F8 JINE 统一回复 (无状态) |
| GET | `/api/jine/chat` | 获取 JINE 聊天记录 |
| POST | `/api/clear` | 清空数据 |
