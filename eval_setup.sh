#!/bin/bash
# AutoDL 模型评估环境一键搭建
# 用法: bash eval_setup.sh
# 在 AutoDL 实例（Ubuntu 22.04, CUDA 12.x）上运行

set -e
echo "=== 超天酱模型评估环境搭建 ==="

# ---------- 1. 基础依赖 ----------
pip install vllm openai transformers -q

# ---------- 2. 下载模型 ----------
# 用 modelscope 镜像（AutoDL 国内网络快）
pip install modelscope -q

MODEL_DIR=~/models
mkdir -p $MODEL_DIR

echo ""
echo "下载 Qwen2.5-32B-Instruct..."
python -c "
from modelscope import snapshot_download
snapshot_download('Qwen/Qwen2.5-32B-Instruct', cache_dir='$MODEL_DIR')
" 2>&1 | tail -3

echo ""
echo "下载 Yi-1.5-34B-Chat..."
python -c "
from modelscope import snapshot_download
snapshot_download('01ai/Yi-1.5-34B-Chat', cache_dir='$MODEL_DIR')
" 2>&1 | tail -3

# ---------- 3. 启动 vLLM 实例 ----------
echo ""
echo "=== 启动 Qwen 32B (端口 8931) ==="
python -m vllm.entrypoints.openai.api_server \
    --model $MODEL_DIR/Qwen/Qwen2.5-32B-Instruct \
    --dtype auto \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.85 \
    --port 8931 \
    --trust-remote-code &
QWEN_PID=$!
echo "Qwen PID: $QWEN_PID"

# 等 Qwen 就绪
echo "等待 Qwen 就绪..."
for i in $(seq 1 60); do
    if curl -s http://localhost:8931/health > /dev/null 2>&1; then
        echo "Qwen 就绪 ✓"
        break
    fi
    sleep 2
done

echo ""
echo "=== 启动 Yi 34B (端口 8932) ==="
python -m vllm.entrypoints.openai.api_server \
    --model $MODEL_DIR/01ai/Yi-1.5-34B-Chat \
    --dtype auto \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.85 \
    --port 8932 \
    --trust-remote-code &
YI_PID=$!
echo "Yi PID: $YI_PID"

echo "等待 Yi 就绪..."
for i in $(seq 1 60); do
    if curl -s http://localhost:8932/health > /dev/null 2>&1; then
        echo "Yi 就绪 ✓"
        break
    fi
    sleep 2
done

# ---------- 4. 配置评估脚本 ----------
echo ""
echo "=== 配置 eval_models.py 端点 ==="
cat > ~/eval_endpoints.py << 'PYEOF'
# 评估端点配置（由 eval_setup.sh 自动生成）

ENDPOINTS = [
    {
        "name": "qwen-32b",
        "api_base": "http://localhost:8931/v1",
        "api_key": "not-needed",
        "model_id": "Qwen/Qwen2.5-32B-Instruct",
    },
    {
        "name": "yi-34b",
        "api_base": "http://localhost:8932/v1",
        "api_key": "not-needed",
        "model_id": "01-ai/Yi-1.5-34B-Chat",
    },
]
PYEOF

echo ""
echo "=== 环境就绪 ==="
echo ""
echo "运行评估:"
echo "  python eval_models.py --all"
echo ""
echo "单独测试某个模型:"
echo "  curl http://localhost:8931/v1/chat/completions -H 'Content-Type: application/json' -d '{\"model\":\"Qwen/Qwen2.5-32B-Instruct\",\"messages\":[{\"role\":\"user\",\"content\":\"你好\"}]}'"
echo ""
echo "停止服务:"
echo "  kill $QWEN_PID $YI_PID"
