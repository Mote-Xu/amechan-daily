"""
推文生成器 v2 — 单事件驱动三层时间线 + hidden_pool
可独立运行：python generator.py [话题]
"""
import json
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from openai import OpenAI

from config import API_KEY, BASE_URL, MODEL, MAX_TOKENS, MAX_RETRIES
from prompts import get_timeline_prompt, get_kangel_user_prompt, get_ame_user_prompt
from prompts import KANGEL_SYSTEM_PROMPT, AME_SYSTEM_PROMPT
from feed import save_timeline, save_hidden_pool

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


def _retry_with_backoff(fn, max_retries: int = MAX_RETRIES):
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"  [!] API 调用失败 (尝试 {attempt + 1}/{max_retries})，{wait}s 后重试: {e}")
                time.sleep(wait)
            else:
                raise


def _call_api(system_prompt: str, user_prompt: str, temperature: float = 0.85) -> str:
    def _call():
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=MAX_TOKENS * 5,  # v2 timeline + hidden_pool needs ~1500 tokens
        )
        return response.choices[0].message.content.strip()

    return _retry_with_backoff(_call)


def _parse_json(raw: str) -> dict:
    """鲁棒 JSON 解析，含截断修复。"""
    # 提取 JSON 块
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start >= 0 and end > start:
        raw = raw[start:end]

    # 尝试直接解析
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 截断修复：统计未闭合的括号并补齐
    depth_brace = raw.count('{') - raw.count('}')
    depth_bracket = raw.count('[') - raw.count(']')

    fixed = raw.rstrip()
    # 如果截断在不完整的键值对中间，回退到最后一个完整逗号
    last_comma = fixed.rfind(',\n  ')
    if last_comma > len(fixed) * 0.6:
        fixed = fixed[:last_comma]

    fixed += ']' * max(0, depth_bracket)
    fixed += '}' * max(0, depth_brace)

    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    raise ValueError(f"JSON 解析失败，原始长度: {len(raw)}, 修复后长度: {len(fixed)}")


def generate_timeline(topic: str | None = None) -> dict:
    """
    v2 核心：单次 API 调用，生成三层时间线 + hidden_pool。
    返回完整的 JSON dict。
    """
    prompt = get_timeline_prompt(topic)
    print(f"[*] 生成三层时间线...")
    print(f"    event: {topic or '随机'}")

    raw = _call_api(KANGEL_SYSTEM_PROMPT, prompt)
    data = _parse_json(raw)

    # 验证必要字段
    if "timeline" not in data:
        raise ValueError(f"API 返回缺少 timeline 字段: {list(data.keys())}")
    if "hidden_pool" not in data:
        data["hidden_pool"] = []
    if "event" not in data:
        data["event"] = topic or "随机"

    return data


def generate_and_save(topic: str | None = None) -> dict:
    """生成时间线并保存到 feed，返回保存结果。"""
    from prompts import _pick_topic
    topic = topic or _pick_topic()

    data = generate_timeline(topic)
    event = data.get("event", topic)

    # 保存时间线
    timeline_count = save_timeline(data["timeline"], event)
    print(f"  [OK] 时间线已保存: {timeline_count} 条")

    # 保存 hidden_pool
    pool = data.get("hidden_pool", [])
    if pool:
        save_hidden_pool(pool)
        print(f"  [OK] hidden_pool 已更新: {len(pool)} 条")

    # 打印预览
    print(f"\n  === 预览 ===")
    for item in data["timeline"]:
        layer_tag = {"poketter": "💖", "diary": "💊", "jine": "💬"}.get(item.get("layer"), "?")
        print(f"  {layer_tag} [{item.get('time', '??:??')}] {item.get('text', '')[:50]}...")

    return data


# ============================================================
# 旧版兼容：单独生成一条推文对
# ============================================================

def generate_single(topic: str | None = None) -> tuple[str, str, str]:
    """旧版兼容：分别生成超天酱推文和糖糖日记。"""
    from prompts import _pick_topic
    topic = topic or _pick_topic()
    print(f"[*] 旧版生成 | 话题: {topic}")

    kangel = _call_api(KANGEL_SYSTEM_PROMPT, get_kangel_user_prompt(topic), 0.9)
    ame = _call_api(AME_SYSTEM_PROMPT, get_ame_user_prompt(topic), 0.7)

    return kangel, ame, topic


# ============================================================
# 独立运行
# ============================================================
if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else None
    generate_and_save(topic)
