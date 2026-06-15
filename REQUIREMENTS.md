# 需求文档 — 超天酱日常推文小站

> 版本：v1.7 · 最后更新：2026-06-17 (v2.7.1)

---

## 功能需求

| ID | 功能 | 状态 |
|----|------|:--:|
| F1 | 双人格推文生成 | ✅ |
| F2 | 推文 Feed 展示 | ✅ |
| F3 | 推文持久化（data/feed.json） | ✅ |
| F4 | 粉紫像素风 + CRT + Win95 | ✅ |
| F5 | JINE 私信 Tab（统一聊天流） | ✅ |
| F6 | 直播小组件 + 弹幕 | ✅ |
| F7 | 戳一戳释放 hidden_pool + JINE 联动 | ✅ |
| F8 | JINE 互动聊天（贴图+文字+台词） | ✅ |
| F9 | GitHub Actions 定时生成 | ✅ |
| F10 | GitHub Pages 静态部署 | ✅ |
| F11 | 情绪系统 + Few-Shot | ✅ |
| F12 | 触发词彩蛋 | ✅ |
| F13 | 多存档系统（localStorage） | ✅ |
| F14 | 游戏原版 JINE Stamp PNG | ✅ |
| F15 | BGM 背景音乐（13首 OST） | ✅ |
| F16 | 糖糖完整人设（6封信+身体依赖） | ✅ |
| F17 | Canvas Webcam（18状态，rAF，状态菜单） | ✅ |
| F18 | JINE 铁律 release prompt（白名单） | ✅ |
| F19 | 微信式时间分割线 + 已读延迟 | ✅ |
| F20 | 多行输入（textarea + Enter/Shift+Enter） | ✅ |
| F21 | 表情包 96×96 统一尺寸 | ✅ |
| F22 | 266:388 游戏比例面板 | ✅ |
| F23 | BGM 懒加载（188MB 不阻塞首屏） | ✅ |

---

## 已知 Bug

| # | 问题 | 状态 |
|---|------|:--:|
| 1 | 弹幕不可见/不可点击 | 🟡 |
| 2 | 刷新页面推博不加载 | 🟡 |
| 3 | JINE release 偶尔泄漏上下文 | 🟡 |
| 4 | 部分 CSS 细节未补（v2.3 遗留） | 🟡 |
| 5 | 存档 UI 不支持重命名/导出 | 🟡 |

---

## 非功能约束

- conda `deepseek_v4_api`，Python 3.11，DeepSeek v4-pro
- 纯 HTML/CSS/JS，零框架，Python http.server，JSON + localStorage
- 只用中文，超天酱禁提阿P，糖糖 tsundere + 身体依赖尺度
