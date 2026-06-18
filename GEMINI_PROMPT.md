# 超天酱模拟账号 — Gemini 紧急救援

> **当前卡死点：双机备站 `bak.amechan.mote-pal.xyz` 无法公网访问。Turso 云端存档已完成。主站正常。**

---

## 已完成的 v4.5 改动

| 改动 | 说明 |
|------|------|
| Turso 云端存档 | `apiFetch` 带 UUID，`POST /api/save`/`GET /api/load`/`DELETE /api/save/delete`，3s debounce 自动上传 |
| 云恢复 | `syncFromCloudOnBoot()` 启动时比对时间戳，云端更新则覆盖本地 |
| 前端降级 | `apiFetch` 主站失败自动切 `bak.amechan.mote-pal.xyz` |
| 切存档修复 | `reloadFromSlot` 重置 reply 引擎状态 |

## 当前部署拓扑

```
主站: amechan.mote-pal.xyz → CNAME → 87fc0324.cfargotunnel.com → 本地 cloudflared (locally-managed, amechan-local)
      状态: 🟢 手机4G可访问

备站: bak.amechan.mote-pal.xyz → CNAME → 51cc70a8.cfargotunnel.com → 老电脑 cloudflared (amechan)
      状态: 🔴 手机4G打不开
```

## 备站故障详情

**老电脑环境**：
- Win10, Python server.py 在跑 (127.0.0.1:8930 正常响应)
- cloudflared tunnel (51cc70a8) 4条QUIC连接在线
- config.yml: `hostname: bak.amechan.mote-pal.xyz → service: http://127.0.0.1:8930`
- `cloudflared tunnel route dns -f` 已执行，DNS CNAME 指向 tunnel UUID

**尝试过的方法（均失败）**：
1. 新建 tunnel `amechan-bak` (fe6dcab0) + `route dns` → 不通
2. 用 Cloudflare API 删旧 DNS 重建 CNAME → 不通
3. 切回旧 tunnel `51cc70a8` + `route dns -f` → 不通
4. cloudflared 日志里看不到任何 ingress 请求（说明流量根本没到 tunnel）

**已知事实**：
- 旧 tunnel `51cc70a8` 是 Zero Trust 时期创建的（非 locally-managed），可能残留 Dashboard 绑定
- 本地 tunnel `87fc0324` 是 locally-managed，`route dns -f` 后正常工作
- cert.pem 从本地复制到老电脑，tunnel 能正常连接 Cloudflare edge
- 没有 Zero Trust Dashboard 权限（需绑信用卡）

## 请 Gemini 诊断

1. 为什么 `route dns -f` 对旧 tunnel 51cc70a8 不生效？流量能到 Cloudflare edge 但进不了 tunnel
2. 是否需要删除旧 tunnel 51cc70a8、重新在本地创建 locally-managed tunnel、把凭证拷到老电脑？
3. 还是 DNS/proxy 层面的问题（orange cloud 和 tunnel 的 hostname 注册冲突）？
