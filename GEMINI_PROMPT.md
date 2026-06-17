# 超天酱模拟账号 — Gemini 全面审查 v4.3

> v4.3：JINE 上下文感知 + IPv6 修复 + 弹幕 GPU 加速 + 多项前端 bug 修复。
> 请重点审查：F7 JINE 自言自语质量、上下文注入效果、部署可靠性。

---

## 一、项目概览

模拟《主播女孩重度依赖》糖糖/超天酱的社交媒体。纯前端 HTML + Python http.server 后端，DeepSeek V4-pro。
三层内容：Poketter 推博 + 糖糖日记 + JINE 私聊 + 弹幕。

## 二、架构（v4.3）

- 前端 localStorage 管理所有数据
- 后端纯计算：sanitize → prompt → DeepSeek → sanitize → 返回 JSON
- ThreadingHTTPServer 多线程 + CORS
- Prompt Injection 防御：11种正则 + system_warning
- JINE 上下文感知：前端传最近 timeline，generator.py 注入 `[系统数据]` 块，**prompts.py 零改动**
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
| JINE 上下文割裂 | 前端传 `recent_posts`，generator 注入 `[系统数据]` 隔离区 |
| 公网 JINE 潜在 IPv6 问题 | HOST → `0.0.0.0` |
| 弹幕 CSS 偶尔消失 | `left` → `transform: translateX()` GPU 动画 |
| fetchTimeline 覆盖 JINE 屏幕 | 空状态加 `ACTIVE_TAB !== 'jine'` 守卫 |
| 已读标记在回复后才出现 | `_read` 与 `_replied` 分离，发送即时显示 |
| Webcam 遮挡内容 | 480px → 430px |

## 四、残余问题

1. **F7 JINE 自言自语质量低**（新发现）：同质化严重（"好累""想被抱着""算了"），和具体推文内容关联弱。涉及 `prompts.py:JINE_RELEASE_SYSTEM` + `get_jine_release_prompt()`。需重新设计 prompt 方向——加强和推文事件的因果关联，扩大情绪范围和用词语料。

2. 公网 JINE 502：待重启验证 IPv6 修复是否生效
3. 老电脑 cloudflared 非服务自启
4. webcam 部分帧缺失 (handspinner_004, tv_005, voice_training_007)
5. Turnstile 前端集成（后端框架已就绪）
6. 重启自恢复全链路未验证
