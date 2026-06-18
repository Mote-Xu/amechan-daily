# 超天酱模拟账号 — Gemini 全面审查 v4.3

> v4.3：JINE 上下文感知 + F7 动态注入 + 多项前端/后端 bug 修复。
> 请重点审查：F7 JINE 自言自语质量（已部分改善）、偶发单条模板化、部署可靠性。

---

## 一、项目概览

模拟《主播女孩重度依赖》糖糖/超天酱的社交媒体。纯前端 HTML + Python http.server 后端，DeepSeek V4-pro。
三层内容：Poketter 推博 + 糖糖日记 + JINE 私聊 + 弹幕。

## 二、架构（v4.3）

- 前端 localStorage 管理所有数据
- 后端纯计算：sanitize → prompt → DeepSeek → sanitize → 返回 JSON
- ThreadingHTTPServer 多线程 + CORS
- Prompt Injection 防御：11种正则 + system_warning
- JINE 上下文感知：前端传最近 timeline，generator.py 注入 `[系统内部同步]` 块（含防误读标注），**prompts.py 零改动**
- F7 release 质量：动态注入 5 种精神标签 + 因果锚点，温度 0.5→0.85
- 弹幕：`transform: translateX()` GPU 加速 + `contain: layout style paint`

### 部署架构（已上线）

```
用户 → https://amechan.mote-pal.xyz → Cloudflare → Named Tunnel → 老家 i5-6500 8GB Win10
   域名: NameSilo $3/年         免费 HTTPS                      server.py(NSSM) + cloudflared
                                                                     AnyDesk 远程运维
```

## 三、v4.3 已修复

| 问题 | 修复 |
|------|------|
| JINE 上下文割裂 | 前端传 `recent_posts`，generator 注入 `[系统内部同步]`（防误读标注） |
| F7 release 质量低 | 动态注入精神标签 + 因果锚点指令 + 温度 0.85 + 空 msgs 兜底 |
| 公网 JINE 潜在 IPv6 问题 | HOST → `0.0.0.0` |
| 弹幕 CSS 偶尔消失 | `left` → `transform: translateX()` GPU 动画 |
| fetchTimeline 覆盖 JINE 屏幕 | `ACTIVE_TAB !== 'jine'` 守卫 |
| 已读延迟 | `_read` 与 `_replied` 分离 |
| 空池按 F7 无反馈 | 按钮"补货中..." + 计数显示 |
| Server 客户端断开崩溃 | `_send_json` try/except |
| Webcam 遮挡 | 480px → 430px |

## 四、残余问题

1. **F7 JINE 自言自语**：动态注入后第二批次明显改善（回扣具体推文内容），但首批仍偶有模板化。需 prompts.py 配合调整。
2. **JINE 聊天偶发单条模板**：如被突然夸奖时回"突然说这种话恶不恶心"，用词单一。prompts.py few-shot 缺少此 pattern。
3. 公网 JINE 502：待重启验证 IPv6 修复
4. 老电脑 cloudflared 非服务自启
5. webcam 部分帧缺失 (handspinner_004, tv_005, voice_training_007)
6. Turnstile 前端集成（后端框架已就绪）
7. 重启自恢复全链路未验证
