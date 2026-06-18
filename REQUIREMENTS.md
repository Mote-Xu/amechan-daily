# 需求文档 — 超天酱日常推文小站

> 版本：v4.3 · 2026-06-18

---

## P0：架构 ✅

| ID | 功能 | 状态 | 关键实现 |
|----|------|:--:|------|
| F7 | 戳一戳 | 🟢 | pool 10条(4次)，600ms发布动画+slideInPost，静默后台补货；v4.3: 空池补货中反馈 |
| F8 | JINE 聊天 | 🟢 | v4.3: sticker动作翻译+语境判断+后端模板词替换+名字固化+注入防御+timeline上下文感知 |

## P1：内容质量

| ID | 领域 | 状态 | 已做 |
|----|------|:--:|------|
| C1 | JINE 聊天 | 🟢 | sticker→动作翻译消除meta点评；core_drives语境判断；15+种身体依赖表达；sticker_rules情绪绑定；后端_regex替换"手冰了"；名字固化；Prompt Injection防御；v4.3: timeline上下文+防误读标注 |
| C2 | 推博 Feed | 🟢 | 超天酱禁止空洞模板；糖糖日记强制无逻辑重复+核心词汇；timeline三层表里反差；hidden_pool扩至10条 |
| C3 | 弹幕 | 🟢 | 应援 30+吐槽 39；v4.3: transform GPU动画 |
| C4 | F7 JINE 自言自语 | 🟡 | v4.3: 动态注入精神标签+因果锚点，质量明显改善（回扣"美瞳""骗处方"等具体内容） |
| C5 | JINE 聊天单条质量 | 🟡 | sticker_7 回应失格（"恶心死了"→应为复杂情绪）；被关心时傲娇反射（"假惺惺"） |

## P2：公网部署 🟢 已上线

| ID | 需求 | 状态 |
|----|------|:--:|
| S1 | CORS | ✅ |
| S2 | Prompt Injection 防御 | ✅ 11种模式 + system_warning |
| S3 | Turnstile | 🟡 后端框架已搭建，缺 Site Key |
| S4 | 频率限制 | ✅ IP 限频 2s/200次每天 |
| S5 | HTTPS | ✅ Cloudflare Tunnel |
| S6 | API Key 保护 | ✅ 后端直连，前端不可见 |
| S7 | 固定域名 | ✅ `amechan.mote-pal.xyz` |
| S8 | 7×24 服务器 | ✅ 老家 i5-6500 8GB Win10 · NSSM + cloudflared |
| S9 | 远程运维 | ✅ AnyDesk |

## v4.3 修改 (2026-06-18)

| 问题 | 修复 | 文件 |
|------|------|------|
| JINE 上下文割裂 | 前端传 `recent_posts`，generator 注入 `[系统内部同步]` 块 + 防误读标注 | index.html + server.py + generator.py |
| F7 release 质量低 | 动态注入 5 种精神标签 + 因果锚点 + 温度 0.85 + 空 msgs 兜底 | generator.py |
| F7 release API 偶尔失败无消息 | 前端自动重试一次，不用硬编码兜底 | index.html |
| 公网 JINE 潜在 IPv6 问题 | HOST `127.0.0.1` → `0.0.0.0` | config.py |
| 弹幕 CSS 偶尔消失 | `left` → `transform: translateX()` + `contain` | index.html |
| fetchTimeline 覆盖 JINE 屏幕 | `ACTIVE_TAB !== 'jine'` 守卫 | index.html |
| 已读延迟 | `_read` 与 `_replied` 分离 | index.html |
| 空池按 F7 无反馈 | 按钮"补货中..." + 计数显示 | index.html |
| Server 客户端断开崩溃 | `_send_json` try/except ConnectionAborted | server.py |
| Webcam 过大 | 480px → 430px | index.html |

## v4.2 修改

| 问题 | 修复 | 文件 |
|------|------|------|
| AI自造名字("混音") | negative_rules硬禁 + 后端正则替换 | prompts.py + generator.py |
| 已读延迟 | batch窗口开始时标记_replied | index.html |
| 公网上线 | cloudflared + Cloudflare Named Tunnel | — |

## 残余

1. F7 release 偶发模板化 + JINE 单条质量 — prompts.py 待用户调
2. webcam 部分帧缺失 (handspinner_004, tv_005, voice_training_007)
3. Turnstile 前端集成
4. 全链路重启验证
5. cloudflared 服务化
