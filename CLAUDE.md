# amechan-daily — 超天酱日常推文小站

> DeepSeek V4 驱动的超天酱模拟账号。
> 最后更新：2026-06-27 (v4.8)
>
> **🔒 角色还原优先于功能开发。见 `PRIVATE.md`（不上传远程仓库）。**
>
> **⚠️ prompts.py 的内容（人设、语气、角色行为）由用户设计，不许擅自改动。**

## 启动

```bash
conda activate deepseek_v4_api
python server.py  # → http://0.0.0.0:8930
```

## 双机节点

| 节点 | 系统 | Hostname | 管理 |
|------|------|------|------|
| 本地 | Windows 11 | HaozeのOffice | 直接操作 |
| 老电脑 | Ubuntu Server 24.04 | mote-home | SSH `mote@100.118.10.0`（Tailscale，免密密钥） |

老电脑 systemd 服务：
```bash
systemctl status amechan      # server.py
systemctl status cloudflared   # CF Tunnel
systemctl status cockpit       # Web 面板 https://192.168.1.4:9090
```

## 核心功能状态

| 功能 | 状态 | 备注 |
|------|:--:|------|
| F7 戳一戳 | 🟢 | pool 10条(5对)；v4.6: 兜底虚无池防耗尽 |
| JINE 聊天 | 🟢 | v4.6: timeline 上下文感知；presence_penalty 0.85 防同义重复 |
| 推博 Feed | 🟢 | 超天酱禁空洞模板，糖糖强制无逻辑重复，三层反差 |
| 弹幕 | 🟢 | 应援 30 + 吐槽 39，transform GPU 动画 |
| 多存档 | ✅ | createdAt 校验防串档 |
| 自动戳一戳 | 🟢 | 每15~30分自动F7，关标签页停；v4.6: 空池走虚无池 |
| 双机容灾 | 🟢 | 共享 Tunnel，Cloudflare 自动轮询 |
| Turso 云端存档 | 🟢 | 匿名 UUID，3s debounce 自动上传，启动时云恢复 |

## 架构 (v4.8)

```
用户 → amechan.mote-pal.xyz → Cloudflare → Tunnel 87fc0324 ─┬─ 本地 Windows (HaozeのOffice):8930
                                                             └─ 老电脑 Ubuntu (mote-home):8930
运维通道: Tailscale 100.118.10.0 (SSH 免密密钥)
Cloudflare 自动轮询，关机后老电脑独扛
```

```
浏览器 localStorage ↕ POST JSON (CORS)
Python ThreadingHTTPServer
  ├─ sanitize_user_input()        注入防御 (11模式)
  ├─ _sanitize_template_phrases() 手[冰|冷]→12种替代表达
  ├─ check_rate_limit()           限频（始终启用）
  ├─ verify_turnstile()           Turnstile (待前端集成)
  └─ _turso_execute()             v4.5: Turso HTTP API 云端存档
  ↕ DeepSeek V4-pro
```

## v4.8 修改记录 (2026-06-27)

| 修改 | 文件 | 说明 |
|------|------|------|
| JINE 渲染停止根治 | index.html | 聊天回复绕过 stagger cache 门控，`_replyProcessing` 在 API 回传后立即释放 |
| 渲染死锁防护 | index.html | `renderJineChatUnified` 包 try/catch；`_replyProcessing` 不再等 display timer |
| 事件循环节流 | index.html | `fetchTimeline` 10s 节流，`_refillPool` 30s 节流，防后台标签页定时器聚并发作 |
| 滚动修复 | index.html | `scrollTop=999999` 钳位滚动，替代冒泡到页面的 `scrollIntoView` |
| stagger 看门狗修复 | index.html | 改用独立 `_f7StaggerStarted` 时间戳，废弃 `_lastActionTime`（防止闲置误杀） |
| CSS 动画修复 | index.html | `fadeInUp` 加 `forwards`，防后台标签页卡在 `opacity:0` |
| 精神标签加权 | generator.py | 被害妄想 20%→10%，躁狂/渴求 25%、抑郁/戒断 25% |
| 老电脑重建 | mote-home | Ubuntu Server 24.04 重装；HDD 挂载 /mnt/data；systemd 管理服务；SSH 禁密码仅密钥；Cockpit Web 面板 |

## v4.6 修改记录 (2026-06-19)

| 修改 | 文件 | 说明 |
|------|------|------|
| F7 兜底虚无池 | index.html | VOID_JINE_POOL 24条简单短句，事件池耗尽时直接注入JINE，不调LLM |
| Stagger 重构 | index.html | 提取 `_staggerJineMsgsToChat()`，API和虚无池共用 |
| presence_penalty 上调 | generator.py | JINE chat: 0.6→0.85, release: 0.8→1.0；治长对话同义重复 |
| 正向重定向 | prompts.py + generator.py | 禁点评+命令狂+透视眼；自信自卑分界；叠字宅宅；上下文排序；release炸弹标记+记忆校准+接梗规则 |
| F7 release slot 竞态 | index.html | 锁 `_releaseSlotId`，防跨存档灌消息 |
| JINE 引擎重写 | index.html | 批量引擎→debounce队列+死锁保险丝；去 _batchStartIdx/_batchSentIdx |
| JINE 音效 | index.html + static/sfx/ | 发送/接收/F7三音效，Audio对象池3通道轮询 |
| 代码清理 | generator.py/server.py/config.py | 删除 feed.py/feed.json，去 API_BACKUP fallback，统一共享 Tunnel |
| 自拍图修复 | index.html | 每条推博独立轮换 + per-save 随机起始偏移 |

## v4.5 修改记录 (2026-06-19)

| 修改 | 文件 | 说明 |
|------|------|------|
| Turso 云端存档 | server.py + index.html | `POST /api/save`, `GET /api/load`, `DELETE /api/save/delete`；匿名 UUID；3s debounce 上传；启动云恢复 |
| 双机共享 Tunnel | 老电脑 cloudflared | 主备共用 `87fc0324`，Cloudflare 自动轮询，不搞独立域名 |
| 自动戳一戳 | index.html | 每15~30分随机自动F7，开窗口即生效，关标签页停 |
| 切存档修复 | index.html | `reloadFromSlot` 重置 reply 引擎状态 |
| Webcam 轮换竞态 | index.html | `_autoCycleTimer` 存引用防手动选状态被抢 |

## v4.3 修改记录

| 修改 | 文件 | 说明 |
|------|------|------|
| JINE 上下文感知 | index.html + server.py + generator.py | 前端传 `recent_posts`，generator 注入 `[系统内部同步]`，prompts.py 零改动 |
| F7 release 动态注入 | generator.py | 5 种精神标签 + 因果锚点 + 温度 0.85 |
| prompts 人格校准 | prompts.py | 底层关系定义、sticker_7 专属规则、硬禁词库扩充 |
| F7 stagger 缓存 | index.html | F7 消息逐条出期间聊天回复先排队 |
| 限频重设计 | server.py | 去日上限，`RATE_LIMIT_ENABLED` 本地默认关闭 |
| 弹幕 GPU 加速 | index.html | `left` → `transform: translateX()` + `contain` |
| fetchTimeline 防覆盖 | index.html | 空状态 `ACTIVE_TAB !== 'jine'` 守卫 |
| 已读即时显示 | index.html | `_read` 与引擎 `_replied` 分离 |
| Server 鲁棒性 | server.py | `_send_json` try/except 防崩 |

## 已知问题

1. **共享 Tunnel 双机容灾**：理论风险——CF 不管 server 死活，一台崩可能丢包。后续上独立 Tunnel + CF Worker 健康检查根治。
2. **JINE 渲染停顿**：v4.8 已根治（去 time-sort + CSS flex 护甲 + 云同步覆盖锁 + save 上限 60→300）。
3. **JINE 聊天偶发傲娇反射**：prompts.py 校准后大幅改善，LLM 偶尔滑回。可接受。
4. 弹幕 CSS 偶尔消失 — transform 加速后待观察
5. webcam 缺帧 handspinner_004/tv_005/voice_training_007 (源资产空号)

## 公网部署

| 项 | 状态 |
|---|:--:|
| CORS / 注入防御 / sanitizer | ✅ |
| Cloudflare Tunnel 共享 | 🟢 `87fc0324` 双机在线 |
| 老电脑 systemd | 🟢 `amechan.service` + `cloudflared.service` 自启 |
| 老电脑 Cockpit | 🟢 `https://192.168.1.4:9090` |
| 老电脑 SSH | 🟢 仅密钥，禁密码 |
| Turso 云端存档 | 🟢 |
| IP 限频 | 🟡 本地默认关闭，部署设 `RATE_LIMIT_ENABLED=1` |
| Turnstile | ⏳ 前端已集成，缺 Site Key |
| 独立 Tunnel + Worker | ⏳ 待上 |
