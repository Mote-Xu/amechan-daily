# amechan-daily — 超天酱日常推文小站

> DeepSeek V4 驱动的超天酱模拟账号。
> 最后更新：2026-06-18 (v4.4)
>
> **🔒 角色还原优先于功能开发。见 `PRIVATE.md`（不上传远程仓库）。**
>
> **⚠️ prompts.py 的内容（人设、语气、角色行为）由用户设计，不许擅自改动。**

## 启动

```bash
conda activate deepseek_v4_api
python server.py  # → http://0.0.0.0:8930
```

环境变量（部署时）：
- `RATE_LIMIT_ENABLED=1` — 启用 IP 限频（本地默认关闭）
- `TURNSTILE_SECRET_KEY=...` — Turnstile 验证密钥
- 前端: `TURNSTILE_SITE_KEY=...` — 部署前在 `index.html` 中填入

## 核心功能状态

| 功能 | 状态 | 备注 |
|------|:--:|------|
| F7 戳一戳 | 🟢 | pool 10条(4次)，600ms 发布动画；v4.3: 空池补货中反馈 + F7 stagger 期间缓存聊天回复 |
| JINE 聊天 | 🟢 | v4.3: timeline 上下文感知 + prompts.py 人格校准（底层关系/sticker_7/硬禁词库） |
| 推博 Feed | 🟢 | 超天酱禁空洞模板，糖糖强制无逻辑重复，三层反差 |
| 弹幕 | 🟢 | 应援 30 + 吐槽 39，transform GPU 动画 |
| 多存档 | ✅ | createdAt 校验防串档 |
| 双机 fallback | 🟢 | v4.4: Locally-Managed Tunnel 绕过 Zero Trust，主备 DNS 已路由，浏览器验证通过 |
| Turnstile | 🟡 | 前端 widget + token 注入已就绪，部署时填 `TURNSTILE_SITE_KEY` |

## 架构 (v4.4)

```
浏览器 localStorage ↕ POST JSON (CORS)
  ├─ apiFetch() 本地直连 / 公网双机 fallback + Turnstile token 注入
Python ThreadingHTTPServer
  ├─ sanitize_user_input()        注入防御 (11模式)
  ├─ _sanitize_template_phrases() 手[冰|冷]→12种替代表达
  ├─ check_rate_limit()           RATE_LIMIT_ENABLED 控制（默认关闭）
  ├─ verify_turnstile()           Turnstile (前端已集成，部署时启用)
  └─ generate_jine_chat()         v4.3: recent_posts→_make_timeline_context()
  ↕ DeepSeek V4-pro
```

### 双机部署架构

```
用户 → amechan.mote-pal.xyz → Cloudflare → Tunnel 87fc0324 → 本地:8930 (主)
       bak.mote-pal.xyz      → Cloudflare → Tunnel 51cc70a8 → 老电脑:8930 (备)
前端 apiFetch 主失败 → 自动降级备用
```

Cloudflared 使用 **Locally-Managed** 模式（`config.yml` + `route dns`），无需 Zero Trust Dashboard / 信用卡。

## v4.4 修改记录 (2026-06-18)

| 修改 | 文件 | 说明 |
|------|------|------|
| Cloudflared 本地管理 | .cloudflared/*.yml, deploy/ | 切到 Locally-Managed 绕过 Zero Trust 绑卡；双机 ingress 分离；`route dns -f` 切主域名到本地 |
| 双机 fallback 上线 | — | 主 `amechan.mote-pal.xyz`→本地，备 `bak.mote-pal.xyz`→老电脑；浏览器验证通过 |
| 部署脚本包 | deploy/ | daemon_server.vbs + daemon_cloudflared.vbs + Task Scheduler 指南 + README |
| Turnstile 前端 | index.html | widget 容器 + token 管理 + apiFetch 注入 cf_token；每 240s 自动刷新 |
| Webcam 帧计数 | index.html | tv 7→8 (加载 007), voice_training 8→9 (加载 008), handspinner 保持 12 |
| cloudflared.exe | 项目根 | v2026.6.0 完整版 (54MB)，配合 `gitignore` 排除 |

## v4.3 修改记录

| 修改 | 文件 | 说明 |
|------|------|------|
| JINE 上下文感知 | index.html + server.py + generator.py | 前端传 `recent_posts`，generator 注入 `[系统内部同步]`（防误读），**prompts.py 零改动** |
| F7 release 动态注入 | generator.py | 5 种精神标签 + 因果锚点 + 温度 0.85 |
| prompts 人格校准 | prompts.py | 底层关系定义（阿P=心理支柱）、sticker_7 专属规则、硬禁词库扩充 |
| 双机 fallback | index.html | `apiFetch()` 本地直连 / 公网主备自动降级 |
| F7 stagger 缓存 | index.html | F7 消息逐条出期间聊天回复先排队，避免穿插 |
| 限频重设计 | server.py | 去日上限，间隔 1s，`RATE_LIMIT_ENABLED` 本地默认关闭 |
| 生成 token 扩容 | generator.py | max_tokens 1500→4096 防 JSON 截断 |
| IPv6 绑定修复 | config.py | HOST `127.0.0.1` → `0.0.0.0` |
| 弹幕 GPU 加速 | index.html | `left` → `transform: translateX()` + `contain` |
| fetchTimeline 防覆盖 | index.html | 空状态 `ACTIVE_TAB !== 'jine'` 守卫 |
| 已读即时显示 | index.html | `_read` 与 `_replied` 分离 |
| Server 鲁棒性 | server.py | `_send_json` try/except 防崩 |
| Webcam 尺寸 | index.html | 480px → 430px |

## 已知问题

1. **JINE 聊天偶发傲娇反射**：prompts.py 校准后大幅改善，LLM 仍偶尔滑回。在可接受范围。
2. **`bak.mote-pal.xyz` DNS 等待传播**：老电脑 `route dns` 已成功，新域名全球生效需等待。
3. **Git Bash curl 无法访问 Cloudflare**：浏览器正常，不影响使用。
4. **弹幕 CSS 偶尔消失** — transform 加速后待观察。
5. **webcam 缺帧**：handspinner_004 (无源资产)，tv_005 和 voice_training_007 (v4.4 已通过调整 count 加载后续帧)。

## 公网部署

| 项 | 状态 |
|---|:--:|
| CORS / 注入防御 / sanitizer | ✅ |
| Cloudflare Tunnel 主链路 | 🟢 Locally-Managed，浏览器验证通过 |
| Cloudflare Tunnel 备用链路 | 🟡 DNS 传播中 |
| 老电脑服务 | 🟢 NSSM 已重启，cloudflared Locally-Managed |
| 双机 fallback | 🟢 主链路上线，备链路等 DNS |
| IP 限频 | 🟡 默认关闭，部署设 `RATE_LIMIT_ENABLED=1` |
| Turnstile | 🟡 前端已集成，部署时填 `TURNSTILE_SITE_KEY` |
| 全链路重启验证 | ⏳ |
