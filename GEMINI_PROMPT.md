# 项目总结 — 超天酱日常推文小站

> 发给 Gemini 的完整项目总结 + 当前卡点。最后更新：2026-06-17 (v2.7.2)

---

## ⚠️ 核心功能优先级

| 优先级 | 功能 | 说明 |
|--------|------|------|
| **P0** | 糖糖 JINE 私信聊天 | 玩家发贴图/文字→糖糖回复。必须流畅、自然、高质量 |
| **P0** | 推博 Feed 时间线 | 刷新后历史推文稳定加载 |
| **P0** | 戳一戳（F7）更新动态 | 释放 hidden_pool→JINE 轰炸 |

---

## 上次 Gemini 诊断后已修复

上次你诊断的三个问题已按你的方案修复：

| 问题 | 根因 | 修复 |
|------|------|------|
| 刷新推博不加载 | `firstLoad` 在空数据时被消费 | 空数据继续轮询，不设 `firstLoad=false` |
| JINE 发文字卡住 | `_replyPending` 锁未释放 + `checkTriggerWords` 抛 TypeError | 锁移到 `.then()` 第一行释放；try/catch 保护 |
| 弹幕看不到 | `animation` 简写属性顺序非法（duration 在 linear 之后） | 改用 `animationDuration`/`animationDelay` 单独设 |

---

## 当前仍存在的问题

### 问题 1: 弹幕仍然看不到 🔴

`animationDuration` 修复后弹幕依然不显示。当前完整弹幕代码：

**CSS:**
```css
.danmaku-bar { height:48px; overflow:hidden; position:relative; background:rgba(0,0,0,0.35); }
.danmaku-wrap { position:absolute; white-space:nowrap; display:flex; left:100%; animation:scrollR 16s linear infinite; }
@keyframes scrollR { from { left:100%; } to { left:-300px; } }
```

**JS 初始化 (initDanmaku):**
```js
function initDanmaku() {
    var bar = document.getElementById('danmaku-bar');
    for (var i = 0; i < 8; i++) {
        var wrap = document.createElement('span');
        wrap.className = 'danmaku-wrap';
        wrap.style.top = positions[i] + 'px';
        wrap.style.animationDuration = (12 + Math.random() * 8) + 's';
        wrap.style.animationDelay = (i < 2 ? Math.random() * 1.5 : Math.random() * 4) + 's';
        spawnDanmakuContent(wrap);  // creates <span class="danmaku-text fan/hate">text</span>
        bar.appendChild(wrap);
    }
}
```

**HTML 位置:**
```html
<div class="danmaku-bar" id="danmaku-bar"></div>
<!-- 在 webcam-container (position:fixed) 和 desktop-icons 之间 -->
```

**已排除的可能原因**：animation 属性顺序、延迟过长、数量不足、bar 无背景。怀疑是 `overflow:hidden` + `position:relative` 裁剪，或者父容器 `win95-outer` 的 `overflow:hidden` 遮挡，或者 `left:100%` 计算不正确。

---

### 问题 2: JINE 贴图回复质量低 🟡

贴图（如 [好]、[太强了]）触发回复时，质量明显低于文字消息。当前逻辑：

```js
// _startReplyCycle 中的路由逻辑
var isPureSticker = lastSticker && texts.every(function(t) { return t.charAt(0) === '['; });
var endpoint = isPureSticker ? '/api/jine/send' : '/api/jine/text';
var body = isPureSticker
    ? JSON.stringify({sticker: lastSticker})
    : JSON.stringify({text: texts.join(' | ')});
```

纯贴图 → `/api/jine/send`（JINE_REPLY_SYSTEM prompt，有 Few-Shot），否则 → `/api/jine/text`（JINE_TEXT_REPLY_SYSTEM prompt）。

但回复质量依然不稳定。`JINE_REPLY_SYSTEM` prompt 已经包含了详细的 Few-Shot 示例和严禁规则（见下方后端代码）。

---

### 问题 3: 回复速度太快，不自然 🟡

已加最小延迟 2.5s（`Date.now() - cycleStart`），但用户仍觉太快。可能需要更长的可变延迟 + 打字指示器分段显示。

---

## 后端 JINE Prompt（供参考）

**JINE_REPLY_SYSTEM** (prompts.py，贴图回复):
```python
JINE_REPLY_SYSTEM = """你是「糖糖」，正在用手机即时通讯 App「JINE」给阿P发消息。
阿P刚给你发了一个表情包，请你立刻回复。

## 🚫 严禁
- 禁止评论聊天本身："不准学我说话""你复读"等
- 禁止高频复用同一句："揍你哦"最多每5条出现1次
- 禁止预设阿P行为："你连赞都不点""你都不回我"
- 禁止"已读"式回复："已读""看到了"

## Few-Shot 示例 (游戏原版台词)
玩家发送：[好] 贴图
文字："嘿嘿！就是这样" / "你就这张嘴甜" / "你懂就好"
贴图：[stamp: ame_smile] 或 [stamp: cat_good]

玩家发送：[太强了] 贴图
文字："你就这张嘴甜" / "一丁点诚意都感受不到" / "讨厌你的回答！"
贴图：[stamp: ame_tsun]
... (每个贴图都有)
"""
```

完整 prompt 在 `prompts.py` 的 `JINE_REPLY_SYSTEM` 和 `JINE_TEXT_REPLY_SYSTEM`。

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
| 前端 | 纯 HTML/CSS/JS 单文件 (~2300行)，零框架 |
| 后端 | Python `http.server` + `threading` |
| 存储 | `data/feed.json` + `localStorage` |
