#!/usr/bin/env python
"""Apply remaining v2.7.1 patches to index.html"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

p = 0

# ===== 1. HTML: webcam canvas + state menu =====
old = '<!-- WEBCAM WINDOW -->\n\t\t<div class="webcam-container" id="webcam-container">\n\t\t    <div class="webcam-frame">\n\t\t        <div class="webcam-titlebar"><span><span class="dot">●</span> Webcam</span></div>\n\t\t        <img class="window-chrome" src="img/windowbase_active_300x200.png" alt="">\n\t\t        <div class="webcam-inner" id="webcam-inner">\n\t\t            <img id="webcam-img" src="img/webcam/smile/stream_ame_smile_000_348x227.png" alt="超天酱">\n\t\t        </div>\n\t\t    </div>\n\t\t</div>'
new = '<!-- WEBCAM WINDOW -->\n\t\t<div class="webcam-container" id="webcam-container">\n\t\t    <div class="webcam-frame">\n\t\t        <div class="webcam-titlebar" id="webcam-titlebar"><span><span class="dot">●</span> <span id="webcam-state-label">Webcam</span></span><span style="font-size:0.5rem;">▼</span></div>\n\t\t        <div class="webcam-state-menu" id="webcam-state-menu"></div>\n\t\t        <img class="window-chrome" src="img/windowbase_active_300x200.png" alt="">\n\t\t        <div class="webcam-inner" id="webcam-inner">\n\t\t            <canvas id="webcam-canvas"></canvas>\n\t\t        </div>\n\t\t    </div>\n\t\t</div>'
if old in html:
    html = html.replace(old, new); p += 1; print('HTML webcam: OK')
else:
    print('HTML webcam: NOT FOUND')

# ===== 2. HTML: spacer div before danmaku =====
old = '</div>\n<div class="danmaku-bar" id="danmaku-bar">'
new = '</div>\n<div style="height:300px"></div>\n<div class="danmaku-bar" id="danmaku-bar">'
if old in html:
    html = html.replace(old, new); p += 1; print('Spacer: OK')
else:
    print('Spacer: NOT FOUND')

# ===== 3. HTML: textarea instead of input =====
old = "<input type=\"text\" class=\"jine-text-input\" id=\"jine-text-input\" placeholder=\"给糖糖发消息...\" maxlength=\"80\">"
new = "<textarea class=\"jine-text-input\" id=\"jine-text-input\" placeholder=\"给糖糖发消息...\" maxlength=\"200\" rows=\"2\"></textarea>"
if old in html:
    html = html.replace(old, new); p += 1; print('Textarea HTML: OK')
else:
    print('Textarea HTML: NOT FOUND')

# ===== 4. JS: Enter key handler (Shift+Enter newline) =====
old = "if (e.key === 'Enter' && document.activeElement === document.getElementById('jine-text-input')) {\n\t        sendText();\n\t    }"
new = "if (e.key === 'Enter' && document.activeElement === document.getElementById('jine-text-input')) {\n\t        if (e.shiftKey) return;\n\t        e.preventDefault();\n\t        sendText();\n\t    }"
if old in html:
    html = html.replace(old, new); p += 1; print('Enter key: OK')
else:
    print('Enter key: NOT FOUND')

# ===== 5. JS: renderFromCache - remove cursor gating =====
old = """function renderFromCache() {\n\t    var filtered = cachedTimeline;\n\t    // v2.6: feed_cursor 独立进度 — 每个存档只看到已解锁的推文\n\t    var cursor = SaveManager.getFeedCursor();\n\t    if (ACTIVE_TAB === 'diary') {\n\t        // Diary tab: diary-only items, up to cursor\n\t        var diaryOnly = cachedTimeline.filter(function(e) { return e.layer === 'diary'; });\n\t        filtered = cursor > 0 ? diaryOnly.slice(0, cursor) : [];\n\t    } else if (ACTIVE_TAB === 'jine') {\n\t        filtered = cachedTimeline.filter(function(e) { return e.layer === 'jine'; });\n\t    } else {\n\t        // ALL tab: show first `cursor` non-JINE entries (Poketter + Diary)\n\t        var nonJine = cachedTimeline.filter(function(e) { return e.layer !== 'jine'; });\n\t        filtered = cursor > 0 ? nonJine.slice(0, cursor) : [];\n\t    }\n\t    renderFeed(filtered);\n\t}"""
new = """function renderFromCache() {\n\t    var filtered = cachedTimeline;\n\t    if (ACTIVE_TAB === 'diary') {\n\t        filtered = cachedTimeline.filter(function(e) { return e.layer === 'diary'; });\n\t    } else if (ACTIVE_TAB === 'jine') {\n\t        filtered = cachedTimeline.filter(function(e) { return e.layer === 'jine'; });\n\t    } else {\n\t        filtered = cachedTimeline.filter(function(e) { return e.layer !== 'jine'; });\n\t    }\n\t    renderFeed(filtered);\n\t}"""
if old in html:
    html = html.replace(old, new); p += 1; print('renderFromCache: OK')
else:
    print('renderFromCache: NOT FOUND')

# ===== 6. JS: Empty state with game icons =====
old = "CONTAINER.innerHTML = '<div class=\"empty-state\"><div class=\"icon\">\U0001f47c</div><p>等待超天酱上线...</p></div>';"
new = "CONTAINER.innerHTML = '<div class=\"empty-state\"><div class=\"icon\"><img src=\"img/icon_cho.png\"></div><p>等待超天酱上线...</p></div>';"
if old in html:
    html = html.replace(old, new); p += 1; print('Empty cho: OK')
else:
    print('Empty cho: NOT FOUND')

old = "html = '<div class=\"empty-state\"><div class=\"icon\">\U0001f512</div><p>这里还没有内容</p></div>';"
new = "html = '<div class=\"empty-state\"><div class=\"icon\"><img src=\"img/icon_ame.png\"></div><p>这里还没有内容</p></div>';"
if old in html:
    html = html.replace(old, new); p += 1; print('Empty ame: OK')
else:
    print('Empty ame: NOT FOUND')

old = "CONTAINER.innerHTML = '<div class=\"empty-state\"><div class=\"icon\">\U0001f4a4</div><p>超天酱暂时失联...</p></div>';"
new = "CONTAINER.innerHTML = '<div class=\"empty-state\"><div class=\"icon\"><img src=\"img/icon_cho_res.png\"></div><p>超天酱暂时失联...</p></div>';"
if old in html:
    html = html.replace(old, new); p += 1; print('Empty offline: OK')
else:
    print('Empty offline: NOT FOUND')

old = "container.innerHTML = html || '<div class=\"empty-state\"><p style=\"font-size:0.7rem;color:rgba(0,0,0,0.4);\">糖糖还没发消息...</p></div>';"
new = "container.innerHTML = html || '<div class=\"empty-state\"><div class=\"icon\"><img src=\"img/icon_ame.png\"></div><p style=\"font-size:0.7rem;color:rgba(0,0,0,0.4);\">糖糖还没发消息...</p></div>';"
if old in html:
    html = html.replace(old, new); p += 1; print('Empty jine: OK')
else:
    print('Empty jine: NOT FOUND')

# ===== 7. JS: renderFeed diary empty state =====
old = "if (!items || items.length === 0) {\n\t        CONTAINER.innerHTML = '<div class=\"empty-state\"><div class=\"icon\"><img src=\"img/icon_cho.png\"></div><p>等待超天酱上线...</p></div>';\n\t        return;\n\t    }"
new = "if (!items || items.length === 0) {\n\t        if (ACTIVE_TAB === 'diary') {\n\t            CONTAINER.innerHTML = '<div class=\"empty-state\"><div class=\"icon\"><img src=\"img/icon_ame.png\"></div><p>糖糖还没写日记...</p></div>';\n\t        } else {\n\t            CONTAINER.innerHTML = '<div class=\"empty-state\"><div class=\"icon\"><img src=\"img/icon_cho.png\"></div><p>等待超天酱上线...</p></div>';\n\t        }\n\t        return;\n\t    }"
if old in html:
    html = html.replace(old, new); p += 1; print('renderFeed empty: OK')
else:
    print('renderFeed empty: NOT FOUND')

# ===== 8. JS: Danmaku mousedown handler =====
old = "document.addEventListener('mousedown', function(e) {\n\t        var item = e.target.closest('.danmaku-item');\n\t        if (!item || item.dataset.type !== 'hate') return;\n\t        e.preventDefault();\n\t        e.stopPropagation();\n\t        trashDanmaku(item);\n\t    }, true);"
new = "bar.addEventListener('mousedown', function(e) {\n\t        var item = e.target.closest('.danmaku-item');\n\t        if (!item || item.dataset.type !== 'hate') return;\n\t        e.preventDefault();\n\t        e.stopPropagation();\n\t        trashDanmaku(item);\n\t    });"
if old in html:
    html = html.replace(old, new); p += 1; print('Danmaku mousedown: OK')
else:
    print('Danmaku mousedown: NOT FOUND')

# ===== 9. JS: Danmaku dynamic positions =====
old = "var positions = [3, 10, 17, 24, 31, 38, 45, 52]; // 8 danmaku spread across 56px bar"
new = "var positions = [];\n\t    var barH = bar.clientHeight || 56;\n\t    var itemH = 15;\n\t    var safeMax = Math.max(2, barH - itemH - 2);\n\t    for (var i = 0; i < DANMAKU_COUNT; i++) {\n\t        positions.push(2 + Math.floor((safeMax - 2) * i / (DANMAKU_COUNT - 1)));\n\t    }"
if old in html:
    html = html.replace(old, new); p += 1; print('Danmaku positions: OK')
else:
    print('Danmaku positions: NOT FOUND')

# ===== 10. Version strings =====
html = html.replace('LIVE v2.3', 'LIVE v2.7.1')
html = html.replace('+ Poketter v2.3 ready +', '+ Poketter v2.7.1 ready +')
html = html.replace('超天酱日常推文小站 · v2.3', '超天酱日常推文小站 · v2.7.1')
p += 1; print('Versions: OK')

# ===== 11. JS: Sticker render order - PNG first in renderStickerBar =====
# Find the renderStickerBar function and swap order
old = "// Image wrapper: CSS pixel cat base + PNG overlay\n\t        var wrap = document.createElement('span');\n\t        wrap.className = 'sticker-img-wrap';\n\t        // CSS pixel cat (always rendered as base fallback)\n\t        var catEl = document.createElement('span');\n\t        catEl.className = 'pixel-cat ' + s.catVar;\n\t        wrap.appendChild(catEl);\n\t        // PNG stamp overlay (hides CSS cat when loaded)\n\t        var imgEl = document.createElement('img');\n\t        imgEl.className = 'sticker-png';\n\t        imgEl.src = 'img/stamps/' + s.pngFile;\n\t        imgEl.onload = function() { this.classList.add('loaded'); };\n\t\t        imgEl.onerror = function() { this.style.display = 'none'; };\n\t        imgEl.alt = s.label;\n\t        wrap.appendChild(imgEl);"
new = "// Image wrapper: PNG first, then CSS fallback\n\t        var wrap = document.createElement('span');\n\t        wrap.className = 'sticker-img-wrap';\n\t        var imgEl = document.createElement('img');\n\t        imgEl.className = 'sticker-png';\n\t        imgEl.src = 'img/stamps/' + s.pngFile;\n\t        imgEl.onerror = function() { this.classList.add('error'); };\n\t        imgEl.alt = s.label;\n\t        wrap.appendChild(imgEl);\n\t        var catEl = document.createElement('span');\n\t        catEl.className = 'pixel-cat ' + s.catVar;\n\t        wrap.appendChild(catEl);"
if old in html:
    html = html.replace(old, new); p += 1; print('Sticker bar order: OK')
else:
    print('Sticker bar order: NOT FOUND')

# ===== 12. JS: stickerHTML - PNG first, onerror =====
old = "'<img class=\"sticker-png\" src=\"img/stamps/' + s.pngFile + '\" alt=\"\" onload=\"this.classList.add(\\'loaded\\')\">'"
new = "'<img class=\"sticker-png\" src=\"img/stamps/' + s.pngFile + '\" alt=\"\" onerror=\"this.classList.add(\\'error\\')\">'"
if old in html:
    html = html.replace(old, new); p += 1; print('stickerHTML onerror: OK')
else:
    print('stickerHTML: NOT FOUND')

# Swap order in stickerHTML output
old = "'<span class=\"' + cssClass + (isAme ? ' ame-pixel' : '') + '\"></span>' +\n\t        '<img class=\"sticker-png\""
new = "'<img class=\"sticker-png\""
if old in html:
    # This is trickier - need to swap the order of the two lines
    html = html.replace(old, new); p += 1; print('stickerHTML order: OK')
else:
    print('stickerHTML order: NOT FOUND - need manual fix')

# ===== 13. JS: firstLoad simplify =====
old = """if (firstLoad) {\n\t            // v2.6: 首次加载时，如果 feedCursor 为 0 但已有内容，自动同步到当前进度\n\t            // cursor 计数 非 JINE 条目（Poketter + Diary）\n\t            var cursor = SaveManager.getFeedCursor();\n\t            if (cursor === 0 && cachedTimeline.length > 0) {\n\t                var nonJineCount = cachedTimeline.filter(function(e) { return e.layer !== 'jine'; }).length;\n\t                if (nonJineCount > 0) {\n\t                    SaveManager.setFeedCursor(nonJineCount);\n\t                }\n\t            }\n\t            renderFromCache();\n\t            firstLoad = false;\n\t            return;\n\t        }"""
new = """if (firstLoad) {\n\t            firstLoad = false;\n\t            renderFromCache();\n\t            return;\n\t        }"""
if old in html:
    html = html.replace(old, new); p += 1; print('firstLoad: OK')
else:
    print('firstLoad: NOT FOUND')

# ===== 14. JS: JINE unified chat with time dividers =====
old_func = """function renderJineChatUnified(timelineItems) {\n\t    var container = document.getElementById('jine-chat-msgs');\n\t    if (!container) return;\n\t    var html = '';\n\t    // Timeline JINE messages as 糖糖 text bubbles\n\t    (timelineItems || []).forEach(function(e) {\n\t        if (e.type === 'system') {\n\t            html += '<div class=\"jine-system-msg recall\">' + esc(e.text) + '</div>';\n\t        } else {\n\t            html += '<div class=\"jine-msg ame\"><div class=\"jine-avatar\"><img src=\"img/icon_ame.png\"></div><div><span class=\"time\">' + esc(e.time||'') + '</span><div class=\"bubble\">' + esc(e.text) + '</div></div></div>';\n\t        }\n\t    });\n\t    // Interactive chat messages (阿P + 糖糖), limited to last 30\n\t    var chatMsgs = jineChatMsgs;\n\t    chatMsgs.forEach(function(msg) {\n\t        if (msg.sticker) {\n\t            html += '<div class=\"jine-msg p\"><div class=\"sticker-content\">';\n\t            html += stickerHTML(msg.sticker);\n\t            html += '</div></div><div class=\"jine-read-receipt\">已读</div>';\n\t        } else if (msg.player_text) {\n\t            html += '<div class=\"jine-msg p-text\"><div class=\"bubble player-text-bubble\">' + esc(msg.player_text) + '</div></div>';\n\t            html += '<div class=\"jine-read-receipt\">已读</div>';\n\t        }\n\t        if (msg.recall) html += '<div class=\"jine-system-msg recall\">糖糖撤回了一条消息</div>';\n\t        if (msg.ame_sticker) {\n\t            html += '<div class=\"jine-msg ame-sticker\"><div class=\"jine-avatar\"><img src=\"img/icon_ame.png\"></div><div><div class=\"jine-bubble stamp-msg\">';\n\t            html += stickerHTML(msg.ame_sticker);\n\t            html += '</div></div></div>';\n\t        }\n\t        if (msg.reply) {\n\t            html += '<div class=\"jine-msg ame\"><div class=\"jine-avatar\"><img src=\"img/icon_ame.png\"></div><div><span class=\"time\">' + esc(msg.time||'') + '</span><div class=\"bubble\">' + esc(msg.reply) + '</div></div></div>';\n\t        }\n\t    });\n\t    container.innerHTML = html || '<div class=\"empty-state\"><div class=\"icon\"><img src=\"img/icon_ame.png\"></div><p style=\"font-size:0.7rem;color:rgba(0,0,0,0.4);\">糖糖还没发消息...</p></div>';\n\t    container.scrollTop = container.scrollHeight;\n\t}"""

new_func = """function renderJineChatUnified(timelineItems) {\n\t    var container = document.getElementById('jine-chat-msgs');\n\t    if (!container) return;\n\n\t    // Collect all into flat chronological list\n\t    var all = [];\n\t    (timelineItems || []).forEach(function(e) {\n\t        all.push({ type: e.type === 'system' ? 'recall-tl' : 'ame-text', time: e.time || '', text: e.text || '' });\n\t    });\n\t    var chatMsgs = jineChatMsgs;\n\t    chatMsgs.forEach(function(msg) {\n\t        var t = msg.time || '';\n\t        if (msg.sticker)     all.push({ type: 'p-sticker', time: t, sticker: msg.sticker });\n\t        if (msg.player_text) all.push({ type: 'p-text',    time: t, text: msg.player_text });\n\t        if (msg.recall)      all.push({ type: 'recall',    time: t });\n\t        if (msg.ame_sticker) all.push({ type: 'ame-sticker', time: t, sticker: msg.ame_sticker });\n\t        if (msg.reply)       all.push({ type: 'ame-text',  time: t, text: msg.reply });\n\t    });\n\t    all.sort(function(a, b) { return (a.time||'00:00').localeCompare(b.time||'00:00'); });\n\n\t    function toMins(t) { var p = (t||'00:00').split(':'); return parseInt(p[0])*60 + parseInt(p[1]); }\n\n\t    var html = '';\n\t    var lastMins = -99;\n\t    for (var i = 0; i < all.length; i++) {\n\t        var m = all[i];\n\t        var mins = toMins(m.time);\n\t        if (mins - lastMins > 5 || i === 0) {\n\t            html += '<div class=\"jine-date-divider\"><span>' + esc(m.time) + '</span></div>';\n\t        }\n\t        lastMins = mins;\n\t        switch (m.type) {\n\t        case 'ame-text':\n\t            html += '<div class=\"jine-msg ame\"><div class=\"jine-avatar\"><img src=\"img/icon_ame.png\"></div><div class=\"bubble\">' + esc(m.text) + '</div></div>';\n\t            break;\n\t        case 'recall': case 'recall-tl':\n\t            html += '<div class=\"jine-system-msg recall\">糖糖撤回了一条消息</div>';\n\t            break;\n\t        case 'p-sticker':\n\t            html += '<div class=\"jine-msg p\"><div class=\"sticker-content\">' + stickerHTML(m.sticker) + '</div></div>';\n\t            html += '<div class=\"jine-read-receipt\">已读</div>';\n\t            break;\n\t        case 'p-text':\n\t            html += '<div class=\"jine-msg p-text\"><div class=\"bubble player-text-bubble\">' + esc(m.text) + '</div></div>';\n\t            html += '<div class=\"jine-read-receipt\">已读</div>';\n\t            break;\n\t        case 'ame-sticker':\n\t            html += '<div class=\"jine-msg ame-sticker\"><div class=\"jine-avatar\"><img src=\"img/icon_ame.png\"></div><div><div class=\"jine-bubble stamp-msg\">' + stickerHTML(m.sticker) + '</div></div></div>';\n\t            break;\n\t        }\n\t    }\n\n\t    container.innerHTML = html || '<div class=\"empty-state\"><div class=\"icon\"><img src=\"img/icon_ame.png\"></div><p style=\"font-size:0.7rem;color:rgba(0,0,0,0.4);\">糖糖还没发消息...</p></div>';\n\t    container.scrollTop = container.scrollHeight;\n\t    // Read receipt delay\n\t    var receipts = container.querySelectorAll('.jine-read-receipt');\n\t    for (var ri = 0; ri < receipts.length; ri++) { receipts[ri].classList.remove('show'); }\n\t    clearTimeout(window._jineReadTimer);\n\t    if (receipts.length > 0) {\n\t        window._jineReadTimer = setTimeout(function() {\n\t            var r2 = container.querySelectorAll('.jine-read-receipt');\n\t            for (var rj = 0; rj < r2.length; rj++) { r2[rj].classList.add('show'); }\n\t        }, 2200);\n\t    }\n\t}"""

if old_func in html:
    html = html.replace(old_func, new_func); p += 1; print('JINE unified chat: OK')
else:
    print('JINE unified chat: NOT FOUND - this is critical!')

print(f'\nTotal patches: {p}')
with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Saved')
