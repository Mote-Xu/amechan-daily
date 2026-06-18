# 超天酱模拟账号 — Gemini 全面审查 v4.4

> v4.4 收工：双机 fallback 全线上线 + prompts 同居设定强化 + 已读标记修复。
> **当前卡点：Turnstile 部署配置；全链路重启验证。**

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

### 双机部署架构（✅ 已上线）

```
用户 → amechan.mote-pal.xyz → Cloudflare → Tunnel 87fc0324 → 本地:8930 (主)
       bak.mote-pal.xyz      → Cloudflare → Tunnel 51cc70a8 → 老电脑:8930 (备)
前端 apiFetch 主失败 → 自动降级备用
```

Cloudflared Locally-Managed 模式，完全绕过 Zero Trust Dashboard / 信用卡。

## 三、v4.4 完成清单

| 修改 | 说明 |
|------|------|
| Locally-Managed Tunnel | `route dns -f` 覆盖 DNS，主备域名均已路由生效 |
| 双机 fallback | 主备链路均可公网访问，前端 apiFetch 自动降级待实测 |
| 同居设定强化 | prompts.py 两处硬约束：同床共枕、禁止「你家/我家」分离 |
| 已读标记修复 | `_shownReceipts[key]` 提前标记，防止 innerHTML 重写导致公网丢已读 |
| Turnstile 前端 | widget + 240s token 刷新 + apiFetch 注入 cf_token |
| 部署脚本包 | `deploy/`: VBS 守护 + Task Scheduler 指南 |
| Webcam 帧计数 | tv 7→8, voice_training 8→9 |

## 四、残余

1. JINE 偶发傲娇反射（可接受范围）
2. webcam 缺帧 handspinner_004 (无源资产)
3. Turnstile 部署时填 key
4. 双机切换全链路测试 — 关主 server，验证浏览器自动降级到 bak
5. 老电脑 VBS 守护部署（当前仍用 NSSM）

## 五、请 Gemini 重点审查

1. **当前架构的长期稳定性**：Locally-Managed Tunnel + 双机 fallback 是否有单点风险？老电脑 NSSM 是否需要替换为 VBS 守护？

2. **已读标记修复方案是否合理**：把 `_shownReceipts` 标记提前到 render 时而非 stagger 回调中，解决了频繁 innerHTML 重写丢状态的问题。是否还有其他边界情况？

3. **Turnstile 的松耦合设计**：前后端均已就绪，部署时填 key 即可启用。这种设计适合长期维护吗？

4. **【重头戏】localStorage → 数据库迁移方案（第二轮深度评审）**

   **背景**：当前全部数据在浏览器 localStorage。动机：清缓存就丢数据、不能跨设备、没有备份。

   **已有分析**（上次审查）：如果主备各有独立 SQLite，切换时会变成"平行宇宙"——老电脑不知道主力机的聊天记录。

   **已排除的方案**：
   - Supabase/Neon 免费版：闲置休眠，首次访问 5-10s 唤醒，响应速度不可接受
   - Litestream 实时同步：Windows 环境运维复杂，文件锁冲突风险高

   **核心约束（不可妥协）**：
   - ❌ 不能出现"平行世界"：主备切换后数据必须一致
   - ❌ 不能影响响应速度：API 调用延迟不能超过现有水平（~2s 聊天回复）
   - ✅ 数据不丢：清浏览器缓存也不怕
   - ✅ 保留双机 fallback 架构

   **请在这组硬约束下重新设计方案**。是否还有我们漏掉的第四种方案？比如：
   - 前端 localStorage 依然做主运行时存储，后端 SQLite 只在存档时写，切换时不读取——纯粹做"云存档备份"而非实时数据源？
   - 用 Cloudflare Workers KV / D1（免费额度，CDN 边缘，无休眠）作为主备之间的共享存储层？
   - 其他我们没想到的架构？
