# JINE 聊天滚动问题 — 求助 Gemini

> 简洁版，只描述问题本身。

---

## 现象

JINE 聊天中，玩家发送消息后，聊天区没有自动滚到底部。已读标志和最新消息需要手动下滑才能看到。

## 已排除的原因

1. **时序** — 试过 50ms/200ms/500ms 延迟滚动，无效
2. **scrollIntoView** — 会触发外层页面滚动，不能直接用
3. **flexbox min-height:0** — 已加，无效
4. **overflow 未生效** — `.jine-chat-msgs` 有 `overflow-y: auto`

## 当前滚动代码

```javascript
container.innerHTML = html || '...';
container.scrollTop = container.scrollHeight;
```

其中 `container = document.getElementById('jine-chat-msgs')`。

## DOM 结构（JINE 标签页内）

```
.win95-outer (aspect-ratio: 266/388; max-height: 85vh; display: flex; flex-direction: column)
  .win95-titlebar (flex-shrink: 0)
  .win95-body (flex: 1; overflow-y: auto; padding: 0.8rem)
    .jine-screen (height: 100%; display: flex; flex-direction: column; border: 2px solid)
      .jine-titlebar (flex-shrink: 0)
      .jine-chat-msgs (flex: 1; min-height: 0; overflow-y: auto; padding: 4px 0) ← container
      .jine-typing (flex-shrink: 0; display: none → flex when typing)
      .jine-interactive (flex-shrink: 0) — 贴图栏 + 输入框
```

## 相关 CSS

```css
.jine-screen { height: 100%; display: flex; flex-direction: column; }
.jine-chat-msgs { flex: 1; min-height: 0; overflow-y: auto; padding: 4px 0; }
.win95-body { flex: 1; overflow-y: auto; padding: 0.8rem; }
```

## 观察

- 当用 `scrollIntoView` 时，不是 inner container 滚动，而是**整个页面**滚到顶部——说明 `.jine-chat-msgs` 可能根本没有形成独立的滚动容器
- 玩家发消息后，手动可以正常滚动 `.jine-chat-msgs`（里面内容比容器高时可以看到滚动条）
- `scrollTop = scrollHeight` 对 `.jine-chat-msgs` 好像无效

## 问题

`container.scrollTop = container.scrollHeight` 为什么不起作用？如何让 JINE 聊天区在消息发送后自动滚到底部？
