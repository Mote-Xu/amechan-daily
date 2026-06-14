# 项目总结 — 超天酱日常推文小站

> 发给 Gemini 的完整项目总结。最后更新：2026-06-17 (v2.7.1)

---

## 事故摘要（2026-06-16）

Claude 修改 index.html 时 Python 脚本失误将文件膨胀到 268 万行。git checkout 恢复后 git stash + git stash drop 将 v2.7.1 未提交改动全丢——git 只 commit 到 v2.3。

从 v2.3 重建了大部分功能。后端 Python 文件后来通过 git fsck --lost-found 从 dropped stash (479f192) 成功恢复原件。前端 index.html 从未进过 git，只能从 v2.3 逐项补。

---

## 当前状态

### 后端（完整 v2.7.1，已从 stash 恢复原件）✅
- JINE_RELEASE_SYSTEM 白名单模式（只允许三类消息）
- generate_jine_release_msgs：单次 API JSON 数组，temperature 0.5
- 滑动窗口防重复（近期 6-8 条负例）
- frequency_penalty=0.95 + presence_penalty=0.8
- 糖糖身体依赖人设
- pop_from_pool 强制配对（缺任何一边返回空触发重新生成）
- hidden_pool 要求 3 Poketter + 2 Diary
- BGM 懒加载 + 0.15 音量

### 前端（v2.3 基座 + v2.7.1 补丁）⚠️
- ✅ Canvas Webcam Engine（18状态，rAF，点击→smile，2轮自动换，480px）
- ✅ JINE 统一聊天流 + 微信式时间分割线 + 已读延迟 2.2s
- ✅ 游戏原版表情包 16张（96×96）
- ✅ 多存档系统（SaveManager + localStorage + 弹窗 UI）
- ✅ BGM 播放器（13首，懒加载）
- ✅ doRelease 写入 SaveManager + JINE 持久化
- ✅ stickerHTML return 修复 + PNG-first DOM 顺序
- ✅ Diary 空状态 icon_ame
- ✅ Google Fonts 移除（阻塞渲染）
- ⚠️ 弹幕：v2.3 CSS 动画驱动，非 v2.7.1 JS tick
- ⚠️ sendText/Enter 键：v2.3 版本
- ⚠️ 部分 CSS 细节未补

### 当前问题（问 Gemini）
- 刷新页面后推博不加载（/api/timeline 返回数据但前端不渲染？）
- 弹幕看不到
- 加载慢
- JINE release 偶尔仍然泄漏上下文（"你看到了""谁要你看了"）

---

## 启动

```bash
conda activate deepseek_v4_api
cd /mnt/e/Desktop/Deepseek_V4_API/amechan-daily
python server.py
# → http://127.0.0.1:8930
```

## 技术栈

| 组件 | 技术 |
|------|------|
| LLM | DeepSeek API (deepseek-v4-pro) |
| 前端 | 纯 HTML/CSS/JS，零框架零构建 |
| 后端 | Python `http.server` |
| 存储 | JSON（服务端）+ localStorage（存档） |
