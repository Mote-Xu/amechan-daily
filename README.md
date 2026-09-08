# amechan-daily — 超天酱日常推文小站

> DeepSeek V4 驱动的超天酱模拟账号。一个「戳一戳就会自言自语、聊聊天就会傲娇」的虚拟角色小站。
> 当前版本：**v4.8**（2026-06-27）

---

## 这是什么

一个纯前端 + 轻量 Python 后端的单页小站：超天酱（JINE）会像真人一样发推博、被「戳一戳」（F7）后碎碎念、和你聊天（F8）。所有内容由 DeepSeek V4 实时生成，角色人设由 `prompts.py` 定义。

- 🔒 **角色还原优先于功能开发** — 人设细节见 `PRIVATE.md`（不上传远程仓库）
- ⚠️ **`prompts.py` 内容由用户设计，不许擅自改动**

## 功能特性

| 功能 | 说明 |
|------|------|
| F7 戳一戳 | 戳一下超天酱就自言自语（JINE release），事件池 10 条 + 兜底虚无池 24 条防耗尽 |
| JINE 聊天 | 带 timeline 上下文感知的聊天，presence_penalty 0.85 防同义重复 |
| 推博 Feed | 超天酱禁空洞模板、糖糖强制无逻辑重复，三层表里反差 |
| 弹幕 | 应援 30 条 + 吐槽 39 条，transform GPU 动画 |
| 多存档 | 多存档槽位，createdAt 校验防串档 |
| 自动戳一戳 | 每 15~30 分钟自动 F7，关标签页即停 |
| 云端存档 | Turso（libsql）匿名 UUID 存档，3s debounce 自动上传，启动时云恢复 |
| 双机容灾 | 本地 + 服务器共享 Cloudflare Tunnel，自动轮询 |

## 快速开始

### 环境要求

- Python 3.10+（conda 环境 `deepseek_v4_api`）
- DeepSeek API Key

### 安装与启动

```bash
conda activate deepseek_v4_api
pip install -r requirements.txt

# 配置 .env（见下）
python server.py  # → http://0.0.0.0:8930
```

浏览器打开 `http://localhost:8930` 即可。

### 环境变量（.env）

| 变量 | 必填 | 说明 |
|------|:--:|------|
| `DEEPSEEK_API_KEY` | ✅ | DeepSeek API Key，缺失则启动失败 |
| `TURSO_URL` / `TURSO_TOKEN` | 可选 | Turso 云端存档，不配则存档仅存本地 |
| `TURNSTILE_SECRET_KEY` | 可选 | Cloudflare Turnstile 验证，配置后自动启用 |
| `RATE_LIMIT_ENABLED` | 可选 | `1` 启用 IP 限频（1s/次），本地默认关闭，公网部署开启 |
| `CORS_ORIGIN` | 可选 | CORS 允许来源，默认 `*` |

## 架构

```
用户 → amechan.mote-pal.xyz → Cloudflare → Tunnel 87fc0324 ─┬─ 本地 Windows:8930（主）
                                                             └─ 老电脑 Ubuntu (mote-home):8930（备）
运维通道: Tailscale（SSH 免密密钥）
Cloudflare 自动轮询，主机关机后备用机独扛
```

```
浏览器 localStorage ↕ POST JSON (CORS)
Python ThreadingHTTPServer
  ├─ sanitize_user_input()        注入防御（11 种模式）
  ├─ _sanitize_template_phrases() 手[冰|冷]→12 种替代表达
  ├─ check_rate_limit()           限频（始终启用）
  ├─ verify_turnstile()           Turnstile 无感验证
  └─ _turso_execute()             Turso HTTP API 云端存档
  ↕ DeepSeek V4-pro
```

**无状态设计（v4 起）**：服务端不存 timeline/聊天记录，前端用 localStorage 管理状态，服务端只负责生成 + 云端存档。

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查（返回 hostname + 时间） |
| POST | `/api/generate` | 生成推博 timeline（无状态，返回 JSON） |
| POST | `/api/release` | F7 戳一戳 → JINE 自言自语消息（2~5 条） |
| POST | `/api/jine/chat` | JINE 聊天回复（带 history + recent_posts 上下文） |
| POST | `/api/save` | 存档上传（Bearer UUID 鉴权） |
| GET | `/api/load` | 加载该用户所有存档槽 |
| POST | `/api/save/delete` | 删除指定存档槽 |
| POST | `/api/verify-turnstile` | Turnstile token 验证 |

## 项目结构

```
amechan-daily/
├── server.py          # HTTP 服务器：路由、注入防御、限频、Turnstile、Turso 存档
├── generator.py       # 推文/JINE 消息生成逻辑（精神标签、因果锚点、温度控制）
├── prompts.py         # ⚠️ 角色人设与语气（用户设计，勿改）
├── config.py          # 全局配置：API Key、模型、温度、话题池、端口
├── static/
│   ├── index.html     # 前端单页（全部交互逻辑）
│   ├── img/           # 自拍图/表情资产
│   ├── bgm/           # 背景音乐（大文件，不入库）
│   └── sfx/           # 发送/接收/F7 音效
├── deploy/            # 双机部署指南 + 老电脑配置
├── data/              # 运行时数据（gitignore）
├── requirements.txt
└── .env               # 密钥（gitignore）
```

## 公网部署

- 域名：`amechan.mote-pal.xyz`（Cloudflare Tunnel 共享 `87fc0324`，双机轮询）
- 老电脑：Ubuntu Server 24.04，systemd 管理 `amechan.service` + `cloudflared.service` 自启
- 详细部署步骤见 [deploy/README.md](deploy/README.md)

### 安全措施

- ✅ Prompt Injection 防御：11 种模式检测，命中后替换为角色化回应
- ✅ Turnstile 无感验证（配置 Secret Key 后启用）
- ✅ IP 限频（公网部署设 `RATE_LIMIT_ENABLED=1`）
- ✅ API Key 仅后端持有，前端不接触
- ✅ CORS 白名单

## 已知问题

1. **共享 Tunnel 盲轮询**：CF 不管 server 死活，死节点剔除时间不确定。待上独立 Tunnel + CF Worker 健康检查根治。
2. **JINE 偶发傲娇反射**：prompts.py 校准后大幅改善，LLM 偶尔滑回，可接受。
3. **弹幕 CSS 偶尔消失**：transform 加速后待观察。
4. **webcam 缺帧**：handspinner_004 / tv_005 / voice_training_007 源资产空号。

## 文档索引

| 文档 | 内容 |
|------|------|
| [CLAUDE.md](CLAUDE.md) | 架构、版本修改记录、已知问题（新会话入口） |
| [REQUIREMENTS.md](REQUIREMENTS.md) | 功能需求 + 非功能约束 |
| [GEMINI_PROMPT.md](GEMINI_PROMPT.md) | 发给外部 AI 的完整项目总结 |
| [PRIVATE.md](PRIVATE.md) | 🔒 角色还原细节（本地，gitignore，不上传） |
| [deploy/README.md](deploy/README.md) | 双机部署指南 |
