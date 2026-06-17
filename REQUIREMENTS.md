# 需求文档 — 超天酱日常推文小站

> 版本：v4.2 · 2026-06-17

---

## P0：架构 ✅

| ID | 功能 | 状态 | 关键实现 |
|----|------|:--:|------|
| F7 | 戳一戳 | 🟢 | v4.1: pool 10条(4次)，600ms发布动画+slideInPost，静默后台补货 |
| F8 | JINE 聊天 | 🟢 | v4.2: sticker动作翻译+语境判断+后端模板词替换+名字固化+注入防御 |

## P1：内容质量 ✅

| ID | 领域 | 状态 | 已做 |
|----|------|:--:|------|
| C1 | JINE 聊天 | 🟢 | sticker→动作翻译消除meta点评；core_drives语境判断(短句≠拒绝)；15+种身体依赖表达；sticker_rules情绪绑定+多样性；后端_regex替换"手冰了"；名字固化(禁止非阿P称呼)；Prompt Injection防御 |
| C2 | 推博 Feed | 🟢 | 超天酱禁止空洞模板(必须含具体微小事件)；糖糖日记强制无逻辑重复+核心词汇；timeline三层表里反差要求；hidden_pool扩至10条 |
| C3 | 弹幕 | 🟢 | 应援 30+吐槽 39 |

## P2：公网部署 🟡 进行中

| ID | 需求 | 状态 |
|----|------|:--:|
| S1 | CORS | ✅ `_set_cors()` + `do_OPTIONS()` |
| S2 | Prompt Injection 防御 | ✅ 11种模式检测 + 角色化替换 + system_warning |
| S3 | Turnstile 无感验证 | 🟡 后端框架已搭建，缺 Site Key |
| S4 | 频率限制 | 🟡 代码已有，本地关闭，部署时启用 |
| S5 | HTTPS | ✅ Cloudflare Tunnel 免费提供 |
| S6 | API Key 保护 | ✅ 后端→DeepSeek直连，前端不可见 |
| S7 | 固定域名 | ✅ `amechan.mote-pal.xyz` (NameSilo $3/年 + Cloudflare Named Tunnel) |
| S8 | 7×24 服务器 | 🟡 当前本机，待迁移老家 i5-6500 8GB |

### 当前部署架构

```
用户 → https://amechan.mote-pal.xyz → Cloudflare → Named Tunnel → :8930
                                                                ↑
                                                当前：本机（关机=断）
                                                计划：老家老电脑（7×24）
```

部署方案：Cloudflare Named Tunnel（固定域名 + 免费 HTTPS + 不需要公网 IP）。

### 老电脑迁移待办

- [ ] 装 Python 3 + openai + python-dotenv
- [ ] 传项目文件
- [ ] 复制 Tunnel 凭证（51cc70a8-*.json + config.yml）
- [ ] 设开机自启 + 禁止休眠 + 禁止自动更新
- [ ] 重启测试全链路

### 部署后待办

- [ ] 申请 Turnstile Site Key + Secret Key
- [ ] 前端加 Turnstile widget
- [ ] 后端启用 check_rate_limit()
- [ ] 环境变量 TURNSTILE_SECRET_KEY 配置

## v4.2 问题修复记录

| 问题 | 修复方式 | 文件 |
|------|---------|------|
| AI自造玩家名字("混音") | negative_rules第0条硬禁非阿P称呼；后端正则替换混音/阿音/小音 → 阿P | prompts.py + generator.py |
| 无法链接公网 | 迁移到 cloudflared + Cloudflare Named Tunnel | — |

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
3. 部署：Turnstile前端集成 + 限频启用 + 老电脑迁移
