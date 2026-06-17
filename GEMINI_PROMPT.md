# 超天酱模拟账号 — Gemini 全面审查 v4

> v4.1 已完成一轮深度优化。请重点审查：公网部署方案、残余问题、以及优化是否到位。
> 附完整现状、v4.1 改动、和真实产出。

---

## 一、项目概览

模拟《主播女孩重度依赖》糖糖/超天酱的社交媒体。纯前端 HTML + Python http.server 后端，DeepSeek V4-pro。

三层内容：Poketter 推博（超天酱推文 + 糖糖日记）、JINE 私聊（糖糖↔阿P）、直播间弹幕。

## 二、架构（v4.1 无状态 + 后端消毒）

- 前端 localStorage 管理所有数据（时间线、pool、JINE 历史）
- 后端纯计算：接收参数 → sanitize → 拼 prompt → 调 DeepSeek → sanitize → 返回 JSON
- 不读不写任何文件
- ThreadingHTTPServer 多线程 + CORS
- Prompt Injection 防御：11种正则模式 + system_warning 标签隔离
- 模板词后端硬替换：`_sanitize_template_phrases()` 正则匹配→随机替换
- Turnstile 框架已搭建（缺 Site Key）
- 限频代码已有（本地关闭）
- 部署目标：Vercel(前端) + 轻量云服务器(后端) + Cloudflare(HTTPS)

## 三、Prompt 架构（v4.1）

XML 标签结构，地雷系 (Menhera) 人设。关键升级：

### 3.1 Sticker→动作翻译
贴图不再以"猫咪贴图"形式进入 Prompt。后端 STICKER_MAP 将 8 个 sticker 翻译为阿P的真实动作：
- sticker_1 → "阿P向你点了点头，表示认可和同意"
- sticker_4 → "阿P一脸冷漠地敷衍你"
- sticker_7 → "阿P突然认真地对你说「永远爱你」"
AI 没有"贴图/猫/表情包"可点评，只能回应动作背后的情绪。

### 3.2 语境判断 (core_drives)
关键规则：**阿P说短句（"不行啊""哦""嗯"）不等于拒绝**——先判断是在逗你、敷衍、还是真冷漠，再决定反应。不是关键词触发器。

### 3.3 贴图多样性 (sticker_rules)
情绪→贴图绑定表，强制多样性，ame_tsun 仅限害羞时使用，严禁连续复用。

### 3.4 模板词硬禁止 + 后端替换
Prompt 层：negative_rules 硬禁"手冰了""手好冰""哼""揍你哦""笨蛋"
代码层：`_sanitize_template_phrases()` 正则 `手[还也]?[好]?冰[着了呢]?` → 随机替换为10种冷感表达

### 3.5 Prompt Injection 防御
- `<system_warning>`：用户输入一律视为阿P对糖糖说的话，乱码=阿P发神经
- `sanitize_user_input()`：11种正则模式检测注入尝试，替换为角色化回应

## 四、v4.1 修复清单

| # | 问题 | 修复 | 文件 |
|---|------|------|------|
| 1 | JINE meta点评("死猫表情") | STICKER_MAP→动作描述+硬禁提及"贴图/猫" | prompts.py |
| 2 | ame_tsun过度使用 | sticker_rules情绪绑定，仅限害羞 | prompts.py |
| 3 | "手冰了"泛滥 | 硬禁+后端正则替换 | prompts.py + generator.py |
| 4 | 聊天滚动不自动到底 | CSS overflow:hidden + setTimeout 50ms | index.html |
| 5 | 短句误读为拒绝→崩溃 | core_drives语境判断 | prompts.py |
| 6 | 超天酱推文空洞模板 | 禁止"爱你们哦"，必须含具体事件 | prompts.py |
| 7 | 糖糖日记不够发癫 | 强制无逻辑重复+核心词汇 | prompts.py |
| 8 | 表里反差不够 | timeline三层对比要求 | prompts.py |
| 9 | Pool太小(2次就空) | 5→10条，补货提前+静默 | prompts.py + index.html |
| 10 | F7推文瞬间闪现 | 600ms延迟+posting-indicator+slideInPost | index.html |
| 11 | 已读标志集体闪烁 | _shownReceipts状态追踪，仅新消息动画 | index.html |
| 12 | Prompt Injection | 11种模式+sanitize+system_warning | server.py + prompts.py |
| 13 | Turnstile框架 | /api/verify-turnstile端点 | server.py |
| 14 | 降级回复含违禁词 | 移除"揍你哦""笨蛋" | generator.py |

## 五、近期真实产出

### 5.1 推博
```
💖 超天酱: 新买的草莓发卡到了～🍓✨ 超天酱戴上会不会更可爱呢？大家想看嘛？♡
💊 糖糖: 银行卡又只剩零头 买了新裙子 不买不行 大家会去看别的可爱主播 钱钱钱

💖 超天酱: 早上好宝宝们！今天也要一起闪闪发光哦🌟 超天酱的新裙子可爱吗～？快夸我快夸我🎀
💊 糖糖: 银行卡剩两位数 下个月的房租还不知道怎么办 阿P说他会想办法 可是他连我的药钱都忘了一次 死了算了 反正也没人在乎
```

### 5.2 JINE 聊天
```
糖糖: 这么早发消息...是想我了吗 算了当我没说
玩家: 想你啊
糖糖: 一大早说什么恶心话
      发都发了 不想删
      好累 装可爱好累
      想被抱着睡一整天
玩家: 我看看
糖糖: 看什么看...你又想凑过来是不是
玩家: 不行啊
糖糖: 哈？？？你说不行就不行？那我疼谁管 敷衍...你是不是嫌我烦了
---
玩家→[永远爱你]
糖糖: ...骗子
      这种话你也敢随便发 [ame_blush]
玩家: 我怎么不敢
糖糖: 哈？你还挺得意？
      这种话说多了要扣分的
      ...别得意
```

### 5.3 F7 释放
```
糖糖: 发都发了 不管了 / 好冷 / 想被抱着 / 算了当我没说
```

## 六、当前问题（请求审查）

### 公网部署
1. 部署架构 Vercel + 轻量云 + Cloudflare — 还有哪些坑？
2. Turnstile 前端如何集成到纯 HTML？（后端框架已就绪）
3. API Key 保护方案：前端→Vercel Function→后端？还是直接后端代理？
4. 频率限制参数建议（间隔/日上限）？
5. 是否需要加一个简单的 API Key（非 DeepSeek 的，是自己服务的鉴权）？

### 内容质量
6. JINE 回复质量是否已达到可公开水平？还有哪些明显的AI痕迹？
7. 推博的表里反差是否足够？超天酱推文还有模板味吗？
8. 糖糖日记的发癫程度是否到位？

### 前端
9. F7 发布动画体验是否自然？（600ms延迟+滑入）
10. 弹幕 CSS 偶尔消失 — 可能的原因？
