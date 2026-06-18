# 超天酱模拟账号 — Gemini 全面审查 v4.4

> v4.4：双机 fallback 上线 — Locally-Managed Tunnel 成功绕过 Zero Trust Dashboard 绑卡。
> **当前卡点：`bak.mote-pal.xyz` DNS 等待全球传播；完整双机切换测试待做。**

---

## 一、项目概览

模拟《主播女孩重度依赖》糖糖/超天酱的社交媒体。纯前端 HTML + Python http.server 后端，DeepSeek V4-pro。
三层内容：Poketter 推博 + 糖糖日记 + JINE 私聊 + 弹幕。

## 二、架构（v4.4）

- 前端 localStorage 管理所有数据
- `apiFetch()` 本地直连 / 公网双机 fallback + Turnstile token 注入
- 后端纯计算：sanitize → prompt → DeepSeek → sanitize → 返回 JSON
- ThreadingHTTPServer + CORS + 限频 + Turnstile 验证（可选）
- Prompt Injection 防御：11种正则 + system_warning
- JINE 上下文感知 + 人格校准 + F7 动态注入 + stagger 缓存

### 双机部署架构（v4.4 ✅）

```
用户 → amechan.mote-pal.xyz → Cloudflare → Tunnel 87fc0324 → 本地:8930 (主)
       bak.mote-pal.xyz      → Cloudflare → Tunnel 51cc70a8 → 老电脑:8930 (备)
前端 apiFetch 主失败 → 自动降级备用
```

**Cloudflared Locally-Managed 模式**：`config.yml` + `route dns -f`。
完全绕过 Zero Trust Dashboard，无需信用卡。已验证通过。

## 三、v4.4 完成

| 修改 | 说明 |
|------|------|
| Locally-Managed Tunnel | `route dns -f` 覆盖 DNS CNAME，主域名切到本地 tunnel |
| 双机 fallback 上线 | 主链路浏览器验证通过；备链路 DNS 传播中 |
| Turnstile 前端 | widget + 240s 自动刷新 token + apiFetch 注入 cf_token |
| 部署脚本包 | `deploy/`: VBS 守护 + Task Scheduler 指南 |
| Webcam 帧计数 | tv 7→8, voice_training 8→9 |

## 四、残余

1. `bak.mote-pal.xyz` DNS 等待全球传播（老电脑 `route dns` 已成功）
2. 完整双机切换测试（关主 server，验证浏览器自动降级到 bak）
3. JINE 偶发傲娇反射（可接受范围）
4. webcam 缺帧 handspinner_004 (无源资产)
5. Turnstile 部署时填 `TURNSTILE_SITE_KEY`
6. 全链路重启验证

## 五、请 Gemini 重点审查

1. **Locally-Managed Tunnel 是否有长期风险？** 当前方案不需要 Zero Trust Dashboard。Cloudflare 是否会强制迁移回 Dashboard？有没有需要监控的点（如 tunnel 证书到期）？

2. **双机 fallback 的边界情况**：当前 `apiFetch` 在 `fetch` 抛异常时降级。如果主服务器返回 HTTP 200 但内容为空（半死不活），不会触发降级。是否需要加健康检查超时逻辑？

3. **VBS 守护 vs NSSM 的取舍**：老电脑目前用 NSSM（需管理员）+ cloudflared Locally-Managed。VBS + Task Scheduler 作为无管理员的备选方案。哪种更适合长期运维？
