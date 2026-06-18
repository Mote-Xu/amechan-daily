# 超天酱模拟账号 — v4.5 最终审查

> v4.5 收工。Turso上线，双机容灾闭环，自动戳一戳。

---

## 最终架构

```
用户 → amechan.mote-pal.xyz → Cloudflare → Tunnel 87fc0324 ─┬─ 本地:8930
                                                             └─ 老电脑:8930
共享Tunnel，CF自动轮询。关机后老电脑独扛。
```

---

## v4.5 完整清单

| 功能 | 说明 |
|------|------|
| Turso 云端存档 | UUID匿名，3s debounce上传，启动云恢复，删档同步删 |
| 双机共享Tunnel | 本地+老电脑同用87fc0324，CF轮询，不搞独立域名 |
| 自动戳一戳 | 开着的窗口每15~30分钟随机自动F7，关标签页停 |
| prompts 人格校准 | 底层关系(sticker_7)/硬禁词库/jine上下文感知 |
| F7 release 动态注入 | 精神标签+因果锚点，温度0.85 |
| 切存档修复 | reloadFromSlot重置reply引擎 |
| Webcam竞态修复 | _autoCycleTimer存引用 |
| 限频重设计 | 本地默认关闭，部署RATE_LIMIT_ENABLED=1 |
| 已读即时显示 | _read与_replied分离 |

## 请审查

1. **自动戳一戳逻辑**：`setTimeout` 循环，关标签页即停。只触发当前存档。池空自动补货。是否有遗漏？

2. **Turso 云端存档**：`POST /api/save` (upsert), `GET /api/load` (全存档), `DELETE /api/save/delete`。启动恢复逻辑：`_cloudPaused` 防新建空存档覆盖云端。是否合理？

3. **架构稳定性**：共享Tunnel双机 + Turso云端 + localStorage运行时。有没有单点风险？

## 残余

1. JINE 偶发傲娇可接受
2. Turnstile待填key
3. cloudflared服务化（长期）
