# amechan-daily — 超天酱日常推文小站

> DeepSeek V4 驱动的超天酱模拟账号，自动生成双人格推文。
> 最后更新：2026-06-17 (v2.7.2)

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
  prompts.py               # 铁律JINE(场景剥夺+严禁meta) + 滑动窗口 + 身体依赖人设
  generator.py             # 单次API JSON数组 + freq/presence_penalty
  feed.py                  # pop_from_pool 强制配对(缺一返回空)
  server.py                # HTTP 服务器 v2.7.2 (后台线程生成首条)
  static/
    index.html             # 前端(单文件 ~2200行, 零框架)
    img/stamps/            # 游戏原版贴图 16张
    img/webcam/            # 18状态帧 (gitignored)
    img/bgm/               # OST WAV 13首 (gitignored, 188MB)
  data/feed.json           # 推文持久化
```

## 核心机制

- **L1 Poketter**: 超天酱公开推文，绝口不提阿P
- **L2 Diary**: 糖糖私密日记
- **L3 JINE**: 糖糖→阿P 私信，统一聊天流 + 回复队列
- **Webcam**: Canvas 18状态, rAF, 点击→smile, 2轮自动换, 发型稀有池(10%)
- **弹幕**: CSS left 动画, 8条, 48px栏, 垃圾桶消除

## v2.7.2 改动记录

| 日期 | 改动 |
|------|------|
| 6/17 | fetchTimeline 日志+退避重试+空数据快速轮询; renderFeed 空html兜底 |
| 6/17 | 弹幕: translateX→left动画, 5→8条, 34→48px, 延迟缩短 |
| 6/17 | Webcam init 延迟400ms; 状态切换不清空canvas; 发型稀有池 |
| 6/17 | JINE_RELEASE_SYSTEM 场景剥夺; JINE_REPLY 严禁meta+高频限制 |
| 6/17 | server.py 首条生成→后台线程; typing indicator去头像 |
| 6/17 | startAmeResponse/endAmeResponse webcam同步; 打字锁auto-cycle |
| 6/17 | sendText/sendSticker 移除jineSending锁→回复队列_startReplyCycle |
| 6/17 | fetch 15s AbortController超时; checkTriggerWords补定义 |

## 已知顽固问题

| # | 问题 | 状态 |
|---|------|:--:|
| 1 | 刷新页面推博不加载（可能加载慢） | 🔴 |
| 2 | JINE 发文字后偶尔卡住 | 🔴 |
| 3 | 弹幕看不到 | 🔴 |
| 4 | 部分 CSS 细节 (v2.3 遗留) | 🟡 |

## 设计原则

1. 克制的互动: F7 按钮触发
2. 超天酱人设保护: Poketter 绝口不提阿P
3. 糖糖 tsundere + 身体依赖尺度
4. 还原游戏质感: 素材优先游戏原版
