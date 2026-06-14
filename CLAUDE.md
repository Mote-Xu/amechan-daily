# amechan-daily — 超天酱日常推文小站

> DeepSeek V4 驱动的超天酱模拟账号，自动生成双人格推文。
> 最后更新：2026-06-16 (v2.7.1 事故恢复)

## ⚠️ 事故记录（2026-06-16）

git stash drop 导致 v2.3→v2.7.1 所有未提交改动丢失。后端已完整重建，前端部分重建。详见 GEMINI_PROMPT.md。

**教训**：每次功能完成后立即 commit，不要攒两个月。

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
  prompts.py               # 铁律JINE + 滑动窗口 + 身体依赖人设
  generator.py             # 单次API JSON数组 + freq/penalty
  feed.py                  # pop_from_pool 配对释放
  server.py                # HTTP 服务器 v2.7.1
  static/
    index.html             # 前端（v2.7.1 部分重建中）
    img/stamps/            # 游戏原版贴图（16张）
    img/webcam/            # webcam 18状态帧（gitignored）
    img/bgm/               # OST WAV 13首（gitignored, 188MB）
  data/feed.json           # 推文持久化
```

## v2.7.1 功能清单

**已重建：**
- Canvas Webcam Engine（18状态，rAF，点击→smile，2轮自动换）
- JINE 微信式时间分割线 + 已读延迟
- 铁律 JINE release prompt（单次API JSON数组）
- 糖糖身体依赖人设
- 滑动窗口防重复
- 游戏原版表情包（16张）
- BGM 懒加载 + 0.15 音量
- 气泡三角尾巴对齐

**待恢复（v2.3 旧版）：**
- 弹幕系统（CSS动画驱动，非 v2.7.1 JS tick）
- 表情包 96×96 统一尺寸
- 多行输入 sendText
- 部分 CSS 补丁

## 技术栈

| 组件 | 技术 |
|------|------|
| LLM | DeepSeek API (deepseek-v4-pro) |
| 前端 | 纯 HTML/CSS/JS |
| 后端 | Python `http.server` |
| 存储 | JSON + localStorage |
