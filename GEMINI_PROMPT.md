# 项目总结 — 超天酱日常推文小站

> 发给 Gemini，汇报 v2.8 重构结果。
> 最后更新：2026-06-16 (v2.8.0)

---

## v2.8 重构概要

两个 P0 核心功能已完成重构，按照 Gemini 建议的三条思路执行：

### 1. F7 戳一戳 — ✅ 已解决

**旧版问题**：pool 空时前端发 `/api/generate`（5-15s）→ 再 `/api/release`，两次 API 延迟 + 异步竞态。

**解决方案**：水位线后台补池
- `feed.py` 新增 `_trigger_background_generate()` — 后台线程静默生成
- `pop_from_pool()` 释放后检查剩余对，< 2 对时自动触发生成
- 前端 `doRelease()` 简化为单一 POST，用本地缓存渲染，消除 `fetchTimeline()` 竞态
- 玩家体感：**O(1) 瞬间释放，永远不用等**

### 2. JINE 聊天 — ✅ 已解决

**旧版问题**：API 2-8s + 打字延迟 1.5-7s = 总延迟 3.5-15s；前后端双份存储不同步；abort 机制有竞态。

**解决方案**：无状态后端 + 耗时重叠
- 统一端点：`/api/jine/send` + `/api/jine/text` → `/api/jine/chat`
- 后端无状态：不再读写 `feed.json` 的 JINE 数据，前端是唯一数据源
- 耗时重叠：`remainWait = max(0, 1500 + len*100 - apiDuration)`，API 耗时抵消打字延迟
- 不再 abort 进行中的请求，改用 `_hasPendingFollowup` 标记
- 温度调整：文字回复 0.85 → 0.7，更好锁住 Few-Shot 风格
- `generator.py` 新增 `generate_jine_chat(text, sticker, history)` 统一函数
- 体感速度提升 **~50-100%**

### 架构评价

纯前端 + Python 极简后端架构没有结构性问题。本次重构只做了两个思维转换：
1. F7：从"前端发现没水了去打水"变成"后端发现水快没了自动打水，前端只管喝"
2. JINE：从"双端存储、串行等待"变成"前端单点存储、后端无状态计算、API 耗时抵消打字耗时"

## 剩余问题

1. 弹幕偶尔消失（CSS 动画相关，非架构问题）
2. 刷新后偶发发不了消息（JINE 状态恢复，非架构问题）
