# 需求文档 — 超天酱日常推文小站

> 版本：v4.4 · 2026-06-18

---

## P0：架构 ✅

| ID | 功能 | 状态 | 关键实现 |
|----|------|:--:|------|
| F7 | 戳一戳 | 🟢 | pool 10条(4次)，600ms发布动画；v4.3: 空池反馈 + stagger缓存聊天回复 |
| F8 | JINE 聊天 | 🟢 | v4.3: timeline上下文感知 + prompts.py人格校准；v4.4: 同居设定强化 |

## P1：内容质量

| ID | 领域 | 状态 | 已做 |
|----|------|:--:|------|
| C1 | JINE 聊天 | 🟢 | 语境判断；身体依赖表达；sticker_rules情绪绑定；名字固化；注入防御；v4.3: timeline上下文 + 人格校准；v4.4: 同居设定硬约束 |
| C2 | 推博 Feed | 🟢 | 禁空洞模板；糖糖强制无逻辑重复；三层表里反差；hidden_pool 10条 |
| C3 | 弹幕 | 🟢 | 应援 30+吐槽 39；transform GPU动画 |
| C4 | F7 JINE 自言自语 | 🟢 | 动态注入精神标签+因果锚点，质量明显改善 |
| C5 | JINE 聊天质量 | 🟡 | prompts.py 校准后大幅改善，LLM 偶发傲娇反射在可接受范围 |

## P2：公网部署

| ID | 需求 | 状态 |
|----|------|:--:|
| S1 | CORS | ✅ |
| S2 | Prompt Injection 防御 | ✅ 11种模式 + system_warning |
| S3 | Turnstile | 🟡 前端已集成，部署时填 `TURNSTILE_SITE_KEY` |
| S4 | 频率限制 | 🟡 本地默认关闭，部署 `RATE_LIMIT_ENABLED=1` |
| S5 | HTTPS | ✅ Cloudflare Tunnel |
| S6 | API Key 保护 | ✅ 后端直连 |
| S7 | 固定域名 | ✅ `amechan.mote-pal.xyz` (主) + `bak.mote-pal.xyz` (备) |
| S8 | 7×24 服务器 | 🟢 NSSM + cloudflared Locally-Managed |
| S9 | 双机 fallback | 🟢 Locally-Managed Tunnel 绕过 Zero Trust，主备 DNS 均已生效 |

## v4.4 修改 (2026-06-18)

| 问题 | 修复 | 文件 |
|------|------|------|
| Zero Trust Dashboard 绑卡墙 | Locally-Managed Tunnel + `route dns -f` 双机 DNS | .cloudflared/*.yml |
| 双机 fallback 无法部署 | 主备链路均已上线，DNS 已生效 | — |
| JINE 同居设定被遗忘 | 人设 + 核心行为两处硬约束：同床共枕、禁止「你家/我家」 | prompts.py |
| 公网已读标记丢失 | `_shownReceipts[key]` 提前到首次渲染时标记 | index.html |
| 老电脑 cloudflared 不稳定 | Locally-Managed 替代 remotely-managed；VBS 守护脚本备用 | deploy/ |
| Turnstile 前端未集成 | widget + token 管理 + apiFetch 注入 cf_token | index.html |
| Webcam 缺帧 | tv 7→8, voice_training 8→9 | index.html |
| 老电脑 server 未更新 | NSSM restart | — |

## v4.3 修改 (2026-06-18)

| 问题 | 修复 | 文件 |
|------|------|------|
| JINE 上下文割裂 | frontend→recent_posts，generator 注入 `[系统内部同步]` | index.html + server.py + generator.py |
| JINE 人格崩坏（sticker_7/傲娇） | 底层关系定义 + sticker_7 专属规则 + 硬禁词库 | prompts.py |
| F7 release 质量低 | 动态注入精神标签+因果锚点，温度 0.85 | generator.py |
| F7 release API 失败 | 前端自动重试一次 | index.html |
| F7+聊天消息穿插 | F7 stagger 期间聊天回复缓存排队 | index.html |
| /api/generate JSON 截断 | max_tokens 1500→4096 | generator.py |
| 限频过于保守 | 去日上限，间隔 1s，本地默认关闭 | server.py |
| 公网 IPv6 绑定 | HOST → 0.0.0.0 | config.py |
| 弹幕 CSS 偶尔消失 | transform: translateX() + contain | index.html |
| fetchTimeline 覆盖 JINE | ACTIVE_TAB 守卫 | index.html |
| 已读延迟 | _read / _replied 分离 | index.html |
| Server 客户端断开崩溃 | _send_json try/except | server.py |
| Webcam 遮挡 | 480→430px | index.html |
| 公网单点故障（双机） | apiFetch 双机 fallback | index.html |

## 残余

1. JINE 聊天偶发傲娇反射 — 可接受范围
2. webcam 缺帧 handspinner_004 (无源资产)，tv_005 和 voice_training_007 (v4.4 已调整 count)
3. Turnstile 部署：填 `TURNSTILE_SITE_KEY` + `TURNSTILE_SECRET_KEY`
4. 双机切换全链路测试
