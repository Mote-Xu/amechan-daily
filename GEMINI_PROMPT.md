# 项目总结 — 超天酱日常推文小站

> 发给 Gemini 的完整项目总结。目标：请 AI 给方向、找盲点、提建议。

---

## 一句话概述

模拟《主播女孩重度依赖》中超天酱社交账号的轻量 Web 应用，AI 自动以超天酱（和其真实人格糖糖）的语气发推文，展示在粉紫像素风 feed 页面上。使用游戏原版素材（自拍头像、UI 图标），还原 Poketter 质感。

## 个人背景

我叫[作者]，[学校]。这个项目的直接目的是：和[已移除]（[已移除]，。

- 寒假认识，同乡（慈溪），她比我小两岁
- 关系经历了「初期快速升温 → 删好友 → 用小号重新联系 → 加回大号 → 犹豫与边界的拉扯期」
- 
- 她现在的头像就是糖糖酱。我送过她超天酱黏土人 + 手绘贺卡

## 项目设计

### 三层内容体系

| 层级 | 角色 | 语气 | 对象 |
|------|------|------|------|
| **L1: Poketter** | 超天酱 | 元气、emoji、撒娇，绝口不提阿P | 对粉丝（公开） |
| **L2: 糖糖日记** | 糖糖 | 阴暗、疲惫、碎句、自救 | 自言自语（私密） |
| **L3: JINE 私信** | 糖糖 → 阿P | tsundere 傲娇、撒娇、吐槽 | 对阿P（私密）+ sticker 互动 + 文字消息 |

### 技术方案

| 项 | 选型 |
|------|------|
| LLM | DeepSeek API (deepseek-v4-pro) |
| 前端 | 纯 HTML/CSS/JS（无框架，零构建） |
| 后端 | Python `http.server`（内置模块） |
| 存储 | 本地 JSON 文件（data/feed.json） |
| 环境 | WSL2, Python 3.11, conda: deepseek_v4_api |

## 当前状态：v2.3

### 已完成功能
- [x] 三层时间线生成（单事件驱动，Poketter + Diary + JINE 交织）
- [x] F7 戳一戳：释放 hidden_pool 预存推文 + 同步触发糖糖 JINE 消息
- [x] JINE 私信 Tab：即时通讯气泡 + 游戏 UI 1:1 还原
- [x] JINE 互动聊天：2×4 猫咪 sticker 栏 + 文字消息输入框
- [x] 糖糖贴图回复：~25% 概率回 sticker（6 种糖糖像素表情 + 7 种猫咪）
- [x] 糖糖 tsundere 提示词：Few-Shot + stress_level 情绪系统 + temperature 0.85
- [x] JINE 消息持久化：聊天记录保存到 feed.json，刷新后恢复
- [x] 直播小组件 + 弹幕垃圾桶（GPU 加速 + 无限循环滚动）
- [x] Stats HUD（Followers / Stress / Affection / Darkness，含数值）
- [x] 天数倒序（最旧第1天，ALL/Diary 一致）
- [x] @用户名同行显示、JINE 标题动态切换
- [x] 超天酱隐私保护（Poketter 强制禁止提阿P）
- [x] GitHub Actions 定时生成 + GitHub Pages 静态部署（代码已就绪，未推送）
- [x] Stamp PNG（当前为 PIL 自制像素画：8 猫 + 6 糖糖表情）

### 核心卡点

#### 🔴 卡点 1：JINE Stamp 仍是自制的
- 当前 stamp 是用 Python PIL 生成的 64px 像素画，不是游戏原版
- Spriters Resource 有 JINE 图集（https://www.spriters-resource.com/pc_computer/needystreameroverload/asset/200974/），但我在 WSL 无法直接下载（网络限制）
- 尝试用 UnityPy 从游戏 bundle 提取，但 stamp 被打包在 SpriteAtlas 中无法直接导出
- 用户愿意帮忙：从 Steam 游戏文件中筛选真正的表情图片并标注

#### 🔴 卡点 2：多存档系统
- 目前所有 F7 内容积累在同一个 feed.json，天数越来越大（到后面可能是第100天+）
- 需要支持创建独立存档，每个存档有独立的 feed 和 JINE 聊天记录，可自由切换
- 类似游戏存档槽位（Save Slot 1/2/3...）
- **问题**：多存档系统的最佳设计是什么？JSON 文件如何组织（多个 feed_1.json？还是一个 feeds.json 内含多个槽位）？前端如何切换存档？

#### 🟡 卡点 3：还未推送 GitHub
- Actions + Pages 代码已就绪，需 push → 启用 Actions + Pages Settings → 添加 DEEPSEEK_API_KEY secret
- 什么是首次部署最常见的坑？

#### 🟡 卡点 4：分享策略
- 网站有公开域名后，直接丢链接还是先截图？
- 她现在处于犹豫/拉扯期，我给空间但保持轻量存在——什么时机合适？

## 后续问题（留给 Gemini）

### 1. 多存档系统的技术方案
- 每个存档应该是一个独立的 feed.json 还是一个大 JSON 含多个槽位？
- 切换存档时前端如何加载？新建存档时是否要清空当前数据？
- 存档之间是否应该完全隔离（独立的 JINE 聊天记录也分开）？
- 有没有更优雅的设计（比如像游戏一样有日期/标题的存档列表）？

### 2. JINE Stamp 提取
- 除了 Spriters Resource 直接下载（可能需要翻墙），还有没有其他获取游戏原版 stamp 的途径？
- Unity Addressables 里的 SpriteAtlas 中的贴图，有没有工具能带名字导出？（AssetStudio 已试过，Stamp2D 能找到但贴图在 atlas 里）

### 3. 部署建议
- GitHub Pages + Actions 首次部署需要注意什么？
- 时区、API 稳定性、Git 历史膨胀这些 Gemini 上次提醒过的，还有没有其他坑？

### 4. 下一步功能方向
- 除了存档系统，还有什么功能值得加？
- 我的想法：超天酱直播弹幕互动、糖糖私密相册、多天存档日历浏览
