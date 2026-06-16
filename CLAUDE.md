# amechan-daily — 超天酱日常推文小站

> DeepSeek V4 驱动的超天酱模拟账号。
> 最后更新：2026-06-17 (v4.0)

## 启动

```bash
conda activate deepseek_v4_api
python server.py  # → http://127.0.0.1:8930
```

## 核心功能状态

| 功能 | 状态 | 备注 |
|------|:--:|------|
| F7 戳一戳 | 🟢 | v4: 前端管 pool，本地取即时显示，后端只生成 JINE 消息 |
| JINE 聊天 | 🟡 | v3.3 Menhera prompt 已上线，meta 点评行为待进一步消除 |
| 推博 Feed | 🟡 | 糖糖日记碎片化进步明显，超天酱推文仍偏模板偶像风 |
| 弹幕 | 🟢 | 应援 30 + 吐槽 39，池子已扩 |
| 多存档 | ✅ | 独立 timeline+JINE+stats |

## 架构 (v4 — 无状态)

```
浏览器 localStorage (所有数据)
  ↕ POST JSON
Python ThreadingHTTPServer (纯无状态)
  ↕
DeepSeek V4-pro API
```

- **前端**：单 HTML，~2400 行，零框架。Pool/时间线/JINE 全在 localStorage
- **后端**：`server.py` + `generator.py` + `prompts.py`，不读不写任何文件
- `feed.py` 已清空为存根

### API

| 方法 | 路径 | 调用 DeepSeek |
|------|------|:--:|
| POST | `/api/generate` | ✅ 生成 timeline+pool，返回 JSON |
| POST | `/api/release` | ✅ 接收 poke_text，生成 JINE 释放消息 |
| POST | `/api/jine/chat` | ✅ 接收 text+sticker+history，返回回复 |
| GET | 其他 | ❌ 返回空（前端管数据） |

## Prompt 架构 (v3.3)

所有 JINE prompt 使用 XML 标签结构，地雷系 (Menhera) 人设：
- `JINE_REPLY_SYSTEM` — 贴图回复，temp 0.85
- `JINE_TEXT_REPLY_SYSTEM` — 文字回复，temp 0.85
- `JINE_RELEASE_SYSTEM` — F7 释放消息，temp 0.5
- 硬禁："哼/揍你哦/笨蛋"、点评贴图/说话方式、找借口
- 关键规则：猫贴图 = 阿P本人，直接回应情绪，不分析表情包

## 当前问题

1. JINE 仍有 meta 点评痕迹（"一只猫就想糊弄我"类）
2. 超天酱推文偏模板偶像风，信息量不足
3. JINE 聊天滚动问题（已提交 Gemini）
4. 弹幕 CSS 偶尔消失

## 🔴 下一步：公网部署 + 内容深化

见 `REQUIREMENTS.md` P2 + `GEMINI_PROMPT.md`
