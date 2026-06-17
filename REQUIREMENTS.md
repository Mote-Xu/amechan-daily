# 需求文档 — 超天酱日常推文小站

> 版本：v4.1 · 2026-06-17

---

## P0：架构 ✅

| ID | 功能 | 状态 | 关键实现 |
|----|------|:--:|------|
| F7 | 戳一戳 | 🟢 | v4.1: pool 10条(4次)，600ms发布动画+slideInPost，静默后台补货 |
| F8 | JINE 聊天 | 🟢 | v4.1: sticker动作翻译+语境判断+后端模板词替换+注入防御 |

## P1：内容质量 ✅

| ID | 领域 | 状态 | 已做 |
|----|------|:--:|------|
| C1 | JINE 聊天 | 🟢 | sticker→动作翻译消除meta点评；core_drives语境判断(短句≠拒绝)；15+种身体依赖表达；sticker_rules情绪绑定+多样性；后端_regex替换"手冰了"；Prompt Injection防御 |
| C2 | 推博 Feed | 🟢 | 超天酱禁止空洞模板(必须含具体微小事件)；糖糖日记强制无逻辑重复+核心词汇；timeline三层表里反差要求；hidden_pool扩至10条 |
| C3 | 弹幕 | 🟢 | 应援 30+吐槽 39 |

## P2：公网部署 🔴 进行中

| ID | 需求 | 状态 |
|----|------|:--:|
| S1 | CORS | ✅ `_set_cors()` + `do_OPTIONS()` |
| S2 | Prompt Injection 防御 | ✅ 11种模式检测 + 角色化替换 + system_warning |
| S3 | Turnstile 无感验证 | 🟡 后端框架已搭建(`/api/verify-turnstile`)，缺 Site Key |
| S4 | 频率限制 | 🟡 代码已有，本地关闭，部署时启用 |
| S5 | HTTPS | ⏳ 待部署（Cloudflare Flexible 模式或 VPS 配证书） |
| S6 | API Key 保护 | ⏳ 不能暴露在前端，需后端代理或环境变量 |

部署方案：Vercel(前端静态) + 轻量云服务器(后端) + Cloudflare(HTTPS+DNS)

### 部署前检查清单

- [ ] 申请 Cloudflare Turnstile Site Key + Secret Key
- [ ] 前端加 Turnstile widget + cf_token 传递
- [ ] 后端启用 `check_rate_limit()`
- [ ] 环境变量 `TURNSTILE_SECRET_KEY` 配置
- [ ] CORS `Access-Control-Allow-Origin` 改为 Vercel 域名
- [ ] Cloudflare SSL/TLS 设为 Flexible（若 VPS 无证书）
- [ ] `.env` 不进 git（确认 .gitignore）

## v4.1 问题修复记录

| 问题 | 修复方式 | 文件 |
|------|---------|------|
| JINE meta点评("死猫表情") | STICKER_MAP→动作描述，禁止提及"贴图/表情包/猫" | prompts.py |
| ame_tsun过度使用 | sticker_rules绑定情绪，仅限害羞时使用 | prompts.py |
| "手冰了"泛滥 | 硬禁(negative_rules)+后端正则替换(_sanitize_template_phrases) | prompts.py + generator.py |
| 短句误读为拒绝 | core_drives加语境判断：短句≠拒绝 | prompts.py |
| 聊天不滚动 | CSS overflow:hidden+scroll-behavior+smooth + JS setTimeout 50ms | index.html |
| Pool小/冷却提示 | pool 5→10条，补货提前+静默，去alert | prompts.py + index.html |
| F7推文瞬间闪现 | 600ms发布延迟+posting-indicator+slideInPost动画 | index.html |
| 已读标志集体闪烁 | _shownReceipts状态追踪，旧消息直接显示，新消息逐条淡入 | index.html |
| Prompt Injection | 11种正则模式+sanitize_user_input+system_warning标签 | server.py + prompts.py |

## 残余

1. 弹幕 CSS 偶尔消失
2. webcam 部分帧缺失 (handspinner_004, tv_005, voice_training_007)
3. 部署：Turnstile前端集成 + 限频启用 + HTTPS
