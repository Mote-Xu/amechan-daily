# amechan-daily — 超天酱日常推文小站

> DeepSeek V4 驱动的超天酱模拟账号，自动生成双人格推文。
> 最后更新：2026-06-13

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
  config.py                # API 配置 + 推文参数 + 路径
  prompts.py               # 超天酱 / 糖糖 双人格提示词 + 话题池
  generator.py             # 推文生成（调 DeepSeek API，可独立运行）
  feed.py                  # JSON 推文存储与读取
  server.py                # HTTP 服务器（API + 静态文件，零新依赖）
  static/
    index.html             # Poketter 前端（v2.0，三 Tab + 直播 + F7）
    img/                   # 游戏提取素材
      icon_cho.png         # 超天酱头像（51×51 像素，卡片 header 固定用）
      icon_ame.png         # 糖糖头像（51×51 像素）
      cho_*.png            # 超天酱自拍（9 张，附在推文正文里当配图）
      ame_*.png            # 糖糖自拍（8 张）
      icon_status_*.png    # 游戏状态栏图标
  data/
    feed.json              # 推文持久化文件
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
| 互动数据 | 从 0 起随天数递增 | 接近 0 |

### 三层内容体系

| 层级 | 角色 | 语气 | 对象 | 形式 |
|------|------|------|------|------|
| **L1: Poketter 推文** ✅ | 超天酱 | 元气、emoji、撒娇 | 对粉丝 | 公开推文卡片 + 自拍配图 |
| **L2: 糖糖日记** ✅ | 糖糖 | 阴暗、疲惫、碎句 | 自言自语 | 暗色私密卡片 |
| **L3: JINE 私信** 🔧 | 糖糖 → 阿P | 求救、依赖、怨念 | 对阿P | 即时通讯气泡 |

> L3 当前为只读——仅展示 AI 生成的糖糖消息。**F8 规划：玩家可发游戏表情包互动，糖糖 AI 实时回复。**

表/里/私三层递进，增强窥探沉浸感。

### 单事件驱动生成

一次 API 调用，基于一个「今日事件」同时生成三层内容时间线（5-8 条，带时间戳 + 因果时序）+ 5 条 hidden_pool 预存。

### 专属话题注入

85% 从事件池随机 + 10% 专属话题（NANA、星露谷等）+ 5% 随机。

## 当前版本：v2.0

**已完成：**
- [x] 三层时间线生成（单事件驱动，Poketter + Diary + JINE 交织）
- [x] hidden_pool 预存 + F7 伪生成按钮（戳一戳释放）
- [x] JINE 私信 Tab（即时通讯气泡视图）
- [x] 直播画面小组件（呼吸灯 LIVE + 观看人数抖动 + 滚动弹幕）
- [x] 三 Tab 切换（All / Diary / JINE） + 桌面图标联动
- [x] 游戏原版素材（头像 + 自拍 + 状态图标）
- [x] 游戏 HUD 状态栏 + 头像/自拍分离
- [x] 游戏原版账号名/用户名/认证/互动数据格式（1:1 还原）
- [x] 弹幕含游戏梗（升天/盐我/鸽了）+ **弹幕垃圾桶消除**（点击负面弹幕→消除→Stress↓）
- [x] CRT 边缘暗角、F7 键盘快捷键 + 震动动画

**待办：**
- [ ] **F8: JINE 互动聊天** — 玩家发游戏表情包，糖糖 AI 实时回复（当前 JINE 只读）
- [ ] 调教超天酱 & 糖糖提示词语气
- [ ] 
- [ ] GitHub Actions 定时自动生成
- [ ] GitHub Pages 部署
- [ ] GitHub Pages 部署（可选）

## 技术栈

| 组件 | 技术 |
|------|------|
| LLM | DeepSeek API (deepseek-v4-pro) |
| 前端 | 纯 HTML/CSS/JS（无框架，零构建） |
| 后端 | Python `http.server`（内置模块） |
| 存储 | JSON 文件 |
| 素材提取 | UnityPy（从 Steam 游戏解包 .assets） |
| 游戏源 | `E:\Steam\steamapps\common\NEEDY GIRL OVERDOSE\` |
| 环境 | WSL2, Python 3.11, conda: deepseek_v4_api |
| 配色 | 粉紫像素风 (#2D1B4E / #FF69B4 / #9B59B6) + CRT 效果 |
| 字体 | DotGothic16（日系像素风） |

## 设计原则（来自 Gemini 建议 + 迭代）

1. **克制的互动**：不加输入框。用「单击按钮触发生成」代替——行动是用户的，内容是 AI 的，维持艺术装置的沉浸
2. **先截图后链接**：分享时先发截图 + 轻描淡写一句话，等她追问再给地址
3. **专属话题低概率**：NANA、星露谷等话题 ~10% 概率混入
4. **糖糖控制尺度**：侧重无力感、自我怀疑、对陪伴的渴望
5. **未来可部署**：前端纯静态，可随时上 GitHub Pages
6. **还原游戏质感**：素材直接来自 Steam 版游戏，不是同人仿制

## 已知问题

| 问题 | 说明 |
|------|------|
| JINE 只读 | 仅展示 AI 单向输出；规划 F8：玩家发游戏表情包 → 糖糖实时回复 |
| 提示词 tone 需迭代 | 三层内容质量取决于 prompt 调教，需持续观察 |
| 仅本地部署 | `127.0.0.1:8930`，外部不可访问 |
| v2 JSON 偶尔截断 | token 限制可能导致 JSON 不完整，已有截断修复但非完美 |
