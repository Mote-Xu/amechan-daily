# 项目总结 — 超天酱日常推文小站

> v3.3 架构稳定，下一步：公共部署。
> 请 Gemini 帮助评估部署方案和 API 安全策略。

---

## 一、项目现状

### 架构
```
浏览器 ←→ Python http.server (127.0.0.1:8930) ←→ DeepSeek V4-pro API
```

- 前端：单个 `index.html`（纯 HTML/CSS/JS，零框架），~2300 行
- 后端：Python 3.11，`http.server` 模块，5 个 `.py` 文件
- API：DeepSeek V4-pro，通过 OpenAI SDK 调用
- 数据：本地 JSON 文件 (`data/feed.json`)

### API 端点

| 方法 | 路径 | 功能 | 是否调用 DeepSeek |
|------|------|------|:--:|
| GET | `/api/timeline` | 获取时间线 | ❌ |
| GET | `/api/jine/chat` | 获取 JINE 记录 | ❌ |
| GET | `/api/stats` | 获取统计 | ❌ |
| POST | `/api/generate` | 生成新批次推文 | ✅ 5-15s |
| POST | `/api/release` | F7 戳一戳 | ✅ ~2s (偶尔触发生成则 15s) |
| POST | `/api/jine/chat` | JINE 聊天回复 | ✅ 2-8s |
| POST | `/api/clear` | 清空数据 | ❌ |

所有 POST 端点当前**没有任何鉴权**，任何知道 URL 的人都能调用并消耗 DeepSeek 额度。

### DeepSeek API 调用参数
```python
model: "deepseek-v4-pro"
temperature: 0.85 (聊天) / 0.5 (F7释放) / 0.9 (推博)
max_tokens: 300 (推博) / ~200 (聊天)
```

### 当前运行环境
- Windows 11 + WSL2 (Ubuntu)
- conda 环境 `deepseek_v4_api`
- 本地 `127.0.0.1:8930`

---

## 二、部署诉求

将项目部署到公网，任何人都能访问，但：

1. **API 不能被滥用** — 只有我自己的前端能调用生成端点
2. **低成本** — 个人项目，不想花大钱
3. **简单维护** — 不想引入复杂的基础设施

## 三、具体问题

### 3.1 部署架构
推荐前端和后端分别放哪里？

选项：
- A) 前端 GitHub Pages / Vercel + 后端放 AutoDL 云服务器（已有 RTX 4090）
- B) 前端 Vercel + 后端用 Cloudflare Workers 中转
- C) 全部放一台便宜的云服务器（阿里云/腾讯云轻量）
- D) 其他方案？

AutoDL 是按量计费的 GPU 实例，平时关机省钱，但用户访问时需要开机——这会导致冷启动延迟。有没有更好的后端托管方案？

### 3.2 API 保护
如何防止陌生人调用生成 API？

当前想的是：
- 前端页面加载时，后端生成一个临时 token
- 前端 POST 请求必须带这个 token
- Token 有过期时间，定期刷新

问题：
- 这个方案够不够？如果攻击者先加载页面拿到 token，再滥用呢？
- 有没有更简单的方案？（比如 Cloudflare Tunnel + Access？）
- 频率限制怎么做？Python 内存记录 IP 计数？还是接入外部服务？

### 3.3 DeepSeek API 中转
前端请求 → 后端 → DeepSeek，这个链路中后端需要加什么保护？

- 是否需要请求队列？并发会不会导致 API 额度超限？
- 是否需要缓存？同样的请求在短时间内多次调用？
- DeepSeek 有没有并发限制？

### 3.4 静态资源
图片（游戏素材、webcam 帧）大概 200+ 个文件，总共 ~20MB。
- 放 GitHub Pages / Vercel 够不够？
- 还是需要对象存储（OSS/S3）？

### 3.5 HTTPS
- AutoDL / 云服务器上怎么配 HTTPS？
- 如果前端放 Vercel（自带 HTTPS），后端放云服务器（HTTP），会被浏览器阻止 mixed content 吗？

### 3.6 其他风险
- `data/feed.json` 包含生成的推文和 JINE 记录，需要备份吗？
- 部署到公网还有哪些我没意识到的安全问题？

---

## 四、约束

- 个人项目，成本敏感
- 不想引入数据库（目前 JSON 文件够用）
- 不想引入前端框架
- 维护越简单越好
