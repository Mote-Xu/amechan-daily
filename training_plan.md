# 自训练模型方案 — 超天酱推文生成器

> 用于替代 DeepSeek V4 API，实现网站公开化。
> 最后更新：2026-06-16

---

## 一、推荐方案：Qwen2.5-14B-Instruct + QLoRA

### 为什么选这个

| 维度 | Qwen2.5-14B | DeepSeek V4 API（当前） |
|------|-------------|------------------------|
| 中文能力 | ⭐⭐⭐⭐⭐ 原生中文训练 | ⭐⭐⭐⭐ |
| 角色扮演 | ⭐⭐⭐⭐ 指令跟随强 | ⭐⭐⭐ 偶尔偏离 prompt |
| 推理速度 | 1-3s（4bit, 4090） | 2-8s（网络 + API 排队） |
| 成本 | 0（电费）~¥2/h 租 GPU | ¥0.5-2/次 API 调用 |
| 可控性 | 完全可控（调参/剪枝/量化） | 受限于 API 提供商 |
| 公开部署 | 可以 | 不可以（API Key 暴露） |

### 硬件要求

| 阶段 | GPU | 显存 | 时长 | 成本 |
|------|-----|------|------|------|
| **训练** (QLoRA 4bit) | 1× RTX 4090 24GB | ~16GB | 2-4 小时 | ~¥8-16 (AutoDL) |
| **推理** (AWQ 4bit) | 1× RTX 4090 24GB | ~10GB | 持续 | ~¥2/h (AutoDL) |
| 推理 (备选) | 1× RTX 4070 12GB | ~10GB (GGUF) | 持续 | ~¥1.2/h |

---

## 二、训练数据构造

### 数据量目标

| 类型 | 数量 | 来源 |
|------|------|------|
| 三层时间线（单事件→Poketter+Diary+JINE） | 200-300 条 | DeepSeek V4 API 批量生成 |
| JINE 贴图回复（8种贴图 × 15-20 variants） | 120-160 条 | 游戏原版台词 + API 补充 |
| JINE 文字回复（开放话题） | 100-200 条 | API 生成 + 手动筛选 |
| JINE Release 独白（自言自语） | 80-120 条 | API 生成 |
| **总计** | **500-800 条** | |

### 数据格式（Alpaca 格式，单轮）

```json
{
  "instruction": "你是「超天酱」，在 Poketter 上发推文。话题：直播时不小心说出了真心话。1-3行，~280字，元气可爱，不提阿P。",
  "input": "",
  "output": "今天直播的时候不小心把心里话说出来了...好害羞>_<✨\n不过宝宝们都说更喜欢真实的我！💖\n那就...偶尔漏一点也没关系吧？毕竟人家也是普通女孩嘛🌟"
}
```

### 数据格式（多轮对话，JINE 聊天）

```json
{
  "messages": [
    {"role": "system", "content": "你是「糖糖」，在JINE上和阿P聊天。活泼的傲娇女友，有身体依赖。"},
    {"role": "user", "content": "[太强了]"},
    {"role": "assistant", "content": "一丁点诚意都感受不到"}
  ]
}
```

### 数据生成策略

1. **高质量种子**：从现有 `data/feed.json` 精选 50-100 条最佳回复
2. **批量扩充**：用 DeepSeek V4 对每个 event 话题生成 8-10 条 variant（改 temperature 0.7-1.0）
3. **人工清洗**：剔除重复、OOC（角色崩塌）、"你在学我说话"等 meta 评论
4. **格式统一**：全部转为 Alpaca 单轮或多轮对话格式

---

## 三、训练配置

### 环境

```bash
# AutoDL 或本地 Linux
pip install transformers peft accelerate bitsandbytes datasets
pip install flash-attn --no-build-isolation  # 加速训练
```

### QLoRA 参数

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model

# 4-bit 量化配置
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype="bfloat16",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)

model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-14B-Instruct",
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True
)

lora_config = LoraConfig(
    r=16,               # rank — 16 足够角色微调
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()  # ~2-3% 参数可训练，约 120-180M
```

### 训练参数

```python
training_args = TrainingArguments(
    output_dir="./amechan-qwen-14b-lora",
    num_train_epochs=3,           # 角色微调 3 轮足够
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4, # 有效 batch=16
    learning_rate=2e-4,
    warmup_ratio=0.1,
    lr_scheduler_type="cosine",
    bf16=True,
    logging_steps=10,
    save_steps=100,
    save_total_limit=2,
)
```

### 训练时间

| batch size | 数据量 | GPU | 时间 |
|------------|--------|-----|------|
| 16 (effective) | 500 条 | RTX 4090 | ~1.5h |
| 16 (effective) | 800 条 | RTX 4090 | ~2.5h |

---

## 四、部署

### 推理部署（vLLM，性能最优）

```bash
# 合并 LoRA 权重到基座模型
python merge_lora.py --base Qwen/Qwen2.5-14B-Instruct --lora ./amechan-qwen-14b-lora --output ./amechan-merged

# AWQ 4-bit 量化（加速推理，减半显存）
python -m awq.entry --model ./amechan-merged --q_bit 4 --q_group_size 128

# 启动 vLLM server
python -m vllm.entrypoints.openai.api_server \
    --model ./amechan-awq-4bit \
    --dtype auto \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.90 \
    --port 8931
```

### 推理速度预期（RTX 4090, 4-bit）

| 任务 | Token 数 | 速度 |
|------|---------|------|
| Poketter 推文（单条） | ~80 tokens | 0.5-1s |
| 三层时间线（单事件） | ~800 tokens | 5-10s |
| JINE 贴图回复 | ~30 tokens | 0.2-0.5s |
| JINE 文字回复 | ~60 tokens | 0.4-0.8s |
| JINE Release 独白（3条） | ~100 tokens | 0.8-1.5s |

**对比 DeepSeek V4 API**：贴图回复从 2-8s → 0.2-0.8s，速度提升 5-10x。

### 备选：Ollama + GGUF（最简单，稍慢）

```bash
# 转换 GGUF
python llama.cpp/convert_hf_to_gguf.py ./amechan-merged --outtype q4_k_m

# Ollama Modelfile
FROM ./amechan-q4_k_m.gguf
SYSTEM "你是超天酱/糖糖，参考 prompts.py 中的完整人设..."

# 启动
ollama serve && ollama create amechan && ollama run amechan
```

vLLM 比 Ollama 快 2-3x，推荐生产环境用 vLLM。

---

## 五、前端改动

几乎不用改。只需换 API endpoint：

```js
// 当前 (DeepSeek API, 通过 Python 后端代理)
fetch('/api/jine/chat', { body: JSON.stringify({text, sticker, history}) })

// 改为直连 vLLM（兼容 OpenAI API 格式）
fetch('http://your-gpu-server:8931/v1/chat/completions', {
    body: JSON.stringify({
        model: 'amechan',
        messages: [...],
        temperature: 0.7
    })
})
```

或者保持 Python 后端做代理（`server.py` 改调本地 vLLM 而非 DeepSeek API），前端零改动。

---

## 六、成本估算

| 项目 | 一次性 | 月常 |
|------|--------|------|
| 训练数据生成（DeepSeek API，~500 次） | ¥50-100 | — |
| GPU 训练（AutoDL 4090, 3h） | ¥12-24 | — |
| GPU 推理（AutoDL 4090, 按量） | — | ¥60-200/月 |
| 推理（家用 RTX 4070 12GB，电费） | ¥0 | ¥50-100/月 |

**首月总投入**：¥150-350（训练+部署）  
**之后月常**：¥60-200（云端）或 ¥50-100（自建）

对比 DeepSeek V4 API：¥100-500/月（取决于调用量）。微调回本周期：2-3 个月。

---

## 七、风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| 训练数据不够 | 角色漂移、重复输出 | 先用 API 批量扩充到 800+ 条 |
| 14B 模型过拟合 | 创造力下降 | 数据增强（同话题 5-10 variant）+ 早停 |
| 推理 OOM | 4090 24GB 装不下 | 用 AWQ 4-bit / GGUF Q4_K_M 压缩到 ~10GB |
| 中文生僻字输出乱码 | 用户体验差 | 训练数据中以中文为主，混入少量日文 emoji |
| 模型学不会 JSON 格式 | 解析失败 | 训练数据中 30% 样本用 JSON 格式输出 |

---

## 八、推荐执行路线

```
第1周：用 DeepSeek V4 API 批量生成 500-800 条训练数据
        ├── 50 个事件话题 × 8 variant = 400 条时间线
        ├── 8 种贴图 × 15 variant = 120 条 JINE 回复
        └── 100 条 JINE Release 独白

第2周：数据清洗 + 格式转换
        ├── 过滤 OOC/重复/meta
        ├── 转 Alpaca/ShareGPT 格式
        └── 划分 train/eval (90/10)

第3周：QLoRA 训练 + 评估
        ├── AutoDL 租 4090 训练 2-4h
        ├── 人工评估 50 条测试输出
        └── 不满意 → 加数据/调参/回第1周

第4周：部署 + 切换
        ├── vLLM 部署到 AutoDL
        ├── server.py 改调本地 vLLM
        └── 灰度：先 JINE 聊天用本地模型，时间线保持 API
```
