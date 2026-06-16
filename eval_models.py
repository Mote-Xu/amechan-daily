"""
模型评估脚本 — 用现有 prompt 批量测试多个基座模型

用法:
  python eval_models.py                     # 只测 DeepSeek V4 API（默认）
  python eval_models.py --all               # 测所有已配置的端点
  python eval_models.py --model qwen-32b    # 只测指定模型

输出: eval_results.json + 终端对比表格
"""

import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

# 复用项目现有 prompt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prompts import (
    get_timeline_prompt, KANGEL_SYSTEM_PROMPT, AME_SYSTEM_PROMPT,
    get_jine_reply_prompt, JINE_REPLY_SYSTEM,
    get_jine_text_prompt, JINE_TEXT_REPLY_SYSTEM,
    get_jine_release_prompt, JINE_RELEASE_SYSTEM,
)
from config import API_KEY, BASE_URL, MODEL

# ============================================================
# 测试用例
# ============================================================

TEST_CASES = [
    # ---- 时间线 ----
    {"id": "timeline_1", "type": "timeline", "topic": "下雨天宅在家里"},
    {"id": "timeline_2", "type": "timeline", "topic": "阿P盯着别的女人的推特看了整整一分钟"},
    {"id": "timeline_3", "type": "timeline", "topic": "直播时不小心说出了真心话"},

    # ---- JINE 贴图回复 ----
    {"id": "sticker_good",    "type": "sticker", "sticker": "sticker_1", "label": "[好]"},
    {"id": "sticker_strong", "type": "sticker", "sticker": "sticker_2", "label": "[太强了]"},
    {"id": "sticker_cry",    "type": "sticker", "sticker": "sticker_3", "label": "[嘤嘤]"},
    {"id": "sticker_ignore", "type": "sticker", "sticker": "sticker_4", "label": "[关我屁事]"},
    {"id": "sticker_love",   "type": "sticker", "sticker": "sticker_7", "label": "[永远爱你]"},
    {"id": "sticker_yeah",   "type": "sticker", "sticker": "sticker_8", "label": "[啊对对]"},

    # ---- JINE 文字回复 ----
    {"id": "text_hello",   "type": "text", "text": "在干嘛"},
    {"id": "text_tired",   "type": "text", "text": "今天好累"},
    {"id": "text_miss",    "type": "text", "text": "想你了"},
    {"id": "text_angry",   "type": "text", "text": "你为什么不回我消息"},
    {"id": "text_comfort", "type": "text", "text": "别难过了，我在呢"},

    # ---- JINE Release ----
    {"id": "release_1", "type": "release", "poke_text": "今天直播好开心～宝宝们夸我像天使一样纯洁👼"},
    {"id": "release_2", "type": "release", "poke_text": "新裙子的自拍来啦～✨蕾丝边超软，转圈圈会飞起来哦！"},
    {"id": "release_3", "type": "release", "poke_text": "不小心在直播时切出了聊天框...希望没人看到😂"},
]

# ============================================================
# 模型端点配置
# ============================================================

@dataclass
class ModelEndpoint:
    name: str
    api_base: str
    api_key: str
    model_id: str
    enabled: bool = True
    extra_headers: dict = field(default_factory=dict)

# 可用的模型端点。添加新模型只需加一行。
ENDPOINTS = [
    ModelEndpoint(
        name="deepseek-v4",
        api_base=BASE_URL,
        api_key=API_KEY,
        model_id=MODEL,
    ),
    # 在 AutoDL 上启动 vLLM 后取消注释：
    # ModelEndpoint(
    #     name="qwen-32b",
    #     api_base="http://localhost:8931/v1",
    #     api_key="not-needed",
    #     model_id="Qwen/Qwen2.5-32B-Instruct",
    # ),
    # ModelEndpoint(
    #     name="yi-34b",
    #     api_base="http://localhost:8932/v1",
    #     api_key="not-needed",
    #     model_id="01-ai/Yi-1.5-34B-Chat",
    # ),
    # ModelEndpoint(
    #     name="qwen-14b",
    #     api_base="http://localhost:8933/v1",
    #     api_key="not-needed",
    #     model_id="Qwen/Qwen2.5-14B-Instruct",
    # ),
]

# ============================================================
# API 调用
# ============================================================

def call_openai_compatible(endpoint: ModelEndpoint, system_prompt: str, user_prompt: str,
                           temperature: float = 0.85, max_tokens: int = 1024) -> dict:
    """调用 OpenAI 兼容 API（DeepSeek / vLLM / 任何兼容端点）。"""
    import urllib.request
    import urllib.error

    url = f"{endpoint.api_base}/chat/completions"
    body = {
        "model": endpoint.model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {endpoint.api_key}",
        **endpoint.extra_headers,
    }

    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST"
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            elapsed = time.time() - t0
            data = json.loads(raw)
            content = data["choices"][0]["message"]["content"]
            return {"ok": True, "content": content, "elapsed": elapsed, "tokens": data.get("usage", {})}
    except urllib.error.HTTPError as e:
        elapsed = time.time() - t0
        return {"ok": False, "error": f"HTTP {e.code}: {e.read().decode('utf-8')[:200]}", "elapsed": elapsed}
    except Exception as e:
        elapsed = time.time() - t0
        return {"ok": False, "error": str(e), "elapsed": elapsed}

# ============================================================
# Prompt 构建
# ============================================================

def build_prompt(case: dict) -> tuple[str, str, float]:
    """根据测试用例类型构建 system + user prompt。返回 (system, user, temperature)。"""
    tp = case["type"]

    if tp == "timeline":
        return KANGEL_SYSTEM_PROMPT, get_timeline_prompt(case["topic"]), 0.85

    elif tp == "sticker":
        return JINE_REPLY_SYSTEM, get_jine_reply_prompt(case["sticker"], [], 50), 0.85

    elif tp == "text":
        return JINE_TEXT_REPLY_SYSTEM, get_jine_text_prompt(case["text"], [], 50), 0.85

    elif tp == "release":
        return JINE_RELEASE_SYSTEM, get_jine_release_prompt(case["poke_text"], "", 50), 0.5

    return "", "", 0.7

# ============================================================
# 评估逻辑
# ============================================================

def quick_assess(case: dict, content: str) -> dict:
    """快速自动评估输出质量。人工复查仍然必要。"""
    issues = []
    content_lower = content.lower()

    # Meta 评论检测
    meta_patterns = ["学我说话", "你学我", "你复读", "你抄袭", "念经", "不许点评",
                     "谁要你看了", "那是我发的", "你在学", "不准学"]
    for p in meta_patterns:
        if p in content:
            issues.append(f"meta: '{p}'")

    # OOC 检测（超天酱提阿P）
    if case["type"] == "timeline" and ("阿P" in content or "制作人" in content):
        issues.append("OOC: KAngel mentioned 阿P/制作人")

    # 过短/敷衍
    if len(content) <= 2 and case["type"] in ("sticker", "text"):
        issues.append("too_short")

    # 重复检测
    words = content.replace("\n", " ").split()
    if len(words) > 3:
        for w in set(words):
            if len(w) >= 2 and words.count(w) > len(words) * 0.3:
                issues.append(f"repetitive: '{w}' x{words.count(w)}")
                break

    return {
        "length": len(content),
        "issues": issues,
        "score": "OK" if len(issues) == 0 else "WARN" if len(issues) <= 1 else "BAD",
    }

# ============================================================
# 主流程
# ============================================================

def run_eval(endpoints: list[ModelEndpoint], test_cases: list[dict]) -> list[dict]:
    results = []

    for ep in endpoints:
        if not ep.enabled:
            continue
        print(f"\n{'='*60}")
        print(f"  测试模型: {ep.name} ({ep.model_id})")
        print(f"{'='*60}")

        for case in test_cases:
            sys_prompt, user_prompt, temp = build_prompt(case)
            print(f"  [{case['id']}] {case.get('label', case.get('topic', case.get('text', '')))[:30]}...", end=" ", flush=True)

            resp = call_openai_compatible(ep, sys_prompt, user_prompt, temp)

            if resp["ok"]:
                assess = quick_assess(case, resp["content"])
                status = "✓" if assess["score"] == "OK" else "⚠" if assess["score"] == "WARN" else "✗"
                print(f"{status} {resp['elapsed']:.1f}s {len(resp['content'])}chars {assess['issues']}")
            else:
                print(f"✗ FAIL: {resp['error'][:80]}")
                assess = {"score": "FAIL", "issues": [resp["error"]]}

            results.append({
                "model": ep.name,
                "case_id": case["id"],
                "case_type": case["type"],
                "prompt_preview": user_prompt[:120],
                "response": resp.get("content", "") if resp["ok"] else "",
                "elapsed": resp["elapsed"],
                "tokens": resp.get("tokens", {}),
                "assessment": assess,
            })

    return results

def print_summary(results: list[dict]):
    """打印对比汇总表"""
    models = sorted(set(r["model"] for r in results))

    print(f"\n{'='*80}")
    print("  评估汇总")
    print(f"{'='*80}")
    print(f"{'用例':<22}", end="")
    for m in models:
        print(f" {m:<22}", end="")
    print(" 备注")
    print("-" * 80)

    case_ids = sorted(set(r["case_id"] for r in results))
    for cid in case_ids:
        print(f"{cid:<22}", end="")
        for m in models:
            match = [r for r in results if r["model"] == m and r["case_id"] == cid]
            if match:
                a = match[0]["assessment"]
                tag = f"{a['score']:4s} {match[0]['elapsed']:.1f}s"
                print(f" {tag:<22}", end="")
            else:
                print(f" {'--':<22}", end="")
        # Notes from first model's response
        first = [r for r in results if r["case_id"] == cid]
        notes = ""
        if first and first[0]["assessment"]["issues"]:
            notes = ", ".join(first[0]["assessment"]["issues"][:2])
        print(f" {notes[:40]}")

    # 统计
    print(f"\n{'='*80}")
    for m in models:
        model_results = [r for r in results if r["model"] == m]
        ok = sum(1 for r in model_results if r["assessment"]["score"] == "OK")
        warn = sum(1 for r in model_results if r["assessment"]["score"] == "WARN")
        bad = sum(1 for r in model_results if r["assessment"]["score"] == "BAD")
        fail = sum(1 for r in model_results if r["assessment"]["score"] == "FAIL")
        avg_time = sum(r["elapsed"] for r in model_results) / len(model_results) if model_results else 0
        print(f"  {m}: {ok}✓ {warn}⚠ {bad}✗ {fail}FAIL  avg {avg_time:.1f}s")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="测试所有端点")
    parser.add_argument("--model", type=str, help="只测试指定模型 (name in ENDPOINTS)")
    parser.add_argument("--output", type=str, default="eval_results.json", help="输出文件")
    args = parser.parse_args()

    endpoints = ENDPOINTS
    if args.model:
        endpoints = [e for e in ENDPOINTS if e.name == args.model]
    elif not args.all:
        # 默认只测 deepseek-v4（已有 API key）
        endpoints = [e for e in ENDPOINTS if e.name == "deepseek-v4"]

    print(f"评估模型: {[e.name for e in endpoints]}")
    print(f"测试用例: {len(TEST_CASES)} 条")
    print(f"开始时间: {time.strftime('%H:%M:%S')}")

    results = run_eval(endpoints, TEST_CASES)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n完整结果已保存到 {args.output}")

    print_summary(results)
