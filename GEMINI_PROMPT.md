# 超天酱模拟账号 — Gemini 全面审查 v4.3

> v4.3：JINE 上下文感知 + 人格校准 + F7 动态注入 + 双机 fallback 前端就绪 + 多项鲁棒性修复。
> **当前卡点：双机部署受阻于 Zero Trust Dashboard（需绑信用卡），老电脑待管理员重启。请给替代方案建议。**

---

## 一、项目概览

模拟《主播女孩重度依赖》糖糖/超天酱的社交媒体。纯前端 HTML + Python http.server 后端，DeepSeek V4-pro。
三层内容：Poketter 推博 + 糖糖日记 + JINE 私聊 + 弹幕。

## 二、架构（v4.3）

- 前端 localStorage 管理所有数据
- `apiFetch()` 本地直连 / 公网双机 fallback（主 `amechan.mote-pal.xyz`、备 `bak.mote-pal.xyz`）— **前端代码已就绪**
- 后端纯计算：sanitize → prompt → DeepSeek → sanitize → 返回 JSON
- ThreadingHTTPServer + CORS + 限频（本地默认关闭，`RATE_LIMIT_ENABLED=1` 启用）
- Prompt Injection 防御：11种正则 + system_warning
- JINE 上下文感知：前端传最近 timeline，generator 注入 `[系统内部同步]`（防误读）
- JINE 人格校准：底层关系定义（阿P=心理支柱）、sticker_7 专属规则、硬禁词库扩充
- F7 release：动态注入 5 种精神标签 + 因果锚点，温度 0.85
- F7 stagger 缓存：F7 消息逐条出期间聊天回复排队，避免时序穿插
- 弹幕：`transform: translateX()` GPU 加速 + `contain`

### 部署架构（理想 vs 现实）

**设计目标**：
```
用户 → https://amechan.mote-pal.xyz → Cloudflare → Tunnel amechan-local → 本地主力机（主）
                            https://bak.mote-pal.xyz → Cloudflare → Tunnel amechan → 老家 i5-6500（备）
  前端 apiFetch 自动检测主服务器状态，失败降级备用
```

**现实状态**：
- 前端 `apiFetch` 代码已写完
- 本地 Tunnel `amechan-local` 已创建（UUID: `87fc0324`）
- 老电脑 Tunnel `amechan` 原有（UUID: `51cc70a8`）
- **将 `amechan.mote-pal.xyz` 从老 Tunnel 切到本地 Tunnel 需要 Zero Trust Dashboard**
- Cloudflare 免费版 Zero Trust 现在要求绑信用卡才能进管理页
- `cloudflared tunnel route dns` 命令只加 DNS 记录，无法覆盖 Zero Trust 的 Public Hostname 绑定
- Cloudflare API Token 可操作 DNS 但无法操作 Tunnel Public Hostname

## 三、v4.3 已修复

| 问题 | 修复 |
|------|------|
| JINE 上下文割裂 | frontend→recent_posts，generator 注入 `[系统内部同步]` |
| JINE 人格崩坏（sticker_7/傲娇） | 底层关系定义 + sticker_7 专属规则 + 硬禁词库 |
| F7 release 质量低 | 动态注入精神标签+因果锚点，温度 0.85 |
| F7+聊天消息时序穿插 | F7 stagger 期间缓存聊天回复 |
| /api/generate JSON 截断 | max_tokens 4096 |
| 限频过于保守 | 去日上限，本地默认关闭，间隔 1s |
| 公网 IPv6 绑定 | HOST → 0.0.0.0 |
| 弹幕 CSS 消失 | transform GPU 动画 + contain |
| fetchTimeline 覆盖 JINE | ACTIVE_TAB 守卫 |
| 已读延迟 | _read / _replied 分离 |
| Server 崩溃 | _send_json try/except |

## 四、残余问题

1. **双机 fallback 部署受阻**：Zero Trust Dashboard 需绑卡。Cloudflare API Token 无法操作 Tunnel Public Hostname 绑定。需要替代方案绕过此限制。
2. **老电脑运维**：代码已通过 AnyDesk 传新文件覆盖，但 server 需管理员 `nssm restart` 才能加载；cloudflared 手动窗口不稳定待服务化。
3. JINE 偶发傲娇反射：prompts.py 校准后大幅改善，在可接受范围
4. webcam 缺帧 (handspinner_004, tv_005, voice_training_007)
5. Turnstile 前端集成
6. 重启自恢复全链路验证

## 五、请 Gemini 重点审查

1. **如何绕过 Zero Trust Dashboard 做 Tunnel hostname 绑定？** 能否用 Cloudflare API 或 `cloudflared` CLI 完成 Public Hostname 的增删改？
2. **双机方案的替代架构**：如果 Dashboard 确实绕不过，有没有不需要 Dashboard 的免费双机方案？
3. 老电脑 cloudflared 服务化的最佳 Windows 实践（无管理员能否用 Task Scheduler 实现开机自启 + 崩溃重启）
