# 需求文档 — 超天酱日常推文小站

> 版本：v4.6 · 2026-06-19

---

## P0：架构 ✅

| ID | 功能 | 状态 | 关键实现 |
|----|------|:--:|------|
| F7 | 戳一戳 | 🟢 | pool 10条(5对)；v4.6: 兜底虚无池(24条)，耗尽自动切，不耗LLM |
| F8 | JINE 聊天 | 🟢 | v4.3: timeline上下文 + prompts人格校准 + sticker_7规则 |

## P1：内容质量

| ID | 领域 | 状态 | 已做 |
|----|------|:--:|------|
| C1 | JINE 聊天 | 🟢 | 语境判断；身体依赖表达；sticker_rules；名字固化；注入防御；timeline上下文；人格校准 |
| C2 | 推博 Feed | 🟢 | 禁空洞模板；无逻辑重复；三层表里反差；hidden_pool 10条 |
| C3 | 弹幕 | 🟢 | 应援 30+吐槽 39；transform GPU动画 |
| C4 | F7 JINE 自言自语 | 🟢 | 动态注入精神标签+因果锚点 |
| C5 | JINE 质量 | 🟢 | presence_penalty 上调防同义重复；傲娇反射残余可接受 |

## P2：公网部署 🟢 已上线

| ID | 需求 | 状态 |
|----|------|:--:|
| S1 | CORS | ✅ |
| S2 | Prompt Injection 防御 | ✅ 11种模式 + system_warning |
| S3 | Turnstile | 🟡 前端已集成，缺 Site Key |
| S4 | 频率限制 | 🟡 本地默认关闭，部署 `RATE_LIMIT_ENABLED=1` |
| S5 | HTTPS | ✅ Cloudflare Tunnel |
| S6 | API Key 保护 | ✅ 后端直连 |
| S7 | 固定域名 | ✅ `amechan.mote-pal.xyz` |
| S8 | 7×24 服务器 | 🟢 NSSM + cloudflared 共享 Tunnel |
| S9 | 双机容灾 | 🟢 共享 `87fc0324`，CF 自动轮询 |
| S10 | 云端存档 | 🟢 Turso UUID + 3s debounce + 启动恢复 |

## v4.6 修改 (2026-06-19)

| 问题 | 修复 | 文件 |
|------|------|------|
| 自动戳一戳池子耗尽→报错/停止 | 兜底虚无池 VOID_JINE_POOL (24条)，耗尽自动切，不调LLM | index.html |
| Stagger 逻辑重复 | 提取 `_staggerJineMsgsToChat()`，API和虚无池共用 | index.html |
| 长对话同义重复（"像血又不像"反复出现）| presence_penalty 0.6→0.85 (chat) / 0.8→1.0 (release) | generator.py |
| 傲娇点评 + 上下文 + 措辞 | 正向重定向 + 命令狂 + 透视眼 + 自信自卑分界 + 叠字限制 + 宅宅态度 | prompts.py |
| F7 release 跨存档串数据 | 锁 slot ID 防 async 竞态 | index.html |
| 代码残留 + 过期配置 | 删 feed.py/json，去 API_BACKUP，统一 Tunnel | 多文件 |
| 自拍图重复/偏离 | 每条推博独立轮换 + per-save 随机偏移 | index.html |

## v4.5 修改 (2026-06-19)

| 问题 | 修复 | 文件 |
|------|------|------|
| 数据丢/不能跨设备 | Turso HTTP API 云端存档 + 匿名UUID + 启动恢复 | server.py + index.html |
| 切存档已读不回 | reloadFromSlot 重置 reply 引擎 | index.html |
| 自动戳一戳 | 每15~30分自动F7，关标签页停，不走隐藏检查 | index.html |
| Webcam 手动选状态被抢 | _autoCycleTimer 存引用 | index.html |
| 双机备站不通 | 共享 Tunnel 87fc0324，放弃独立 bak 域名 | 老电脑 cloudflared |

## v4.3 修改

| 问题 | 修复 |
|------|------|
| JINE 上下文割裂 | generator 注入 `[系统内部同步]` |
| JINE 人格崩坏 | 底层关系定义 + sticker_7 + 硬禁词库 |
| F7 release 质量低 | 动态注入精神标签+因果锚点 |
| 弹幕 CSS 消失 | transform GPU动画 |
| 已读延迟 | _read/_replied 分离 |

## 残余

1. JINE 偶发傲娇反射 — 可接受范围
2. webcam 缺帧 handspinner_004 (无源资产)
3. Turnstile 部署填 key
4. cloudflared 服务化（长期运维）
