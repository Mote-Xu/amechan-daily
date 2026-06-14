# amechan-daily — 超天酱日常推文小站

> DeepSeek V4 驱动的超天酱模拟账号，自动生成双人格推文。
> 最后更新：2026-06-14 (v2.3)

## 项目定位

模拟《主播女孩重度依赖》中「超天酱」社交账号的轻量 Web 应用。AI 自动生成超天酱 & 糖糖风格的日常推文，粉紫像素风 feed 展示。

**核心目标**：→ 

## 启动

```bash
# WSL 终端
conda activate deepseek_v4_api
cd /mnt/e/Desktop/Deepseek_V4_API/amechan-daily

# 配置 API Key（已有则跳过）
nano .env  # 设置 DEEPSEEK_API_KEY=sk-xxx

# 启动服务器
python server.py
```

浏览器 `http://127.0.0.1:8930`

## 架构

```
amechan-daily/
  .env                     # DEEPSEEK_API_KEY（不纳入 git）
  .github/workflows/       # GitHub Actions CI/CD
    daily-generate.yml     # 每日定时生成 + commit feed.json
    pages-deploy.yml       # push → 部署 GitHub Pages
  config.py                # API 配置 + 推文参数 + 路径
  prompts.py               # 超天酱 / 糖糖 双人格提示词 + 话题池
  generator.py             # 推文生成（调 DeepSeek API，可独立运行）
  feed.py                  # JSON 推文存储与读取
  server.py                # HTTP 服务器（API + 静态文件，零新依赖）
  static/
    index.html             # Poketter 前端（v2.3，三 Tab + 直播 + F7 + 静态模式 + 文字消息）
    img/                   # 游戏提取素材
      icon_cho.png         # 超天酱头像（51×51 像素，卡片 header 固定用）
      icon_ame.png         # 糖糖头像（51×51 像素）
      cho_*.png            # 超天酱自拍（9 张，附在推文正文里当配图）
      ame_*.png            # 糖糖自拍（8 张）
      icon_status_*.png    # 游戏状态栏图标
      stamps/              # JINE stamp PNG（当前为 PIL 自制像素画，待替换游戏原版）
  data/
    feed.json              # 推文持久化（含 jine_chat 互动记录）
  CLAUDE.md                # 本文件
  REQUIREMENTS.md          # 需求文档
  GEMINI_PROMPT.md         # 发给 Gemini 的项目总结
```

## 核心机制

### 游戏原版账号设定（1:1 还原）

| 项目 | 超天酱（大号） | 糖糖（小号） |
|------|---------------|-------------|
| 昵称 | 🎀超绝最可爱🎁天使酱 | 💙糖糖💙 |
| @用户名 | @x_angelkawaii_x | @raincandy_U |
| 头像 | icon_cho.png (51×51) | icon_ame.png (51×51) |
| 认证 | ✨认证 徽章 | 无 |
| 互动数据 | 粉丝递增，评论正常 | 💬 固定 0（私密账号） |

### 三层内容体系

| 层级 | 角色 | 语气 | 对象 | 形式 |
|------|------|------|------|------|
| **L1: Poketter 推文** ✅ | 超天酱 | 元气、emoji、撒娇，绝口不提阿P | 对粉丝（公开） | 公开推文卡片 + 自拍配图 |
| **L2: 糖糖日记** ✅ | 糖糖 | 阴暗、疲惫、碎句 | 自言自语（私密） | 暗色私密卡片，评论数 0 |
| **L3: JINE 私信** ✅ | 糖糖 → 阿P | tsundere 傲娇、撒娇、吐槽 | 对阿P（私密） | 即时通讯气泡 + sticker 互动 + 文字消息 |

> **重要人设规则**：超天酱是网红女主播，在 Poketter（公开）上绝对不能提及阿P、男友或任何恋爱对象。阿P 只存在于 JINE（私聊）和糖糖日记（私密账号）中。

### 单事件驱动生成

一次 API 调用，基于一个「今日事件」同时生成三层内容时间线（5-8 条，带时间戳 + 因果时序）+ 5 条 hidden_pool 预存。

### 专属话题注入

85% 从事件池随机 + 10% 专属话题（NANA、星露谷等）+ 5% 随机。

## 当前版本：v2.3

**v2.3 新增：**
- [x] **JINE 回复风格重写** — 从"脆弱/受伤"改为活泼 tsundere（"揍你哦!"、"笨蛋"、"哼"）
- [x] **糖糖贴图回复** — ~25% 概率回复 sticker 而非文字；6 种糖糖像素表情 + 7 种猫咪贴图
- [x] **JINE 文字消息** — sticker 栏下方输入框，可给糖糖发文字，AI 实时回复
- [x] **F7 联动 JINE** — 戳一戳后糖糖主动给阿P发消息（服务端生成，持久化到 feed.json）
- [x] **JINE 消息持久化** — 互动聊天记录保存到 feed.json，刷新页面后恢复
- [x] **Stamp PNG（PIL 自制）** — 8 猫 + 6 糖糖表情 PNG，前端双层渲染（PNG 覆盖 CSS fallback）
- [x] **Stats HUD 修复** — Stress 移到 Affection 前；四栏均有数值显示
- [x] **@用户名同行显示** — @raincandy_U 和 @x_angelkawaii_x 移到昵称右侧
- [x] **糖糖贴图布局** — 左对齐 + 头像 + 淡蓝气泡底
- [x] **天数倒序** — 最旧=第1天，最新=第N天，ALL/Diary 一致
- [x] **弹幕修复** — 速度 18-28s，反色 15%，初始位置屏幕外
- [x] **JINE 标题动态切换** — 切到 JINE Tab 时窗口标题显示 "JINE"
- [x] **超天酱隐私保护** — KANGEL_PERSONA 和 timeline prompt 强制禁止在 Poketter 提及阿P

**v2.2 已完成：**
- [x] GitHub Actions 定时生成 + GitHub Pages 部署 + 前端静态模式
- [x] Stress Level 情绪系统 + JINE Few-Shot + temperature 0.85
- [x] PNG stamp 支持（双层渲染 + CSS fallback）

**v2.1 已完成：**
- [x] F8 JINE 互动聊天 + 视觉还原 + 2×4 sticker + 延迟回复 + 撤回 + 弹幕修复

**当前卡点：**
- [ ] **JINE stamp 仍是 PIL 自制像素画**，非游戏原版。用户愿意帮忙筛选游戏内真实图片并标注
- [ ] **多存档系统** — 目前所有 F7 内容积累在同一个 feed.json，天数越来越大。需要支持创建独立存档、自由切换
- [ ] 推送 GitHub → 启用 Actions + Pages

## 技术栈

| 组件 | 技术 |
|------|------|
| LLM | DeepSeek API (deepseek-v4-pro) |
| 前端 | 纯 HTML/CSS/JS（无框架，零构建） |
| 后端 | Python `http.server`（内置模块） |
| 存储 | JSON 文件（data/feed.json） |
| Stamp 图片 | PIL 生成 64px 像素画（待替换游戏原版） |
| 素材提取 | UnityPy（从 Steam 游戏解包 .assets） |
| 游戏源 | `E:\Steam\steamapps\common\NEEDY GIRL OVERDOSE\` |
| 环境 | WSL2, Python 3.11, conda: deepseek_v4_api |
| 配色 | 粉紫像素风 (#2D1B4E / #FF69B4 / #9B59B6) + CRT 效果 |
| 字体 | DotGothic16（日系像素风） |

## 设计原则

1. **克制的互动**：用 F7 按钮触发生成——行动是用户的，内容是 AI 的，维持艺术装置感
2. **先截图后链接**：分享时先发截图 + 轻描淡写一句话，等她追问再给地址
3. **专属话题低概率**：NANA、星露谷等话题 ~10% 概率混入
4. **超天酱人设保护**：Poketter（公开）绝对不能提阿P；阿P 仅存在于 JINE + 糖糖日记
5. **糖糖控制尺度**：对阿P 是 tsundere 傲娇（活泼、吐槽、撒娇），而非纯抑郁
6. **还原游戏质感**：素材优先从 Steam 版游戏提取，JINE UI 1:1 还原

## 已知问题

| 问题 | 说明 |
|------|------|
| **JINE stamp 为 PIL 自制** | 8 猫 + 6 糖糖表情为 Python PIL 生成；需替换游戏原版 PNG |
| **无存档系统** | 所有内容积累在单个 feed.json；天数会无限增长 |
| 提示词需持续观察 | tsundere tone 已大幅改善，但仍需迭代 |
| GitHub Pages 只读 | 静态模式无 API，F7/JINE 互动不可用 |
| v2 JSON 偶尔截断 | token 限制可能导致 JSON 不完整，已有截断修复 |
