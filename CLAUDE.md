# amechan-daily — 超天酱日常推文小站

> DeepSeek V4 驱动的超天酱模拟账号。
> 最后更新：2026-06-18 (v4.3)
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

## 核心功能状态

| 功能 | 状态 | 备注 |
|------|:--:|------|
| F7 戳一戳 | 🟢 | pool 10条(4次)，600ms 发布动画；v4.3: 空池补货中反馈 + F7 stagger 期间缓存聊天回复 |
| JINE 聊天 | 🟢 | v4.3: timeline 上下文感知 + prompts.py 人格校准（底层关系/sticker_7/硬禁词库） |
| 推博 Feed | 🟢 | 超天酱禁空洞模板，糖糖强制无逻辑重复，三层反差 |
| 弹幕 | 🟢 | 应援 30 + 吐槽 39，transform GPU 动画 |
| 多存档 | ✅ | createdAt 校验防串档 |
| 双机 fallback | 🟢 | 公网主→`amechan.mote-pal.xyz`，备→`bak.mote-pal.xyz`，前端自动降级 |

## 架构 (v4.3)

```
浏览器 localStorage ↕ POST JSON (CORS)
  ├─ apiFetch() 本地直连 / 公网双机 fallback
Python ThreadingHTTPServer
  ├─ sanitize_user_input()        注入防御 (11模式)
  ├─ _sanitize_template_phrases() 手[冰|冷]→12种替代表达
  ├─ check_rate_limit()           RATE_LIMIT_ENABLED 控制（默认关闭）
  ├─ verify_turnstile()           Turnstile (待前端集成)
  └─ generate_jine_chat()         v4.3: recent_posts→_make_timeline_context()
  ↕ DeepSeek V4-pro
```

## v4.3 修改记录 (2026-06-18)

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

1. **JINE 聊天偶发傲娇反射**：prompts.py 校准后大幅改善，LLM 仍偶尔滑回（如"恶心...但是可以"）。在可接受范围。
2. 弹幕 CSS 偶尔消失 — transform 加速后待观察
3. webcam 部分帧缺失 (handspinner_004, tv_005, voice_training_007)

## 公网部署

| 项 | 状态 |
|---|:--:|
| CORS / 注入防御 / sanitizer | ✅ |
| Cloudflare Tunnel + 域名 `amechan.mote-pal.xyz` | ✅ |
| 老电脑 NSSM 服务 | ✅ |
| 双机 fallback | ⏳ 待配 `bak.mote-pal.xyz` Tunnel |
| IP 限频 | 🟡 默认关闭，部署设 `RATE_LIMIT_ENABLED=1` |
| Turnstile 前端集成 | ⏳ |
| 全链路重启验证 | ⏳ |
