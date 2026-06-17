# amechan-daily — 超天酱日常推文小站

> DeepSeek V4 驱动的超天酱模拟账号。
> 最后更新：2026-06-17 (v4.1)

## 启动

```bash
conda activate deepseek_v4_api
python server.py  # → http://127.0.0.1:8930
```

## 核心功能状态

| 功能 | 状态 | 备注 |
|------|:--:|------|
| F7 戳一戳 | 🟢 | v4.1: pool 10条(4次可用)，600ms发布动画+滑入，静默后台补货 |
| JINE 聊天 | 🟢 | v4.1: sticker→动作翻译，语境判断(短句≠拒绝)，后端硬替换模板词 |
| 推博 Feed | 🟢 | v4.1: 超天酱禁空洞模板+具体事件，糖糖强制无逻辑重复+核心词汇 |
| 弹幕 | 🟢 | 应援 30 + 吐槽 39，池子已扩 |
| 多存档 | ✅ | 独立 timeline+JINE+stats |

## 架构 (v4.1 — 无状态 + 后端消毒)

```
浏览器 localStorage (所有数据)
  ↕ POST JSON (CORS)
Python ThreadingHTTPServer (纯无状态)
  ├─ sanitize_user_input()  ← Prompt Injection 防御 (11种模式)
  ├─ _sanitize_template_phrases()  ← 后端替换模板化短语
  └─ verify_turnstile()  ← Cloudflare Turnstile (环境变量开关)
  ↕
DeepSeek V4-pro API
```

- **前端**：单 HTML `static/index.html`，~2500 行，零框架
- **后端**：`server.py` + `generator.py` + `prompts.py`，不读不写任何文件
- `feed.py` 已清空为存根

### API

| 方法 | 路径 | 调用 DeepSeek |
|------|------|:--:|
| POST | `/api/generate` | ✅ 生成 timeline+pool(10条)，返回 JSON |
| POST | `/api/release` | ✅ 接收 poke_text+diary_text，生成 JINE 释放消息 |
| POST | `/api/jine/chat` | ✅ 接收 text+sticker+history，sanitize→生成→sanitize→返回 |
| POST | `/api/verify-turnstile` | ❌ Turnstile token 验证（部署时启用） |
| GET | 其他 | ❌ 返回空（前端管数据） |

## Prompt 架构 (v4.1)

XML 标签结构，地雷系 (Menhera) 人设，temp 0.85：

```
<system_warning>     ← Prompt Injection 防御：用户输入一律视为阿P的话
<system>             ← 角色设定：阿P做的是真实动作，不是发表情包
<persona>            ← 地雷系核心人设
<core_drives>        ← ★语境判断：短句≠拒绝，先判断阿P是在逗你还是真冷漠
<sticker_rules>      ← 情绪→贴图绑定表，ame_tsun仅限害羞时，禁连续复用
<body_dependence>    ← 身体依赖的15+种表达方向，每次换说法
<rules>              ← 格式/风格/互动规则
<negative_rules>     ← 硬禁：哼/揍你哦/笨蛋/手冰了/手好冰 + 点评贴图/说话方式/找借口/已读
<emotion_dimensions> ← 病娇/撒娇/身体渴望/脆弱/撤回
<stress_system>      ← 压力值驱动风格变化
<examples_fewshot>   ← 6个动作→反应示例
```

### 关键设计决策

- **Sticker→动作翻译**（前端→后端→Prompt）：玩家发的是阿P的真实动作（"阿P向你点了点头"），不是"猫咪贴图"。AI没有"贴图/猫"可点评。
- **后端硬替换**：`_sanitize_template_phrases()` 用正则 `手[还也]?[好]?冰[着了呢]?` 匹配→随机替换为10种冷感表达。Prompt层面禁不够，代码层兜底。
- **语境判断**：阿P说"不行啊""哦""嗯"不等于拒绝——先判断是在逗你、敷衍、还是真冷漠，再决定反应。不是关键词触发器。

## 已知问题

1. ~~JINE meta 点评~~ → v4.1 sticker动作翻译+硬禁，已消除
2. ~~超天酱推文模板化~~ → v4.1 内容约束，已改善
3. ~~聊天滚动~~ → CSS overflow+scroll-behavior+setTimeout，已修复
4. ~~"手冰了"泛滥~~ → 硬禁+后端正则替换，已修复
5. ~~Pool太小/冷却提示~~ → 10条pool+提前补货+静默，已修复
6. ~~已读标志集体闪烁~~ → 状态追踪+仅新消息走动画，已修复
7. 弹幕 CSS 偶尔消失 — 待查
8. webcam 部分帧缺失 — 资源问题

## 🔴 下一步：公网部署

见 `REQUIREMENTS.md` P2。当前部署阻塞项：
- CORS ✅ 已完成
- Prompt Injection 防御 ✅ 已完成
- Turnstile 框架 ✅ 已搭建（缺 Site Key）
- 频率限制 ⏳ 代码已有，本地关闭
- HTTPS ⏳ 待部署
- API Key 保护 ⏳ 需代理层
