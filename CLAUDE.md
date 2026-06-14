# amechan-daily — 超天酱日常推文小站

> DeepSeek V4 驱动的超天酱模拟账号，自动生成双人格推文。
> 最后更新：2026-06-16 (v2.7.1)

## 项目定位

模拟《主播女孩重度依赖》中「超天酱」社交账号的轻量 Web 应用。AI 自动生成超天酱 & 糖糖风格的日常推文，粉紫像素风 feed 展示。

**核心目标**：→ 

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
  prompts.py               # 超天酱/糖糖双人格提示词 + 铁律JINE + 滑动窗口
  generator.py             # 推文生成（DeepSeek API，frequency/presence_penalty）
  feed.py                  # JSON 推文存储（pop_from_pool 配对释放）
  server.py                # HTTP 服务器（API + 静态文件）
  static/
    index.html             # 前端（v2.7.1，Canvas Webcam + 微信时间线 + 多行输入）
    img/
      stamps/              # 游戏原版贴图（糖糖8张 + 阿P 8张 + 猫7张）
      webcam/              # webcam 18状态帧
      bgm/                 # 游戏 OST WAV（13首）
  data/feed.json           # 推文持久化
```

## 核心机制

| 项目 | 超天酱 | 糖糖 |
|------|--------|------|
| 昵称 | 🎀超绝最可爱🎁天使酱 | 💙糖糖💙 🔑 |
| @用户名 | @x_angelkawaii_x | @raincandy_U |

- **L1 Poketter**：超天酱公开推文，绝口不提阿P
- **L2 Diary**：糖糖私密日记
- **L3 JINE**：糖糖→阿P 私信，tsundere 傲娇，合并为单一聊天流

## v2.7.1 功能

- Canvas Webcam（18状态，rAF驱动，点击→smile，2轮自动切换）
- JINE 微信式时间分割线（>5min间隔）
- JINE release 铁律 prompt（单次API JSON数组，防学说话/防泄漏）
- JINE 多行输入（textarea，Enter发送/Shift+Enter换行）
- 已读延迟亮起
- 266:388 游戏比例面板
- BGM 懒加载（188MB WAV不阻塞首屏）
- 表情包 96×96 统一尺寸
- 空状态游戏原版像素图标
- 滑动窗口防重复 + 身体依赖人设

## 技术栈

| 组件 | 技术 |
|------|------|
| LLM | DeepSeek API (deepseek-v4-pro) |
| 前端 | 纯 HTML/CSS/JS，零框架零构建 |
| 后端 | Python `http.server` |
| 存储 | JSON（服务端）+ localStorage（存档） |
| 环境 | WSL2, Python 3.11, conda: deepseek_v4_api |

## 设计原则

1. 克制的互动：F7 按钮触发，维持艺术装置感
2. 超天酱人设保护：Poketter 绝口不提阿P
3. 糖糖 tsundere + 身体依赖尺度
4. 还原游戏质感：素材优先游戏原版
