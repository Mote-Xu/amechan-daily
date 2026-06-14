# 项目总结 — 超天酱日常推文小站

> 发给 Gemini 的完整项目总结。目标：请 AI 给方向、找盲点、提建议。
> 最后更新：2026-06-16 (v2.7.1 事故后)

---

## 事故摘要（2026-06-16）

Claude 在修改 index.html 时，Python 脚本字符串匹配错误导致文件膨胀到 268 万行。`git checkout` 恢复后，`git stash` + `git stash drop` 意外将 v2.7.1 的所有改动（Python 后端 + 前端 JS）全部抹掉——因为 git 只 commit 到 v2.3。

随后 Claude 从 v2.3 重建了：
- Python 后端：prompts.py / generator.py / server.py / feed.py → v2.7.1
- 前端 index.html：Webcam Engine + JINE 统一聊天 + CSS 补丁
- 表情包：从用户本地 `E:\Desktop\webcam\表情包_游戏原版` 恢复游戏原版

**教训**：git 提交频率过低，两个月间的改动全在 working tree 里，一次 stash drop 全丢。

---

## 一句话概述

模拟《主播女孩重度依赖》中超天酱社交账号的轻量 Web 应用。AI 自动以超天酱（和其真实人格糖糖）的语气发推文。纯 HTML/CSS/JS + Python http.server + DeepSeek API。

## 个人背景

[作者]，[学校]。项目目的：和[已移除]创造共同话题。。

## 当前状态：v2.7.1（部分重建）

### 后端（完整 v2.7.1）✅
- JINE_RELEASE_SYSTEM "铁律"格式：禁令打头 + 正反例对照
- generate_jine_release_msgs：单次 API JSON 数组输出，同批不重复
- 滑动窗口防重复：近期 6-8 条注入为负例
- frequency_penalty=0.95 + presence_penalty=0.8
- 糖糖身体依赖人设（ecchi 侧）
- pop_from_pool 配对释放（Poketter + Diary）
- hidden_pool 要求 3+2 平衡

### 前端（v2.3 base + 关键补丁）⚠️
- ✅ Webcam Canvas Engine（18状态，rAF，点击→smile，2轮自动换）
- ✅ JINE 统一聊天 + 微信式时间分割线 + 已读延迟
- ✅ 表情包：游戏原版 16 张（8 糖糖 + 8 阿P）
- ✅ BGM 懒加载 + 音量 0.15
- ✅ 气泡三角尾巴对齐（flex-start + top:10px）
- ⚠️ 弹幕：v2.3 原版（CSS 动画驱动），未升到 v2.7.1
- ⚠️ 表情包 96×96 强制尺寸：CSS 部分应用
- ⚠️ 多行输入 textarea：HTML 已改，JS sendText 是 v2.3 版
- ⚠️ 空状态图标：部分替换为游戏像素图

### 已推送到 GitHub
- ✅ 后端 4 文件 + 前端 index.html + 游戏原版表情包 + .gitignore
- ✅ .gitignore 排除：bgm/(188MB WAV)、webcam/(84帧)、_extracted/(270+纹理)

### 未推送（本地就绪）
- 无。所有改动已 commit。

---

## 技术栈

| 组件 | 技术 |
|------|------|
| LLM | DeepSeek API (deepseek-v4-pro) |
| 前端 | 纯 HTML/CSS/JS，零框架零构建 |
| 后端 | Python `http.server` |
| 存储 | JSON（服务端）+ localStorage（存档） |
| 环境 | WSL2, Python 3.11, conda: deepseek_v4_api |

## 启动

```bash
conda activate deepseek_v4_api
cd /mnt/e/Desktop/Deepseek_V4_API/amechan-daily
python server.py
# → http://127.0.0.1:8930
```

## 设计原则

1. 克制的互动：F7 按钮触发
2. 超天酱人设保护：Poketter 绝口不提阿P
3. 糖糖 tsundere + 身体依赖尺度
4. 还原游戏质感：素材优先游戏原版
