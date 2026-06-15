# 需求文档 — 超天酱日常推文小站

> 版本：v2.8 · 最后更新：2026-06-16 (v2.8.0)

## 核心功能需求（P0）

| ID | 功能 | 目标 | 状态 |
|----|------|------|:--:|
| F7 | 戳一戳 | 每次稳定释放 1 P+1 D，立刻渲染 | 🟢 |
| F8 | JINE 聊天 | 即时响应，高质量回复，不丢消息 | 🟢 |

## v2.8 已解决

1. ~~戳一戳 pool 空时需要两次 API 调用（generate + release）~~ → 水位线后台补池
2. ~~JINE 回复总延迟 3.5-15s（API 2-8s + 打字延迟）~~ → 耗时重叠，remainWait = max(0, expectedTyping - apiDuration)
3. ~~对话感泄漏（meta 评论）~~ → 温度 0.85→0.7 + 强化 prompt
4. ~~localStorage 与服务器 feed.json 的 JINE 记录不同步~~ → 后端无状态，前端单源

## 残余问题

1. 弹幕偶尔消失
2. 刷新后偶发发不了消息

## 约束

- conda `deepseek_v4_api`，Python 3.11，DeepSeek v4-pro
- 纯 HTML/CSS/JS，零框架
- 超天酱禁提阿P/糖糖
