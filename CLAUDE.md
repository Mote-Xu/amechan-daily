# amechan-daily — 超天酱日常推文小站

> DeepSeek V4 驱动的超天酱模拟账号。
> 最后更新：2026-06-16 (v2.7.2)

## 启动

```bash
conda activate deepseek_v4_api
python server.py  # → http://127.0.0.1:8930
```

## 当前状态

| 功能 | 状态 |
|------|:--:|
| F7 戳一戳 | ✅ 对释放+自动补池 |
| JINE 互动聊天 | 🟡 偶有卡顿 |
| 推博 Feed | ✅ 每存档独立+排序 |
| JINE release 独白 | 🟡 仍有对话泄漏 |
| 弹幕 | 🟡 72px/3轨/12条 |
| 多存档 | ✅ |
| BGM | ✅ 13首OST |

## 已知问题

| # | 问题 |
|---|------|
| 1 | JINE release 对话泄漏 |
| 2 | 刷新后偶发发不了消息 |
| 3 | 弹幕偶尔消失 |
