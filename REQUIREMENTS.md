# 需求文档 — 超天酱日常推文小站

> 版本：v4.3 · 2026-06-18

---

## P0：架构 ✅

| ID | 功能 | 状态 | 关键实现 |
|----|------|:--:|------|
| F7 | 戳一戳 | 🟢 | pool 10条(4次)，600ms发布动画+slideInPost，静默后台补货 |
| F8 | JINE 聊天 | 🟢 | v4.3: sticker动作翻译+语境判断+后端模板词替换+名字固化+注入防御+timeline上下文感知 |

## P1：内容质量

| ID | 领域 | 状态 | 已做 |
|----|------|:--:|------|
| C1 | JINE 聊天 | 🟢 | sticker→动作翻译消除meta点评；core_drives语境判断；15+种身体依赖表达；sticker_rules情绪绑定；后端_regex替换"手冰了"；名字固化；Prompt Injection防御；v4.3: timeline上下文隔离区(generator.py注入，不改prompts.py) |
| C2 | 推博 Feed | 🟢 | 超天酱禁止空洞模板；糖糖日记强制无逻辑重复+核心词汇；timeline三层表里反差；hidden_pool扩至10条 |
| C3 | 弹幕 | 🟢 | 应援 30+吐槽 39；v4.3: transform GPU动画 |
| C4 | F7 JINE 自言自语 | 🔴 | 质量低、同质化严重、和推文关联弱。需调整 prompts.py:JINE_RELEASE_SYSTEM |

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
| JINE 上下文割裂 | 前端传 `recent_posts`，generator 注入 `[系统数据]` 块 | index.html + server.py + generator.py |
| 公网 JINE 潜在 IPv6 问题 | HOST `127.0.0.1` → `0.0.0.0` | config.py |
| 弹幕 CSS 偶尔消失 | `left` → `transform: translateX()` + `contain` | index.html |
| fetchTimeline 覆盖 JINE 屏幕 | 空状态加 `ACTIVE_TAB !== 'jine'` 守卫 | index.html |
| 已读在回消息后才出现 | `_read` 标记与引擎 `_replied` 分离 | index.html |
| Webcam 过大遮挡内容 | 480px → 430px | index.html |

## v4.2 修改

| 问题 | 修复 | 文件 |
|------|------|------|
| AI自造名字("混音") | negative_rules硬禁 + 后端正则替换 | prompts.py + generator.py |
| 已读延迟 | batch窗口开始时标记_replied | index.html |
| 公网上线 | cloudflared + Cloudflare Named Tunnel | — |

## 残余

1. **F7 JINE 自言自语质量低** — prompts.py 需调整（等用户指示）
2. webcam 部分帧缺失 (handspinner_004, tv_005, voice_training_007)
3. Turnstile 前端集成
4. 全链路重启验证
5. cloudflared 服务化
