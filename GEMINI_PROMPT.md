# 项目总结 — 超天酱日常推文小站

> 发给 Gemini，重点求助两个核心功能的优化。
> 最后更新：2026-06-16 (v2.7.2)

---

## 求助重点

请严格审查以下两个核心功能的**准确性、稳定性、响应速度**，指出所有潜在问题和优化方案：

| 功能 | 目标 |
|------|------|
| **戳一戳 (F7)** | 每次点击稳定释放 1 Poketter + 1 Diary，立刻渲染；pool 空时自动补池不卡 |
| **JINE 聊天** | 发贴图/文字即时响应，回复质量高，不卡顿不丢消息，刷新后恢复 |

---

## 功能 1: 戳一戳 (F7) — 完整代码路径

### 前端 doRelease (index.html)
```js
window.doRelease = function() {
    if (isStaticMode) return;
    var btn = document.getElementById('f7-btn');
    btn.classList.add('shaking'); btn.textContent = '...'; btn.disabled = true;
    fetch(API + '/api/release', { method: 'POST' })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.ok) {
            var entries = data.entries || [];
            for (var n = 0; n < entries.length; n++) {
                SaveManager.incrementFeedCursor();
                SaveManager.addReleasedEntry(entries[n]);
            }
            updateSaveIndicator();
            fetchTimeline();  // async re-fetch to sync with server
            // JINE follow-up messages appear with staggered setTimeout...
        } else {
            // Pool empty → trigger regeneration, then retry release
            fetch(API + '/api/generate', { method: 'POST', body: '{}' })
            .then(function() {
                fetchTimeline();
                fetch(API + '/api/release', { method: 'POST' })
                .then(function(r) { return r.json(); })
                .then(function(d2) {
                    // same save+render logic
                });
            });
        }
    });
};
```

### 后端 /api/release (server.py)
```python
elif path == "/api/release":
    entries = pop_from_pool()
    if entries:
        # Success: 2 entries (poketter + diary)
        poke_text = next((e['text'][:40] for e in entries if e['layer'] == 'poketter'), '')
        msgs = generate_jine_release_msgs(poke_text, '', count=random.randint(2,5))
        # Save JINE msgs to feed.json, return entries + jine_msgs
        self._send_json({"ok": True, "entries": entries, ...})
    else:
        # Pool empty/imbalanced → frontend triggers regeneration
        self._send_json({"ok": False, ...})  # ← 注意: 返回 ok:False!
```

### 后端 pop_from_pool (feed.py)
```python
def pop_from_pool():
    poke_item = _find_one("poketter")
    diary_item = _find_one("diary")
    if poke_item and diary_item:
        entries.append(_pop_it(poke_item))
        entries.append(_pop_it(diary_item))
        return entries  # 2 items
    return []  # 不平衡或空 → 触发重新生成
```

### 后端 generate_and_save (generator.py) — DeepSeek API 调用
```python
def generate_and_save(topic=None):
    data = generate_timeline(topic)  # single API call, ~5-15s
    save_timeline(data["timeline"], event)
    pool = data.get("hidden_pool", [])
    if pool: save_hidden_pool(pool)
    return data
```

### 🔴 已知问题
1. **doRelease 和 fetchTimeline 异步竞态**: `addReleasedEntry` 保存到 localStorage → `fetchTimeline()` 异步从服务器拉数据 → `SaveManager.mergeTimeline()` 合并 → `cachedTimeline = SaveManager.getTimeline()`。两个异步路径可能互相覆盖。
2. **pool 空时两次 API 调用**: 先 `/api/generate`（5-15s DeepSeek）再 `/api/release`，用户等两次 API 延迟。
3. **后端 regeneration 路径**: 服务端 `/api/release` 返回 `ok: False`，但前端期望 `data.ok` 为 true 的 entries。空 pool 时走了两趟网络请求。

---

## 功能 2: JINE 聊天 — 完整代码路径

### 前端 sendText (index.html)
```js
window.sendText = function() {
    try {
        var input = document.getElementById('jine-text-input');
        if (!input) return;
        var text = input.value.trim();
        if (!text) return;
        input.value = '';
        startAmeResponse();  // webcam → egosearching

        // Trigger words: instant local reply
        var trigger = null;
        try { trigger = checkTriggerWords(text); } catch(e) {}
        if (trigger) {
            jineChatMsgs.push({ time: timeStr, player_text: text, reply: trigger.reply, ... });
            SaveManager.addJineMessage(last);
            return;  // no API call
        }

        var playerMsg = { time: timeStr, player_text: text, reply: '', recall: false };
        jineChatMsgs.push(playerMsg);
        SaveManager.addJineMessage(playerMsg);
        if (ACTIVE_TAB === 'jine') renderJineChatMsgs();
        _startReplyCycle();  // triggers API call
    } catch(e) { console.error('[sendText] crashed:', e); }
};
```

### 前端 sendSticker (index.html)
```js
function sendSticker(stickerId) {
    try {
        startAmeResponse();
        var sticker = STICKERS.find(...);
        if (!sticker) { endAmeResponse(); return; }
        var stickerMsg = { time: timeStr, sticker: stickerId, reply: '', recall: false };
        jineChatMsgs.push(stickerMsg);
        SaveManager.addJineMessage(stickerMsg);
        if (ACTIVE_TAB === 'jine') renderJineChatMsgs();
        _startReplyCycle();
    } catch(e) { console.error('[sendSticker] crashed:', e); }
};
```

### 前端 _startReplyCycle — 回复队列 (index.html)
```js
function _startReplyCycle() {
    if (_replyPending && _pendingController) {
        _pendingController.abort();  // cancel old, batch with new
        _replyPending = false; _pendingController = null;
    }
    if (_replyPending) return;
    _replyPending = true;

    var replyIdx = jineChatMsgs.length;
    // Collect ALL unreplied messages
    var texts = [], lastSticker = null;
    for (var i = jineChatMsgs.length - 1; i >= 0; i--) {
        var m = jineChatMsgs[i];
        if (m.reply) break;
        if (m.player_text) texts.unshift(m.player_text);
        if (m.sticker) { texts.unshift('[...]'); lastSticker = m.sticker; }
    }

    // Route: pure stickers → /api/jine/send (Few-Shot), text → /api/jine/text
    var isPureSticker = lastSticker && texts.every(function(t){ return t.charAt(0)==='['; });
    var endpoint = isPureSticker ? '/api/jine/send' : '/api/jine/text';
    var body = isPureSticker
        ? JSON.stringify({sticker: lastSticker, history: jineChatMsgs.slice(-8)})
        : JSON.stringify({text: texts.join(' | '), history: jineChatMsgs.slice(-8)});

    // fetch with 20s timeout
    fetch(API + endpoint, { method:'POST', body:body, signal:_pendingController.signal })
    .then(function(r){ return r.json(); })
    .then(function(data){
        _replyPending = false; _pendingController = null;
        // Dynamic delay: 1.5s + 120ms/char, max 7s
        var typingTime = Math.min(1500 + (data.reply||'').length * 120, 7000);
        var remainWait = Math.max(800, typingTime - (Date.now() - cycleStart));
        setTimeout(function(){
            // Insert reply after last pending msg
            jineChatMsgs.splice(replyIdx, 0, replyMsg);
            SaveManager.addJineMessage(replyMsg);
            renderJineChatMsgs();
            // Check for more unreplied → another cycle
        }, remainWait);
    }).catch(function(err){
        if (err.name === 'AbortError') return; // intentional cancel
        // fallback reply
    });
}
```

### 后端 /api/jine/send 和 /api/jine/text (server.py → generator.py)
```python
# /api/jine/send → generate_jine_reply(sticker) → JINE_REPLY_SYSTEM + Few-Shot
# /api/jine/text → generate_jine_text_reply(text) → JINE_TEXT_REPLY_SYSTEM
# Both use DeepSeek API, temperature 0.85, ~2-8s response time
```

### 🔴 已知问题
1. **回复速度**: DeepSeek API 2-8s + 动态打字延迟 1.5-7s = 总等待 3.5-15s。太慢。
2. **abort 后 catch 残留**: abort 旧请求 → `.catch()` 触发 → 虽然有 AbortError 检查，但 `_replyPending` 的释放时机仍有竞态风险。
3. **贴图回复走 text 端点**: 混合消息（文字+贴图）走 `/api/jine/text`，丢失 Few-Shot。
4. **对话感泄漏**: 模型偶尔生成"你在学我说话""揍你哦"等 meta 评论。系统 prompt + 用户 prompt 都已加严禁规则，但仍偶发。
5. **刷新后 jineChatMsgs 恢复**: 从 SaveManager 加载，但回复队列状态 (_replyPending, _pendingController) 丢失——刷新时若有进行中的请求，回复会丢失。
6. **SaveManager 与服务器不同步**: 玩家消息存 localStorage，回复存 localStorage。但服务器 `feed.json` 里的 `jine_chat` 是另一份副本。两边的 JINE 聊天记录可能不一致。

---

## 请 Gemini 审查

1. **戳一戳**: 异步流程有没有竞态？pool regenerate 能否合并成一次 API 调用？能否在服务端直接完成 regenerate+release 而不需要前端发两次请求？

2. **JINE 聊天**: `_startReplyCycle` 的 abort+重发机制有没有死锁风险？如何降低感知延迟（预取？流式？）？如何彻底杜绝对话感泄漏？

3. **整体**: 这个单文件 HTML + Python http.server 架构在稳定性和响应速度上有没有结构性问题？
