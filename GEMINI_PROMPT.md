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

---

## 🔴 紧急：JINE 渲染停顿 — 前端诊断数据

### 现象
- 可以发送消息和收消息（音效正常）
- 但 JINE 聊天区看不到任何新消息（华为浏览器 + Chrome）
- 硬刷新后 85+ 条旧消息可以看到，发送新消息后看不到新增的

### v4.8 已做的修复（仍无效）
1. 消息存盘上限 60→300
2. 云同步异步覆盖锁（`_cloudRestoreDone` guard）
3. render 不再从 save 同步（避免 capped save 覆盖内存）
4. 滚动改用 `scrollTop=999999` 钳位
5. CSS 动画 `fadeInUp` 加 `forwards`
6. `renderJineChatUnified` 包 try/catch

### 关键诊断输出（`[jine:diag]`）
```
85 msgs → 85 items → 17849 chars
last 3 msgs: ['在干嘛', '哼', '又不说话']  ← F7 auto-poke 消息
container display: block | visibility: visible | opacity: 1 | height: 363px | overflow-y: auto

89 msgs → 89 items → 18888 chars
last 3 msgs: ['在干嘛', '哼', '又不说话']  ← 始终是F7消息，新的聊天回复不在末尾
container display: block | visibility: visible | opacity: 1 | height: 323px
```

### 矛盾点
- DOM 子节点数量、文本内容、CSS 全部正常
- 容器 `display:block` `visibility:visible` `opacity:1` `height:323px`
- 但用户**完全看不到任何消息**（不是"新消息看不到"，是全部看不到）
- 容器高度在缩小（363→323→297）

### 可能方向（需 Gemini 判断）
1. `.jine-screen` flex 布局中，`.jine-chat-msgs` 被 `.jine-interactive` 挤压导致实际可视高度为 0？
2. `CONTAINER.innerHTML` 被某段代码反复重置（renderFromCache），每次重建 DOM 但滚动位置未恢复？
3. 华为浏览器渲染引擎 bug（Chromium fork 的 CSS flex + overflow 行为异常）？
4. 消息排序问题——新聊天消息插入位置不对，被旧 F7 消息覆盖在视图之外？
5. `scrollTop=999999` 在某些情况下没有触发实际滚动（`overflow-y:auto` 但容器不需要滚动因为内容恰好 fit）？

---

## 请 Gemini 回答

1. **独立 Tunnel + CF Worker 方案是否值得现在投入？** 当前共享 Tunnel 实际表现可接受吗？

2. **Turso 云端存档**目前是单点依赖。如果 Turso 挂了，双机容灾也白搭。有没有必要加一层本地 SQLite 兜底？

3. **🔴 JINE 渲染停顿** — 基于上面的诊断数据，根因是什么？怎么修？
