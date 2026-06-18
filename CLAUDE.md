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

## 核心功能状态

| 功能 | 状态 | 备注 |
|------|:--:|------|
| F7 戳一戳 | 🟢 | pool 10条(4次)，600ms 发布动画，Diary在上(后发反应)；v4.3: 空池显示补货中 |
| JINE 聊天 | 🟢 | v4.3: 前端传最近 timeline，generator 注入上下文（不改 prompts.py） |
| 推博 Feed | 🟢 | 超天酱禁空洞模板，糖糖强制无逻辑重复，三层反差 |
| 弹幕 | 🟢 | 应援 30 + 吐槽 39，transform GPU 动画 |
| 多存档 | ✅ | createdAt 校验防串档 |

## 架构 (v4.3)

```
浏览器 localStorage ↕ POST JSON (CORS)
Python ThreadingHTTPServer
  ├─ sanitize_user_input()        注入防御 (11模式)
  ├─ _sanitize_template_phrases() 手[冰|冷]→12种替代表达
  ├─ check_rate_limit()           限频（始终启用）
  ├─ verify_turnstile()           Turnstile (待前端集成)
  └─ generate_jine_chat()         v4.3: recent_posts→_make_timeline_context()
  ↕ DeepSeek V4-pro
```

## v4.3 修改记录 (2026-06-18)

| 修改 | 文件 | 说明 |
|------|------|------|
| JINE 上下文感知 | index.html + server.py + generator.py | 前端传 `recent_posts`，generator 注入 `[系统内部同步]` 块（防误读标注），**prompts.py 零改动** |
| F7 release 动态注入 | generator.py | 5 种随机精神标签 + 因果锚点指令 + 温度 0.5→0.85 + 空 msgs 兜底 |
| IPv6 绑定修复 | config.py | HOST `127.0.0.1` → `0.0.0.0` |
| 弹幕 GPU 加速 | index.html | `left` 动画 → `transform: translateX()` + `contain` |
| fetchTimeline 防覆盖 | index.html | 空状态 `ACTIVE_TAB !== 'jine'` 守卫 |
| 已读即时显示 | index.html | `_read` 标记（与引擎 `_replied` 分离） |
| 空池 UI 反馈 | index.html | F7 按钮显示"补货中..." + 计数显示"(补货中...)" |
| Server 鲁棒性 | server.py | `_send_json` 捕获 ConnectionAborted/ConnectionReset |
| Webcam 尺寸 | index.html | 480px → 430px |

## 已知问题

1. **F7 JINE 自言自语**：动态注入后第二批次已改善（回扣推文内容），首批仍偶有模板化。**prompts.py 需用户主导调整。**
2. **JINE 聊天偶发单条模板**（如被夸时回"突然说这种话恶不恶心"）— few-shot 缺少此 pattern。**等用户指示调整 prompts.py。**
3. 弹幕 CSS 偶尔消失 — transform 加速后待观察
4. webcam 部分帧缺失 (handspinner_004, tv_005, voice_training_007)

## 公网部署

| 项 | 状态 |
|---|:--:|
| CORS / 注入防御 / sanitizer | ✅ |
| Cloudflare Tunnel + 域名 `amechan.mote-pal.xyz` | ✅ |
| 老电脑 NSSM 服务 | ✅ |
| IP 限频 | ✅ 始终启用 |
| Turnstile 前端集成 | ⏳ |
| 全链路重启验证 | ⏳ |
