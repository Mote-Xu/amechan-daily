# 超天酱模拟账号 — v4.5 收工报告

> v4.5：Turso 云端存档 + 双机共享 Tunnel 容灾 + 多项修复。
> 结论：双机容灾闭环，云端存档上线。

---

## 最终架构

```
用户 → amechan.mote-pal.xyz → Cloudflare → Tunnel 87fc0324 ─┬─ 本地:8930
                                                             └─ 老电脑:8930
Cloudflare 自动轮询，本地关机→老电脑独扛，无感知切换
```

- 前端 localStorage 主运行存储 + Turso 云端存档（3s debounce，启动恢复）
- 匿名 UUID 认证，无需登录
- 后端纯计算 + Turso HTTP API（无 lib 依赖）
- prompts.py 人格校准（底层关系/sticker_7/硬禁词库）
- JINE 上下文感知（generator 注入，不改 prompts）

## v4.5 新增

| 改动 | 说明 |
|------|------|
| Turso 云端存档 | `POST /api/save` (upsert), `GET /api/load` (全存档), `DELETE /api/save/delete` |
| 匿名身份 | `crypto.randomUUID()` → localStorage → apiFetch Bearer header |
| 云恢复 | `syncFromCloudOnBoot()` 启动比对时间戳，`_cloudPaused` 防空覆盖 |
| 双机共享 Tunnel | 主备同用 `87fc0324`，CF 自动轮询，放弃独立 bak 域名（Zero Trust ghost lock） |
| 切存档修复 | `reloadFromSlot` 加 reply 引擎重置 |
| Webcam 修复 | `_autoCycleTimer` 存储引用，`switchState` 清除 |

## 残余

1. JINE 偶发傲娇反射 — 可接受
2. Turnstile — 前端就绪，缺 Site Key
3. cloudflared 服务化 — 老电脑可用 `cloudflared service install`
4. webcam 缺帧 handspinner_004
