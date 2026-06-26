# 超天酱模拟账号 — v4.8 双机部署上线

> v4.8：JINE 渲染根治 + 老电脑 Ubuntu Server 重建 + systemd 管理。
> v4.6 完整实装：虚无池 + 正向重定向 + 命令狂/透视眼禁令 + JINE轰炸模式 + identity fix + 引擎重写 + 音效。

---

## 当前架构

```
用户 → amechan.mote-pal.xyz → Cloudflare → Tunnel 87fc0324 ─┬─ 本地 Win11 (HaozeのOffice):8930
                                                             └─ 老电脑 Ubuntu (mote-home):8930
运维通道: Tailscale 100.118.10.0 (SSH 免密密钥)
```

双机共享一个 Tunnel ID，Cloudflare 自动轮询，systemd 管理服务和自启。

## 老电脑 mote-home 规格

| 项目 | 规格 |
|------|------|
| OS | Ubuntu Server 24.04.4 LTS |
| CPU/RAM | 4 线程 / 8 GB (空闲 7.2GB) |
| 磁盘 | SSD 111GB 系统 + HDD 465GB `/mnt/data` |
| 安全 | ufw (仅 SSH + Tailscale + 9090) + SSH 禁密码仅密钥 |
| 面板 | Cockpit `https://192.168.1.4:9090` (家人友好) |
| 运行时 | Docker + Miniconda `deepseek_v4_api` (Python 3.11) |
| 服务 | systemd — `amechan.service` + `cloudflared.service` 自启 |

## v4.8 新增 (2026-06-27)

| 修改 | 说明 |
|------|------|
| **JINE 渲染根治** | 聊天回复绕过 stagger cache 门控；`_replyProcessing` 在 API 回传后立即释放 |
| **事件循环节流** | `fetchTimeline` 10s 节流，`_refillPool` 30s 节流，防后台标签页定时器聚并发作 |
| **滚动修复** | `scrollTop=999999` 钳位替代 `scrollIntoView`（避免冒泡到页面级滚动） |
| **stagger 看门狗修复** | 独立 `_f7StaggerStarted` 时间戳，废弃 `_lastActionTime`（防止闲置误杀） |
| **CSS 动画修复** | `fadeInUp` 加 `forwards`，防后台标签页卡在 `opacity:0` |
| **精神标签加权** | 被害妄想 20%→10%，躁狂/渴求 25%、抑郁/戒断 25% |
| **老电脑重建** | Ubuntu Server 24.04 重装；HDD 挂载；systemd 替换 NSSM |

## v4.6 已实装

- F7 兜底虚无池（24 条，耗尽时直注 JINE 不耗 LLM）
- 正向重定向（禁点评→视为敷衍发脾气）+ 命令狂禁令 + 透视眼禁令
- JINE Release 轰炸模式（须用「你」、允许问句、禁"反正你也不会回"）
- 记忆校准 + 接梗规则（`糖糖(连发/未读):` 标记）
- presence_penalty chat 0.85 / release 1.0
- JINE 引擎：debounce 队列 + 死锁保险丝
- JINE 音效：Audio 对象池 3 通道
- Turso 云端存档：匿名 UUID、3s debounce、启动恢复
- 双机共享 Tunnel 容灾

## 已知问题

1. **共享 Tunnel 盲轮询**：CF 不管 server 死活，死节点剔除时间不确定。实测老电脑刚上线时全部请求打到新节点。
2. JINE 偶发傲娇反射 — 可接受
3. 弹幕 CSS 偶尔消失 — 待观察
4. webcam 缺帧 — 源资产空号

---

## 请 Gemini 回答

1. **独立 Tunnel + CF Worker 方案是否值得现在投入？** 当前共享 Tunnel 实际表现可接受吗？还是应该趁老电脑刚重建，一次性把独立 Tunnel + Worker 做完？

2. **8GB 老电脑空闲 7.2GB**，amechan-daily 占用 ~20MB。还有余力跑什么轻量服务？（AdGuard Home？filebrowser？）

3. **Turso 云端存档**目前是单点依赖。如果 Turso 挂了，双机容灾也白搭。有没有必要加一层本地 SQLite 兜底？
