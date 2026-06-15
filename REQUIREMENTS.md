# 需求文档 — 超天酱日常推文小站

> 版本：v1.9 · 最后更新：2026-06-17 (v2.7.2)

---

## 功能需求

| ID | 功能 | 状态 |
|----|------|:--:|
| F1 | 双人格推文生成 | ✅ |
| F2 | 推文 Feed 展示 | ⚠️ |
| F3 | 推文持久化（data/feed.json） | ✅ |
| F4 | 粉紫像素风 + CRT + Win95 | ✅ |
| F5 | JINE 私信 Tab（统一聊天流） | ✅ |
| F6 | 直播小组件 + 弹幕 | ⚠️ |
| F7 | 戳一戳释放 hidden_pool + JINE 联动 | ✅ |
| F8 | JINE 互动聊天（贴图+文字） | ⚠️ |
| F9 | GitHub Actions 定时生成 | ✅ |
| F10 | GitHub Pages 静态部署 | ✅ |
| F11 | 情绪系统 + Few-Shot | ✅ |
| F12 | 触发词彩蛋 | ✅ |
| F13 | 多存档系统（localStorage） | ✅ |
| F14 | 游戏原版 JINE Stamp PNG | ✅ |
| F15 | BGM 背景音乐（13首 OST） | ✅ |
| F16 | 糖糖完整人设（身体依赖） | ✅ |
| F17 | Canvas Webcam（18状态，rAF，状态菜单） | ✅ |
| F18 | JINE 铁律 release prompt | ✅ |
| F19 | 微信式时间分割线 + 已读延迟 | ✅ |
| F20 | 多行输入（textarea + Enter） | ✅ |
| F21 | 表情包 96×96 统一尺寸 | ✅ |
| F22 | 266:388 游戏比例面板 | ✅ |
| F23 | BGM 懒加载 | ✅ |

---

## 顽固 Bug（已多次尝试修复）

| # | 问题 | 已尝试 | 状态 |
|---|------|--------|:--:|
| 1 | 刷新后推博不加载 | 退避重试/快速轮询/后台生成首条/加载状态提示 | 🔴 |
| 2 | JINE 发文字偶尔卡住 | AbortController超时/移除全局锁/回复队列 | 🔴 |
| 3 | 弹幕看不到 | translateX→left动画/增加数量/扩大区域/缩短延迟 | 🔴 |

---

## 非功能约束

- conda `deepseek_v4_api`，Python 3.11，DeepSeek v4-pro
- 纯 HTML/CSS/JS，零框架，Python http.server，JSON + localStorage
- 只用中文，超天酱禁提阿P，糖糖 tsundere + 身体依赖尺度
