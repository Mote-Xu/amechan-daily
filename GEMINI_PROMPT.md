# 超天酱模拟账号 — Gemini 全面审查 v4.2

> v4.2：名字固化修复 + Cloudflare Tunnel 公网部署已完成。
> 请重点审查：老电脑迁移方案、残余问题、以及内容质量。

---

## 一、项目概览

模拟《主播女孩重度依赖》糖糖/超天酱的社交媒体。纯前端 HTML + Python http.server 后端，DeepSeek V4-pro。

三层内容：Poketter 推博（超天酱推文 + 糖糖日记）、JINE 私聊（糖糖↔阿P）、直播间弹幕。

## 二、架构（v4.2 无状态 + 后端消毒）

- 前端 localStorage 管理所有数据（时间线、pool、JINE 历史）
- 后端纯计算：接收参数 → sanitize → 拼 prompt → 调 DeepSeek → sanitize → 返回 JSON
- 不读不写任何文件
- ThreadingHTTPServer 多线程 + CORS
- Prompt Injection 防御：11种正则模式 + system_warning 标签隔离
- 模板词后端硬替换：`_sanitize_template_phrases()` 正则匹配→随机替换（手冰了、自造名字等）
- Turnstile 框架已搭建（缺 Site Key）
- 限频代码已有（本地关闭）

### 部署架构（已完成）

```
用户 → https://amechan.mote-pal.xyz → Cloudflare → Named Tunnel → :8930
   域名: NameSilo $3/年          免费 HTTPS       UUID: 51cc70a8...   当前：本机
                                                                     计划：老家 i5-6500
```

- 不需要公网 IP（Tunnel 从电脑主动外连 Cloudflare）
- SSL/TLS 完全免费（Cloudflare 提供，Let's Encrypt 都不需要）
- API Key 天然保护（Key 只在服务器端环境变量，前端永远不可见）

## 三、Prompt 架构（v4.2）

XML 标签结构，地雷系 (Menhera) 人设。关键升级：

### 3.1 名字固化（v4.2 新增）
**问题**：DeepSeek 高 temp(0.85) 会幻觉自造玩家名字（如"混音"）。
**修复**：
- negative_rules 第 0 条：硬禁非"阿P"称呼（混音/阿音/喂/那个谁等）
- `_sanitize_template_phrases()` 后端正则兜底替换

### 3.2 Sticker→动作翻译
贴图不再以"猫咪贴图"形式进入 Prompt。后端 STICKER_MAP 将 8 个 sticker 翻译为阿P的真实动作。

### 3.3 语境判断 (core_drives)
阿P说短句不等于拒绝——先判断语境再反应。不是关键词触发器。

### 3.4 模板词硬禁止 + 后端替换
Prompt 层硬禁 + 代码层正则替换（手冰了→随机冷感表达，幻觉名字→阿P）。

### 3.5 Prompt Injection 防御
`<system_warning>` + `sanitize_user_input()` 11种正则模式。

## 四、v4.2 修复

| # | 问题 | 修复 | 文件 |
|---|------|------|------|
| 15 | AI自造玩家名字("混音") | negative_rules硬禁+后端正则替换 | prompts.py + generator.py |

## 五、v4.1 修复清单

| # | 问题 | 修复 | 文件 |
|---|------|------|------|
| 1-14 | （见之前版本）| ... | ... |

## 六、当前问题（请求审查）

### 老电脑迁移
1. 家中 i5-6500 8GB Windows 老电脑，计划暑假回改装 Ubuntu Server。过渡期先远程配 Windows + AnyDesk。
2. Windows 做服务器的坑：自动更新重启、休眠。应对：禁止更新+自动登录+BIOS来电开机+NSSM注册服务。
3. 暑假换 Linux 后：systemd 管理 server + cloudflared，SSH 远程，30分钟搞定。

### 部署
4. Turnstile 前端如何集成到纯 HTML？（后端框架已就绪）
5. 频率限制参数建议（间隔/日上限）？
6. 是否需要加一个简单的 API Key（非 DeepSeek 的，是自己服务的鉴权）？

### 内容质量
7. JINE 回复质量是否还有AI痕迹？
8. 推博的表里反差是否足够？

### 前端
9. 弹幕 CSS 偶尔消失 — 可能的原因？
