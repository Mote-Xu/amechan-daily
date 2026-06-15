# 项目总结 — 超天酱日常推文小站

> 发给 Gemini 的完整项目总结 + 当前卡点。最后更新：2026-06-17 (v2.7.2)

---

## ⚠️ 核心功能优先级（最高优先级）

这个项目的灵魂只有三个功能，它们必须**流畅、稳定、零卡顿**：

| 优先级 | 功能 | 说明 |
|--------|------|------|
| **P0** | 戳一戳（F7）更新动态 | 点击→释放 hidden_pool→Poketter+Diary 同时发布→糖糖来 JINE 轰炸。全程不能卡、不能丢数据 |
| **P0** | 糖糖 JINE 私信聊天 | 玩家发贴图/文字→糖糖回复。必须像真实聊天 App 一样即时响应，不能卡住、不能丢消息 |
| **P0** | 推博 Feed 时间线 | 刷新页面后历史推文必须稳定加载，不能白屏 |

其他功能（Webcam、弹幕、BGM、存档管理）是锦上添花，可以容忍小瑕疵，但**上述三个 P0 功能必须可靠**。

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
| 前端 | 纯 HTML/CSS/JS 单文件 (~2200行)，零框架零构建 |
| 后端 | Python `http.server` + `threading` |
| 存储 | `data/feed.json`（服务端）+ `localStorage`（多存档） |

## 架构

```
amechan-daily/
  prompts.py        # 系统提示词 (JINE_RELEASE/JINE_REPLY/JINE_TEXT + 铁律)
  generator.py      # DeepSeek API 调用 + 重试 + JSON 解析
  feed.py           # timeline/hidden_pool/JINE chat CRUD
  server.py         # HTTP API (GET /api/timeline, POST /api/release, /api/jine/...)
  static/index.html # 前端单文件
```

---

## 当前三个顽固问题

### 问题 1: 刷新页面后推博不加载

**现象**：`python server.py` 正常启动，浏览器刷新 `localhost:8930`，推博区域空白或长时间显示"连接中"。

**已尝试的修复**：
- `fetchTimeline` 加了 `console.log` 追踪
- 失败时指数退避重试（3s/6s/9s...）
- 首次空数据后 3s/7s/12s 快速轮询
- 后端首条生成从同步阻塞改为 `threading.Thread` 后台生成，服务器立刻监听

**关键代码** — `fetchTimeline` (index.html ~L1712)：
```js
var _fetchRetries = 0;
function fetchTimeline() {
    if (firstLoad && _fetchRetries === 0) {
        CONTAINER.innerHTML = '...连接超天酱中...';
    }
    fetch(API + '/api/timeline').then(function(r) { return r.json(); }).then(function(data) {
        _fetchRetries = 0;
        cachedTimeline = data.timeline || [];
        if (firstLoad) { renderFromCache(); firstLoad = false; return; }
        var hasNew = cachedTimeline.some(function(e) { return !knownBatches[e.batch_id]; });
        if (hasNew) { /* render */ }
    }).catch(function(err) {
        // static fallback → data/feed.json → retry with backoff
        _fetchRetries++;
        var delay = Math.min(3000 * _fetchRetries, 15000);
        setTimeout(function() { firstLoad = true; fetchTimeline(); }, delay);
    });
}
// Fast poll if feed empty:
if (cachedTimeline.length === 0) {
    setTimeout(function() { if (cachedTimeline.length === 0) fetchTimeline(); }, 3000);
    setTimeout(function() { if (cachedTimeline.length === 0) fetchTimeline(); }, 7000);
    setTimeout(function() { if (cachedTimeline.length === 0) fetchTimeline(); }, 12000);
}
```

**关键代码** — server.py 启动 (`main()`):
```python
server = HTTPServer((HOST, PORT), AmechanHandler)
server.allow_reuse_address = True
# 后台生成，不阻塞监听
import threading
if feed_count() == 0:
    def _initial_generate():
        try: generate_and_save()
        except Exception as e: print(f"生成失败: {e}")
    threading.Thread(target=_initial_generate, daemon=True).start()
server.serve_forever()
```

**怀疑**：`renderFeed()` 里 ALL tab 对 jine-layer 条目的处理、`renderFromCache()` 的过滤逻辑、或者 CSS 让内容不可见（win95-body overflow/padding）。

---

### 问题 2: JINE 发送文字后卡住

**现象**：有时发完文字后整个 JINE 无法再发任何消息，贴图也点不了。

**已尝试的修复**：
- 移除了全局 `jineSending` 锁 ← 现在允许并发
- 加了 `AbortController` 15s 超时 + 20s 安全解锁定时器 ← 防 fetch 永久挂起
- 改为回复队列 `_startReplyCycle()`：多条玩家消息合并成一次 API 调用

**关键代码** — `_startReplyCycle` (index.html ~L1909)：
```js
var _replyPending = false;
var _pendingController = null;
var _pendingMsgIdx = -1;

function _startReplyCycle() {
    if (_replyPending) return;
    _replyPending = true;
    _pendingMsgIdx = jineChatMsgs.length;

    // 收集所有未回复的玩家消息
    var texts = [];
    for (var i = jineChatMsgs.length - 1; i >= 0; i--) {
        var m = jineChatMsgs[i];
        if (m.reply) break;
        if (m.player_text) texts.unshift(m.player_text);
        if (m.sticker) texts.unshift('[' + (findSticker(m.sticker)||{}).label || '贴图' + ']');
    }
    var combined = texts.join(' | ') || '...';
    if (texts.length === 0) { _replyPending = false; return; }

    // typing indicator + API call with 20s timeout
    _pendingController = new AbortController();
    var fetchTimeout = setTimeout(function() { if (_pendingController) _pendingController.abort(); }, 20000);

    fetch(API + '/api/jine/text', {
        method: 'POST',
        body: JSON.stringify({text: combined}),
        signal: _pendingController.signal
    }).then(...).catch(function(err) {
        // fallback reply
        _replyPending = false; _pendingController = null;
        // 检查是否有新消息堆积 → 自动下一轮
        if (hasUnreplied) { startAmeResponse(); _startReplyCycle(); }
    });
}
```

**关键代码** — `sendText` (index.html ~L2100)：
```js
window.sendText = function() {
    var input = document.getElementById('jine-text-input');
    if (!input) return;
    var text = input.value.trim();
    if (!text) return;
    input.value = '';
    startAmeResponse();  // webcam → egosearching

    var trigger = checkTriggerWords(text);
    if (trigger) {
        // 本地即时回复，不走 API
        jineChatMsgs.push({..., reply: trigger.reply, ...});
        return;
    }
    jineChatMsgs.push({ time: timeStr, player_text: text, reply: '', recall: false });
    _startReplyCycle();
};
```

**怀疑**：
- `_replyPending` 在某些错误路径没重置 → 后续调用全在 `if (_replyPending) return` 被拦截
- `_pendingController.abort()` 后 `.catch()` 没正确清理状态
- `sendSticker` 也走 `_startReplyCycle()`，但贴图用的是 `/api/jine/text` 端点（应该用 `/api/jine/send`）
- `checkTriggerWords` 函数之前从未定义（刚补上），之前调用时报 TypeError，可能导致 `sendText` 静默失败

---

### 问题 3: 弹幕看不到

**现象**：弹幕区域（直播栏下方）始终空白，看不到任何滚动弹幕。

**已尝试的修复**：
- 从 `transform: translateX(100vw)` 改为 `left` 动画（`from left:100% to left:-300px`）
- 弹幕数量 5→8，高度 34→48px，延迟 0-10s→0-4s，前2条几乎0延迟
- 栏加背景色 `rgba(0,0,0,0.35)` + 顶部分割线

**关键代码** — 弹幕 CSS (index.html ~L735)：
```css
.danmaku-bar { height:48px; overflow:hidden; position:relative; background:rgba(0,0,0,0.35); }
.danmaku-wrap { position:absolute; white-space:nowrap; display:flex; left:100%; animation:scrollR 16s linear infinite; }
@keyframes scrollR { from { left:100%; } to { left:-300px; } }
```

**关键代码** — 弹幕 JS 初始化 (index.html ~L1465)：
```js
function initDanmaku() {
    var bar = document.getElementById('danmaku-bar');
    // 8条弹幕，等分高度
    for (var i = 0; i < DANMAKU_COUNT; i++) {
        var wrap = document.createElement('span');
        wrap.className = 'danmaku-wrap';
        wrap.style.top = positions[i] + 'px';
        wrap.style.animation = 'scrollR linear infinite ' + (12 + Math.random() * 8) + 's';
        wrap.style.animationDelay = (i < 2 ? Math.random() * 1.5 : Math.random() * 4) + 's';
        spawnDanmakuContent(wrap);
        bar.appendChild(wrap);
    }
}
```

**怀疑**：
- `danmaku-bar` 的 `overflow:hidden` + `position:relative` 裁剪了绝对定位的子元素
- `left:100%` 动画起点是否被父容器宽度正确计算
- 弹幕可能在 DOM 里但在视口外被裁剪（父容器 `win95-outer` 有 `overflow:hidden`）
- `spawnDanmakuContent` 创建的 span 可能没有实际文本内容

---

## 其他可能需要关注的问题

### Webcam 状态切换
- 点击 titlebar 打开菜单后 `click` 事件冒泡到 `document` 立即关闭 → 已加 `e.stopPropagation()` 修复
- 切状态时 canvas 先清空再等图片加载 → 已改为先等帧加载再绘制
- 发型四种 (hair_*) 太频繁 → 已拆为稀有池 (10%)

### JINE 回复质量
- "不准学我说话"等 meta 评论 → 已加严禁规则
- "揍你哦"高频出现 → Few-Shot 移除 + 频率限制

---

## 请 Gemini 给方向

三个问题都是前端 DOM/CSS/异步时序问题。请：
1. 先分析最可能的根因（不是猜，是结合代码逻辑推理）
2. 给出最小改动修复方案
3. 如果某个问题需要重写某个模块，说明原因
