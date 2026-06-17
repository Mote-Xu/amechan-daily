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

## P2：公网部署 🟢 已上线（2026-06-17）

| ID | 需求 | 状态 |
|----|------|:--:|
| S1 | CORS | ✅ `_set_cors()` + `do_OPTIONS()` |
| S2 | Prompt Injection 防御 | ✅ 11种模式检测 + 角色化替换 + system_warning |
| S3 | Turnstile 无感验证 | 🟡 后端框架已搭建，缺 Site Key |
| S4 | 频率限制 | 🟡 代码已有，本地关闭，部署时启用 |
| S5 | HTTPS | ✅ Cloudflare Tunnel 免费提供 |
| S6 | API Key 保护 | ✅ 后端→DeepSeek直连，前端不可见 |
| S7 | 固定域名 | ✅ `amechan.mote-pal.xyz` (NameSilo $3/年 + Cloudflare Named Tunnel) |
| S8 | 7×24 服务器 | ✅ 老家 i5-6500 8GB Win10 · server.py(NSSM) + cloudflared(手动+TaskScheduler) |
| S9 | 远程运维 | ✅ AnyDesk 无人值守 |

### 当前部署架构

```
用户 → https://amechan.mote-pal.xyz → Cloudflare → Named Tunnel → 老家电脑:8930
                                                                   i5-6500 8GB Win10
                                                                   server.py (NSSM 服务)
                                                                   cloudflared (手动 + Task Scheduler)
```

部署方案：Cloudflare Named Tunnel（固定域名 + 免费 HTTPS + 不需要公网 IP）。

### 老电脑运维

| 操作 | 命令 |
|------|------|
| server 状态 | `nssm.exe status amechan-server` |
| 重启 server | `nssm.exe restart amechan-server` |
| 启动 tunnel | `cloudflared.exe tunnel run amechan` |
| 更新代码 | AnyDesk 传文件 或 `git pull` + 重启 server |

### 残余问题

- cloudflared NSSM 服务僵尸化（SERVICE_PAUSED），暂用手动+Task Scheduler
- 需重启验证全链路自恢复
- 暑假换 Ubuntu Server → systemd 替代 NSSM
- [x] 装 Python 3 + openai + python-dotenv
- [x] 传项目文件
- [x] 复制 Tunnel 凭证
- [x] 设开机自启 (server: NSSM, tunnel: Task Scheduler)
- [x] 禁止休眠 + 自动登录
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
| 已读标记延迟出现 | 已读在API回复后才显示→提前到batch窗口开始时标记_replied | static/index.html |
| 无法链接公网 | 迁移到 cloudflared + Cloudflare Named Tunnel | — |

## v4.2 已知问题（未修复）

| 问题 | 现象 | 可能原因 |
|------|------|------|
| 公网访问时 JINE 无法工作 | 本地 localhost:8930 JINE 正常；通过 amechan.mote-pal.xyz 发消息无响应或502 | cloudflared 用 IPv6 [::1] 连 server 但 server 绑 127.0.0.1；config.yml 已改 127.0.0.1 但待验证 |
| JINE 上下文割裂 | 糖糖不知自己 timeline 发过的内容（如"芥末冰激凌"推文后在聊天中失忆） | JINE API 请求未传 timeline，AI 无上下文 |
| 老电脑网络不稳定 | tunnel 断连频繁，需手动重启 | 家庭网络波动；cloudflared 非服务自启 |

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
3. 部署：Turnstile前端集成 + 限频启用 + 老电脑重启验证
4. JINE 上下文割裂：糖糖不知道自己发过的 timeline 内容（如发了"芥末冰激凌"推但聊天中毫不知情），需前端传最近 timeline 给后端拼进 prompt
