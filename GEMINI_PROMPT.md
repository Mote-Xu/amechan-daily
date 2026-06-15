# 项目总结 — 超天酱日常推文小站

> 发给 Gemini 的完整项目总结。最后更新：2026-06-16 (v2.7.2)

---

## ⚠️ 核心功能优先级

| 优先级 | 功能 | 状态 |
|--------|------|:--:|
| **P0** | 糖糖 JINE 私信聊天 | 基本可用，偶有卡顿+对话感泄漏 |
| **P0** | 推博 Feed 时间线 | 可用，每存档独立，排序已修复 |
| **P0** | 戳一戳（F7）更新动态 | 可用，对释放+自动补池 |

---

## 启动

```bash
conda activate deepseek_v4_api
python server.py  # → http://127.0.0.1:8930
```

## 技术栈

纯 HTML/CSS/JS 单文件 (~2400行) + Python `http.server` + DeepSeek API + localStorage/JSON

---

## 当前仍存在的问题

### 1. JINE 偶尔发不了消息 🟡
刷新页面后有时输入文字/点贴图无反应。已加 try-catch + console.log，需 F12 定位。

### 2. JINE release 对话感泄漏 🔴
F7 后糖糖主动发的 JINE 消息偶尔仍带对话感（"你在学我说话？""揍你哦！""才不是特意发给你看的"）。已做：
- 系统 prompt 重写为 5 种自言自语格式
- 用户 prompt 开头场景剥夺
- 禁止"你"字+问句
- 用户 prompt 加了 `🚫 底线` 块

### 3. 弹幕偶尔消失 🟡
72px/3轨/12条，refreshDanmaku 已不再重置动画。

---

## 最新改动摘要

- pop_from_pool 恢复成对释放
- sendText/sendSticker try-catch 保护
- renderFromCache 排序 newest-first
- 已读标记改为 debounced 统一显示
- 所有 prompt 加了"你念经呢""那是我发的"到禁用列表
- BGM 播放区美化（胶囊栏+emoji图标）
