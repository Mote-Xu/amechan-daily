# 自训练模型方案 — 超天酱生成器

> 用于替代 DeepSeek V4 API，实现网站公开化。**以效果为唯一优先，不限硬件**。
> 最后更新：2026-06-17

---

## 零、先评估，再训练

**不要直接微调。先跑一轮快速评估确定最佳基座。**

```bash
# 1. 在 AutoDL 租 1× A100 40GB
# 2. 一键搭建: bash eval_setup.sh
#    （自动下载 Qwen 32B + Yi 34B + 启动 vLLM）
# 3. 运行评估: python eval_models.py --all
#    （17 个测试用例 × 3 个模型 = 51 次推理）
# 4. 对比 eval_results.json 中的输出质量
```

评估结果决定下一步：
- Qwen 32B 原版质量接近 DeepSeek → 微调后大概率超越
- 原版差距大（角色崩塌/复读）→ 换基座或加大数据量
- Yi 34B 明显更好 → 改用 Yi 做基座

## 决策总结

| 维度 | 推荐 | 原因 |
|------|------|------|
| 基座模型 | Qwen2.5-32B-Instruct | 中文最强开源模型，14B 太小会丢细节 |
| 微调方式 | 全量微调（非 LoRA） | 角色一致性 > 参数效率，全量更能内化人设 |
| 训练数据 | 1000-2000 条 | 角色丰富度需要足够样本支撑 |
| 云 GPU | 2× A100 80GB 或 4× RTX 4090 | 全量微调 32B 需要 ~60GB |
| 推理部署 | 1× A100 40GB 或 2× RTX 4090 | 32B FP16 推理需 ~64GB，4bit 需 ~20GB |
| 推理框架 | vLLM | 吞吐量最高，兼容 OpenAI API |

**为什么不是 14B？**  
你的 v4 prompt 已经非常复杂——Menhera 人设、XML 标签结构、8 种贴图 × Few-Shot、身体依赖、背景故事渗透。14B 在训练数据不足时会过拟合到表面句式，丢失深层角色逻辑。32B 有足够容量内化"地雷系女友"的内在一致性——什么时候 tsundere、什么时候崩溃、什么时候黏人。

**为什么不是 LoRA？**  
LoRA 只训练 ~2% 参数。角色扮演不是"加个风格插件"——你需要模型从根本上改变输出分布（从通用助手变成病娇女友）。全量微调让所有 32B 参数都参与角色适应。成本高（¥50-100 vs ¥12-24），但效果天差地别。

---

## 一、模型对比

| 模型 | 中文质量 | 角色扮演 | 全量微调显存 | 推理显存 (FP16) | 推理显存 (4bit) | 推理速度 |
|------|:--:|:--:|----------|-------------|-------------|:--:|
| Qwen2.5-14B | ⭐⭐⭐⭐ | ⭐⭐⭐ | ~56GB | ~28GB | ~10GB | 快 |
| Qwen2.5-32B | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ~140GB | ~64GB | ~20GB | 中 |
| Qwen2.5-72B | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ~300GB | ~144GB | ~40GB | 慢 |
| DeepSeek-V3 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 不可微调 | API only | — | 2-8s/次 |

**推荐 Qwen2.5-32B**：中文能力接近 V3，角色扮演有足够容量，推理成本和延迟可接受。

---

## 二、训练数据构造（扩展版）

### 数据量目标

| 类型 | 数量 | 说明 |
|------|------|------|
| 三层时间线 | 400-600 条 | 50 事件 × 8-12 variant |
| JINE 贴图回复 | 200-300 条 | 8 贴图 × 25-35 variant，覆盖 stress 高低 |
| JINE 文字回复 | 300-400 条 | 开放话题 + 情境对话 |
| JINE Release 独白 | 150-200 条 | 自言自语 |
| 超天酱单独推文 | 200-300 条 | 不含阿P，独立推文 |
| 糖糖单独日记 | 200-300 条 | 碎片化，阴暗风 |
| **总计** | **1500-2100 条** | |

### 数据多样性策略

**关键原则**：同一个输入不要只给一个输出。模型需要学会"同一个情绪可以有多种表达"。

```
输入: 阿P向你点了点头表示认可
输出变体:
  - 就这？一丁点诚意都感受不到 [ame_tsun]
  - 嘿嘿...你懂就好 [ame_smile]
  - 突然这么乖？是不是又干了什么坏事 [ame_tsun]
  - ...笨蛋 知道了 [ame_blush]
  - 哼 每次都用这招 但我就是吃这套 烦死了
```

每个输入提供 5-8 个变体，训练时随机采样。这防止模型变成"复读机"。

### 数据格式（ShareGPT 多轮对话）

```json
{
  "conversations": [
    {"from": "system", "value": "完整的 JINE_REPLY_SYSTEM prompt..."},
    {"from": "human", "value": "阿P非常敷衍地夸了你一句「太强了」，明显没走心。"},
    {"from": "gpt", "value": "一丁点诚意都感受不到"}
  ]
}
```

### 数据来源

1. **现有 `data/feed.json` 精华**：从历史生成中筛选 100-200 条高质量输出
2. **DeepSeek V4 API 批量扩充**：对每个模板用 temperature 0.7-1.0 各生成 10-15 条
3. **游戏原版台词**：从 NSO 提取真实 JINE 对话作为 Few-Shot 锚点
4. **人工筛选**：剔除重复、OOC、meta 评论、"你在学我说话"类输出

---

## 三、训练配置（全量微调）

### 环境

```bash
# AutoDL 租用：2× A100 80GB 或 4× RTX 4090
pip install transformers datasets accelerate deepspeed flash-attn
```

### DeepSpeed ZeRO-2 配置（全量微调 32B 需要 ~140GB → ZeRO-2 分片）

```python
# train.py
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
import torch

model_name = "Qwen/Qwen2.5-32B-Instruct"

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
    # 不用量化——全量微调用 BF16
)

training_args = TrainingArguments(
    output_dir="./amechan-qwen-32b",
    num_train_epochs=2,              # 全量微调 2 轮足够，3 轮会过拟合
    per_device_train_batch_size=2,   # ZeRO-2 下有效 batch 取决于 GPU 数
    gradient_accumulation_steps=8,   # 有效 batch = 2 × 8 × num_gpus
    learning_rate=1e-5,              # 全量微调学习率要低（比 LoRA 低一个数量级）
    warmup_ratio=0.05,
    lr_scheduler_type="cosine",
    bf16=True,
    logging_steps=10,
    save_steps=200,
    save_total_limit=2,
    deepspeed="./ds_config_zero2.json",  # ZeRO-2 配置
    gradient_checkpointing=True,         # 节省显存
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    tokenizer=tokenizer,
)

trainer.train()
model.save_pretrained("./amechan-qwen-32b-final")
```

### DeepSpeed ZeRO-2 配置

```json
{
  "zero_optimization": {
    "stage": 2,
    "offload_optimizer": {"device": "cpu"},
    "allgather_partitions": true,
    "reduce_scatter": true,
    "overlap_comm": true,
    "contiguous_gradients": true
  },
  "bf16": {"enabled": true},
  "train_micro_batch_size_per_gpu": 2,
  "gradient_accumulation_steps": 8,
  "wall_clock_breakdown": false
}
```

### 训练资源估算

| 配置 | 显存需求 | AutoDL 价格 | 训练时长 |
|------|---------|------------|---------|
| 2× A100 80GB | ~70GB/卡（ZeRO-2分片） | ~¥30/h | ~3-5h |
| 4× RTX 4090 24GB | ~22GB/卡（ZeRO-2分片） | ~¥10/h | ~6-8h |
| 8× RTX 4090 24GB | ~22GB/卡 | ~¥20/h | ~3-4h |

**推荐 2× A100**：稳定、快速、显存余量大。

---

## 四、推理部署

### 方案 A：vLLM + AWQ 4-bit（推荐）

```bash
# 量化模型
python -m awq.entry --model ./amechan-qwen-32b-final \
    --q_bit 4 --q_group_size 128 --output ./amechan-32b-awq

# 启动 vLLM（1× A100 40GB 或 2× RTX 4090）
python -m vllm.entrypoints.openai.api_server \
    --model ./amechan-32b-awq \
    --dtype auto \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.90 \
    --port 8931
```

### 方案 B：SGLang（更快，实验性）

```bash
python -m sglang.launch_server \
    --model ./amechan-32b-awq \
    --host 0.0.0.0 --port 8931
```

### 推理速度预期（32B AWQ 4-bit, 1× A100）

| 任务 | Token 数 | 速度 |
|------|---------|:--:|
| 超天酱推文 | ~80 | 0.8-1.5s |
| 糖糖日记 | ~60 | 0.6-1.2s |
| JINE 贴图回复 | ~30 | 0.3-0.6s |
| JINE 文字回复 | ~60 | 0.6-1.2s |
| F7 Release 独白 (3条) | ~100 | 1-2s |
| 三层时间线 (单事件) | ~800 | 8-15s |

文字回复从 DeepSeek API 的 2-8s → **0.6-1.2s**，且延时稳定（无网络抖动）。

### 月常成本

| 方案 | 配置 | 价格 |
|------|------|------|
| AutoDL 按量 | 1× A100 40GB | ~¥4.5/h → ~¥500/月（日均 4h） |
| AutoDL 包月 | 1× A100 40GB | ~¥2000-3000/月 |
| 轻量云服务器 | 1× RTX 4090 | ~¥600-1000/月 |

---

## 五、前端改动

```js
// 只需改 API endpoint——v4 架构已是无状态 JSON 交互
// 从 DeepSeek API（通过 Python 代理）
fetch('/api/jine/chat', { body: JSON.stringify({text, sticker, history}) })

// 改为直连 vLLM（OpenAI 兼容 API）
fetch('http://gpu-server:8931/v1/chat/completions', {
    body: JSON.stringify({
        model: 'amechan-32b',
        messages: [
            {role: 'system', content: 'JINE_REPLY_SYSTEM...'},
            {role: 'user', content: '阿P向你点了点头...'}
        ],
        temperature: 0.85
    })
})
```

或者保持 `server.py` 做代理换 endpoint——前端零改动。

---

## 六、风险与缓解

| 风险 | 概率 | 缓解 |
|------|:--:|------|
| 32B 全量微调 2 轮后角色崩塌（灾难性遗忘） | 中 | 混入 10% 通用中文语料（维基/新闻）做正则化 |
| 训练数据不够多样化→输出重复 | 中 | 每个输入 5-8 变体 + temperature 采样 |
| 推理成本超出预算 | 低 | 降级到 14B AWQ（¥300/月）或混合部署 |
| 中文生僻场景出现乱码 | 低 | 训练数据以中文为主，注入少量日文 emoji |
| 模型不遵循 JSON 格式输出 | 低 | 训练数据中 30% 用 JSON，推理时用 guided generation |

---

## 七、执行路线

```
第1-2周：数据工程
  ├── 精选历史产出 100-200 条
  ├── DeepSeek V4 API 批量生成 1500-2000 条变体
  ├── 提取游戏原版 JINE 台词作为 Few-Shot 锚点
  └── 人工清洗 + 格式转换

第3周：训练
  ├── AutoDL 租 2× A100 80GB
  ├── 全量微调 Qwen2.5-32B, ~3-5h
  ├── 评估 100 条测试输出（角色一致性/多样性/OOC率）
  └── 不满意 → 回第2周加数据

第4周：部署
  ├── AWQ 4-bit 量化
  ├── vLLM 部署到 AutoDL
  ├── server.py 切 endpoint
  └── 灰度：先 JINE 聊天用本地模型，时间线保持 API

第5周+：迭代
  ├── 收集真实用户反馈
  ├── 根据实际对话数据补充训练集
  └── 每月微调一轮持续提升
```

---

## 八、总成本

| 阶段 | 项目 | 费用 |
|------|------|------|
| 数据生成 | DeepSeek API × 2000 次 | ¥100-200 |
| 训练 | 2× A100 80GB × 5h | ¥150-200 |
| 推理 | 1× A100 40GB 按量，首月 | ¥500-800 |
| **首月合计** | | **¥750-1200** |
| **稳定运行** | 月常推理 + 每月微调 | ¥600-1000/月 |

对比 DeepSeek V4 API 公开部署（不可行——API Key 暴露）：**自训练是唯一能公开化的路线**。
