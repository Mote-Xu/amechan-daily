"""
推文生成器 — 调用 DeepSeek API 生成双人格推文
可独立运行：python generator.py [主题]
"""
import json
import sys
import time

# 修复 Windows 控制台 UTF-8 编码
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from openai import OpenAI

from config import API_KEY, BASE_URL, MODEL, MAX_TOKENS, MAX_RETRIES
from config import KANGEL_TEMPERATURE, AME_TEMPERATURE
from prompts import (
    KANGEL_SYSTEM_PROMPT,
    AME_SYSTEM_PROMPT,
    get_kangel_user_prompt,
    get_ame_user_prompt,
    get_combined_user_prompt,
)
from feed import save_tweet_pair

# --- OpenAI 客户端（DeepSeek 兼容接口）---
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


def _retry_with_backoff(fn, max_retries: int = MAX_RETRIES):
    """指数退避重试。"""
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


def _call_api(system_prompt: str, user_prompt: str, temperature: float) -> str:
    """单次 API 调用，返回文本内容。"""
    def _call():
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content.strip()

    return _retry_with_backoff(_call)


def generate_separately(topic: str | None = None) -> tuple[str, str, str]:
    """
    分别调用两次 API，各产生一条推文（更高随机性）。
    返回 (kangel_text, ame_text, topic)
    """
    topic = topic or "随机"
    print(f"[*] 生成推文对 | 话题: {topic}")

    print("  -> 生成超天酱推文...")
    kangel = _call_api(KANGEL_SYSTEM_PROMPT, get_kangel_user_prompt(topic), KANGEL_TEMPERATURE)

    print("  -> 生成糖糖日记...")
    ame = _call_api(AME_SYSTEM_PROMPT, get_ame_user_prompt(topic), AME_TEMPERATURE)

    return kangel, ame, topic


def generate_combined(topic: str | None = None) -> tuple[str, str, str]:
    """
    一次 API 调用同时生成两条（保证主题一致，表里呼应）。
    返回 (kangel_text, ame_text, topic)
    """
    from prompts import _pick_topic
    topic = topic or _pick_topic()
    print(f"[*] 生成推文对 | 话题: {topic}")

    print("  -> 调用 DeepSeek API...")
    raw = _call_api(KANGEL_SYSTEM_PROMPT, get_combined_user_prompt(topic), 0.85)

    # 解析 JSON 响应
    try:
        # 尝试直接解析
        data = json.loads(raw)
    except json.JSONDecodeError:
        # 尝试提取 JSON 块
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        # 尝试找花括号
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            raw = raw[start:end]
        data = json.loads(raw)

    kangel = data.get("kangel", "").strip()
    ame = data.get("ame", "").strip()

    if not kangel or not ame:
        raise ValueError(f"API 返回内容不完整: kangel={kangel!r}, ame={ame!r}")

    return kangel, ame, topic


def generate_and_save(topic: str | None = None) -> dict:
    """生成一对推文并保存到 feed，返回保存的条目。"""
    kangel, ame, topic = generate_combined(topic)
    entry = save_tweet_pair(kangel, ame, topic)
    print(f"  [OK] 推文已保存: {entry['id']}")
    print(f"       KAngel: {kangel[:60]}...")
    print(f"       Ame:    {ame[:60]}...")
    return entry


# ============================================================
# 独立运行
# ============================================================
if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else None
    generate_and_save(topic)
