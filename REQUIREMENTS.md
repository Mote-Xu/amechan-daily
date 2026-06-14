# 需求文档 — 超天酱日常推文小站

> 版本：v1.1 · 最后更新：2026-06-14

---

## 功能需求

### F1: 双人格推文生成 ✅
- **描述**：DeepSeek API 同时产出「超天酱推文」和「糖糖日记」
- **超天酱风格**：元气可爱、大量 emoji、对粉丝说话、偶尔无意露脆弱、**绝口不提阿P**
- **糖糖风格**：阴暗疲惫、零 emoji、短句碎片、自言自语
- **输入**：可选主题/心情关键词，留空则随机选题
- **实现**：`generator.py` + `prompts.py`

### F2: 推文 Feed 展示 ✅
- **描述**：时间线形式展示历史推文，Poketter 风格
- 超天酱推文：粉色卡片 + 认证徽章 + 头像 + 自拍配图，@用户名在昵称同行右侧
- 糖糖日记：暗色卡片 + 头像 + glitch hover 效果，评论数固定为 0，@用户名在昵称右侧
- 天数倒序：最旧=第1天，最新=第N天，ALL/Diary 一致
- **实现**：`static/index.html`

### F3: 推文持久化 ✅
- **描述**：生成的推文自动保存到 `data/feed.json`
- 启动时自动加载历史 feed，最多保留 50 条
- **实现**：`feed.py`

### F4: 视觉风格 ✅
- **描述**：粉紫像素风 UI，还原游戏 Poketter 质感
- 配色：深紫背景 + 粉色主色调，CRT 扫描线效果 + Win95 视窗
- 游戏原版头像 + 自拍配图 + HUD 状态栏（Followers / Stress / Affection / Darkness）
- 桌面图标行（Poketter / Diary / JINE），三 Tab 切换
- **实现**：`static/index.html` + `static/img/`

### F5: JINE 私信 Tab ✅
- **描述**：糖糖给阿P的私密聊天界面
- 即时通讯气泡风格（还原游戏内 JINE App）
- 内容由时间线生成 + JINE 互动聊天
- 三种视图 Tab 切换：All / Diary / JINE，JINE Tab 窗口标题动态显示 "JINE"
- **实现**：`static/index.html` v2.3

### F6: 直播画面小组件 ✅
- **描述**：假装超天酱正在直播的小组件
- CSS 呼吸灯 LIVE 角标 + 虚拟观看人数随机抖动
- 滚动弹幕（速度 18-28s，反色 15%，初始位置屏幕外）
- **实现**：`static/index.html`

### F7: 戳一戳发表新动态 ✅
- **描述**：「戳一戳超天酱 ✨」按钮
- 单击 → `POST /api/release` → 从 hidden_pool 释放预存推文
- hidden_pool 耗尽时自动触发生成
- 同步触发糖糖在 JINE 主动发消息（服务端生成，持久化）
- **实现**：`server.py` + `static/index.html`

### F6.5: 弹幕垃圾桶 ✅
- **描述**：还原游戏「消除负面评论」玩法
- 反色弹幕始终显示垃圾桶图标，点击 → 飞入动画消除 → Stress −3
- hover 暂停弹幕滚动，crosshair 光标，GPU 加速
- **实现**：`static/index.html`

### F8: JINE 互动聊天 ✅
- **描述**：玩家在 JINE Tab 中发送猫咪贴图或文字，糖糖 AI 实时回复
- **JINE 视觉还原**：游戏原版配色/气泡/布局
- **2×4 猫咪 sticker 栏**：8 只猫咪贴图 + 文字标签
- **文字消息**：sticker 栏下方输入框，可给糖糖发文字
- **糖糖贴图回复**：~25% 概率回复 sticker（6 种糖糖表情 + 7 种猫咪）
- **糖糖回复风格**：活泼 tsundere（傲娇、吐槽、撒娇），非阴沉/脆弱
- **延迟回复**：已读 → 正在输入 → 回复出现
- **撤回效果**：~20% 概率
- **消息持久化**：JINE 聊天记录保存到 feed.json，刷新后恢复
- **实现**：`server.py` + `generator.py` + `prompts.py` + `feed.py` + `static/index.html`

### F9: GitHub Actions 定时生成 ✅
- **描述**：每日 UTC 00:07（北京 08:07）自动生成推文
- `workflow_dispatch` 支持手动触发
- **实现**：`.github/workflows/daily-generate.yml`

### F10: GitHub Pages 静态部署 ✅
- **描述**：push main 自动部署静态站
- 前端双模式：本地 API / Pages 只读（自动隐藏 F7 + JINE 互动）
- **实现**：`.github/workflows/pages-deploy.yml` + `static/index.html`

### F11: 情绪系统 + 提示词强化 ✅
- **描述**：提升糖糖 JINE 回复质量
- **stress_level**：基于最近 sticker 互动计算压力值 (0-100)
- **Few-Shot 示例**：每种 sticker 多个回复示例（文字 + 贴图）
- **Temperature**：JINE 回复 0.85
- **实现**：`prompts.py` + `generator.py`

---

## 新需求（待实现）

### F13: 多存档系统
- **描述**：随着戳一戳次数增加，天数会无限增长。需要支持创建多个独立存档槽位（Save Slot），每个槽位有自己独立的 feed 时间线和 JINE 聊天记录，可自由切换
- **参考**：类似游戏存档槽位（Save Slot 1/2/3...），新建存档、切换存档、删除存档
- **待设计**

### F14: 游戏原版 JINE Stamp PNG
- **描述**：当前 stamp 为 PIL 自制的像素画，需替换为游戏原版贴图
- **来源**：Spriters Resource JINE sheet (https://www.spriters-resource.com/pc_computer/needystreameroverload/asset/200974/) 或用户从游戏文件中手动筛选
- **待用户协助**：筛选 + 标注真正的游戏内表情图片

---

## 非功能约束

### N1: 技术约束
- conda 环境 `deepseek_v4_api`，Python 3.11
- DeepSeek API (deepseek-v4-pro)
- 纯 HTML/CSS/JS 前端，零框架零构建
- Python `http.server` 后端，JSON 文件存储
- 不依赖 GPU，启动速度 < 5 秒

### N2: 内容约束
- 推文内容必须符合角色人设
- **超天酱（Poketter）绝对不能提及阿P、男友或恋爱对象**
- 不得生成政治敏感、色情暴力内容
- 糖糖控制在 tsundere 傲娇尺度（活泼吐槽 + 撒娇），不纯抑郁

### N3: 性能约束
- 单次生成响应时间 < 10 秒
- API 调用失败时自动重试（最多 3 次，指数退避）

---

## 变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-06-13 | 初始需求，规划 Gradio 方案 |
| v0.2 | 2026-06-13 | 按 Gemini 建议重构：弃用 Gradio，纯 HTML/JS + http.server |
| v0.3 | 2026-06-13 | 提取游戏原版素材；新增 F5-F7 规划 |
| v0.5 | 2026-06-13 | v2.0 重构：三层时间线 + JINE + 直播 + F7 |
| v0.6 | 2026-06-13 | 游戏原版账号/UI 1:1 还原 |
| v0.7 | 2026-06-13 | 新增 F8(JINE 互动聊天) 规划 |
| v0.8 | 2026-06-13 | F6.5 弹幕垃圾桶 |
| v0.9 | 2026-06-13 | F8 JINE 互动聊天 + 弹幕修复 + 撤回效果 |
| v1.0 | 2026-06-13 | F9 GitHub Actions + F10 Pages + F11 stress_level + F12 PNG stamp |
| v1.1 | 2026-06-14 | F8 大幅增强：tsundere 提示词重写、文字消息、糖糖贴图回复、F7 JINE 联动、消息持久化、stats/弹幕/天数/用户名/隐私多项修复 |
