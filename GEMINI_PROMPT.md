# 超天酱模拟账号 — Gemini 全面审查 v4.2

> v4.2：名字固化 + Cloudflare Tunnel 公网上线。老电脑 7×24 运行中。
> 请重点审查：残余问题、内容质量、老电脑运维可靠性。

---

## 一、项目概览

模拟《主播女孩重度依赖》糖糖/超天酱的社交媒体。纯前端 HTML + Python http.server 后端，DeepSeek V4-pro。
三层内容：Poketter 推博 + 糖糖日记 + JINE 私聊 + 弹幕。

## 二、架构（v4.2 无状态 + 后端消毒）

- 前端 localStorage 管理所有数据
- 后端纯计算：sanitize → prompt → DeepSeek → sanitize → 返回 JSON
- ThreadingHTTPServer 多线程 + CORS
- Prompt Injection 防御：11种正则 + system_warning
- 后端硬替换：手冰了→冷感表达池，自造名字→阿P

### 部署架构（已上线）

```
用户 → https://amechan.mote-pal.xyz → Cloudflare → Named Tunnel → 老家 i5-6500 8GB Win10
   域名: NameSilo $3/年         免费 HTTPS       UUID: 51cc70a8...    server.py(NSSM) + cloudflared
                                                                      AnyDesk 远程运维
```

- 无需公网 IP（Tunnel 主动外连 Cloudflare）
- HTTPS 免费（Cloudflare 提供）
- API Key 在后端环境变量，前端不可见

## 三、当前状态

### 已修复
| 问题 | 修复 |
|------|------|
| AI自造名字("混音") | negative_rules硬禁 + 后端正则替换 |
| "手冰了"泛滥 | 硬禁 + 后端正则→12种表达 |
| JINE meta点评("死猫表情") | sticker→动作翻译 |
| Pool太小 | 5→10条，静默补货 |
| 已读标志闪烁 | 状态追踪 |

### 残余问题
1. JINE 上下文割裂：糖糖不知道自己发过的 timeline 内容（如发了"芥末冰激凌"推文但聊天中毫不知情），需前端传最近 timeline 进 prompt
2. Turnstile 前端集成（后端框架已就绪）
3. 频率限制未启用
4. 弹幕 CSS 偶尔消失
5. 老电脑 cloudflared 待改为服务自启（当前手动窗口）
6. 重启自恢复全链路未验证

### 老电脑运维
- NSSM 管理 server.py（自启 + 崩溃自动重启）
- cloudflared 当前手动窗口 + Task Scheduler 兜底
- 暑假换 Ubuntu Server：systemd 替代 NSSM，SSH 替代 AnyDesk
