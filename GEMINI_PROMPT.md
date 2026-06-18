# 超天酱模拟账号 — Gemini 全面审查 v4.3

> v4.3：JINE 上下文感知 + 人格校准 + F7 动态注入 + 双机 fallback + 多项鲁棒性修复。
> 请重点审查：人格校准效果、双机部署方案、残余问题优先级。

---

## 一、项目概览

模拟《主播女孩重度依赖》糖糖/超天酱的社交媒体。纯前端 HTML + Python http.server 后端，DeepSeek V4-pro。
三层内容：Poketter 推博 + 糖糖日记 + JINE 私聊 + 弹幕。

## 二、架构（v4.3）

- 前端 localStorage 管理所有数据
- `apiFetch()` 本地直连 / 公网双机 fallback（主 `amechan`、备 `bak`）
- 后端纯计算：sanitize → prompt → DeepSeek → sanitize → 返回 JSON
- ThreadingHTTPServer + CORS + 限频（本地默认关闭，`RATE_LIMIT_ENABLED=1` 启用）
- Prompt Injection 防御：11种正则 + system_warning
- JINE 上下文感知：前端传最近 timeline，generator 注入 `[系统内部同步]`（防误读）
- JINE 人格校准：底层关系定义（阿P=心理支柱）、sticker_7 专属规则、硬禁词库扩充
- F7 release：动态注入 5 种精神标签 + 因果锚点，温度 0.85
- F7 stagger 缓存：F7 消息逐条出期间聊天回复排队，避免时序穿插
- 弹幕：`transform: translateX()` GPU 加速 + `contain`

### 部署架构

```
用户 → https://amechan.mote-pal.xyz → Cloudflare Tunnel → 主服务器（本地主力机）
                                    └→ Cloudflare Tunnel → 备服务器（老家 i5-6500）
  前端 apiFetch 自动检测主服务器状态，失败降级备用
```

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
| 公网单点故障 | apiFetch 双机 fallback |

## 四、残余问题

1. **JINE 偶发傲娇反射**：prompts.py 校准后大幅改善，LLM 偶尔滑回（如"恶心...但是可以"），在可接受范围
2. webcam 缺帧 (handspinner_004, tv_005, voice_training_007)
3. 公网 502：待重启验证 IPv6 修复
4. 老电脑 cloudflared 服务化
5. Turnstile 前端集成
6. 双机 fallback：前端已就绪，待配 `bak.mote-pal.xyz` Tunnel
7. 重启自恢复全链路验证
