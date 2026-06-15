# 需求文档 — 超天酱日常推文小站

> 版本：v3.2 · 最后更新：2026-06-16

---

## P0：架构稳定性 ✅ 全部完成

| ID | 功能 | 目标 | 状态 |
|----|------|------|:--:|
| F7 | 戳一戳 | 单 POST 瞬间释放，pool 空时后台自动补池 | 🟢 |
| F8 | JINE 聊天 | 微聚合窗口 + 打断重发 + 无状态后端 | 🟢 |

### 已解决的架构问题
- ~~pool 空时两次 API（generate + release）~~ → 水位线后台补池
- ~~JINE 延迟 3.5-15s~~ → 耗时重叠 + 聚合窗口
- ~~逐条回复僵硬~~ → 微聚合窗口，一次回复整个 batch
- ~~无限回复死循环~~ → `_batchSentIdx` 指针防重复
- ~~贴图被 AI 理解为省略号~~ → 发送实际标签 `[好][嘤嘤]`
- ~~硬编码触发词破坏沉浸~~ → 全部删除，100% AI 回复
- ~~localStorage 与服务器不同步~~ → 后端无状态
- ~~状态栏溢出~~ → `flex-wrap:nowrap` + 缩小间距
- ~~BGM 不自动播放~~ → 首次点击自动启动
- ~~JINE 背景用渐变~~ → 换成游戏原图 `JINEBG_266x388.png`
- ~~贴图 `[stamp:xxx]` 泄漏到文本~~ → 前端后端双解析

---

## P1：内容质量 🔴 当前重点

| ID | 领域 | 目标 |
|----|------|------|
| C1 | JINE 聊天 | 回复要有糖糖风格——傲娇、病娇、撒娇、身体依赖、思维跳跃。杜绝平淡客套 |
| C2 | 推博 Feed | 超天酱推文 + 糖糖日记有反差感、故事性、真实网红/少女感 |
| C3 | 弹幕 | 应援和吐槽文案更有网感、更搞笑、更多样 |

### 关键文件
- `prompts.py` — 所有人设 prompt（`JINE_REPLY_SYSTEM`, `JINE_TEXT_REPLY_SYSTEM`, `KANGEL_PERSONA`, `AME_DIARY_PERSONA`, `AME_JINE_PERSONA`, `get_timeline_prompt()`）
- `prompts.py` — 弹幕池 `EVENT_POOL`
- `static/index.html` — 前端弹幕文案池 `DANMAKU_OEN` / `DANMAKU_TUCAO`

### 评判标准
- 糖糖的回复是否有"游戏原版"的味儿——不是客服、不是 ChatGPT、不是普通傲娇模板
- 推文是否有信息量——看完能脑补出她今天经历了什么
- 弹幕是否像真实直播间的弹幕——有梗、有节奏、有情绪

---

## 残余问题（低优先级）
1. 弹幕 CSS 动画偶尔消失
2. 刷新后偶发发不了消息

## 约束
- conda `deepseek_v4_api`，Python 3.11，DeepSeek v4-pro
- 纯 HTML/CSS/JS，零框架
- 超天酱禁提阿P/糖糖（公开推文层面）
