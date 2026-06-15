# amechan-daily — 超天酱日常推文小站

> DeepSeek V4 驱动的超天酱模拟账号，自动生成双人格推文。
> 最后更新：2026-06-17 (v2.7.1)

## 启动

```bash
conda activate deepseek_v4_api
cd /mnt/e/Desktop/Deepseek_V4_API/amechan-daily
python server.py
# → http://127.0.0.1:8930
```

## 架构

```
amechan-daily/
  prompts.py               # 铁律JINE(白名单) + 滑动窗口 + 身体依赖人设
  generator.py             # 单次API JSON数组 + freq/presence_penalty
  feed.py                  # pop_from_pool 强制配对(缺一返回空)
  server.py                # HTTP 服务器 v2.7.1
  static/
    index.html             # 前端(单文件 HTML/CSS/JS, v2.3基座+v2.7.1补丁)
    img/stamps/            # 游戏原版贴图 16张
    img/webcam/            # 18状态帧 (gitignored)
    img/bgm/               # OST WAV 13首 (gitignored, 188MB)
  data/feed.json           # 推文持久化
```

## 核心机制

| 项目 | 超天酱 | 糖糖 |
|------|--------|------|
| 昵称 | 🎀超绝最可爱🎁天使酱 | 💙糖糖💙 🔑 |
| @用户名 | @x_angelkawaii_x | @raincandy_U |

- **L1 Poketter**: 超天酱公开推文，绝口不提阿P
- **L2 Diary**: 糖糖私密日记
- **L3 JINE**: 糖糖→阿P 私信，统一聊天流

## v2.7.1 功能

- Canvas Webcam (18状态, rAF, 点击→smile, 2轮自动换, 480px)
- JINE 统一聊天流 + 微信式时间分割线 + 已读延迟 2.2s
- 铁律 JINE release prompt (白名单模式, temperature 0.5)
- 多存档系统 (SaveManager + localStorage + 弹窗UI)
- 游戏原版表情包 16张 (96×96)
- BGM 13首 (懒加载, 0.15音量)
- pop_from_pool 强制配对 (Poketter+Diary 缺一不可)
- 糖糖身体依赖人设 + 滑动窗口防重复
- 266:388 游戏比例面板
- 多行输入 (textarea, Enter发送/Shift+Enter换行)

## 已知问题

| 问题 | 状态 |
|------|:--:|
| 弹幕不可见/不可点击 | 🟡 |
| 刷新页面推博不加载 | 🟡 |
| JINE release 偶尔泄漏上下文 | 🟡 |
| 部分 CSS 细节 (v2.3 遗留) | 🟡 |

## 设计原则

1. 克制的互动: F7 按钮触发
2. 超天酱人设保护: Poketter 绝口不提阿P
3. 糖糖 tsundere + 身体依赖尺度
4. 还原游戏质感: 素材优先游戏原版
