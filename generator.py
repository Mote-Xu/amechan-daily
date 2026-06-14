"""
推文生成器 v2.7.1 — 单事件驱动 + hidden_pool + JINE铁律
"""
import json
import random
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from openai import OpenAI

from config import API_KEY, BASE_URL, MODEL, MAX_TOKENS, MAX_RETRIES
from prompts import (get_timeline_prompt, get_kangel_user_prompt, get_ame_user_prompt,
                     get_jine_reply_prompt, get_jine_text_prompt, get_jine_release_prompt)
from prompts import (KANGEL_SYSTEM_PROMPT, AME_SYSTEM_PROMPT, JINE_REPLY_SYSTEM,
                     JINE_TEXT_REPLY_SYSTEM, JINE_RELEASE_SYSTEM, AME_STAMP_POOL)
from feed import save_timeline, save_hidden_pool, get_jine_chat

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


def _call_api(system_prompt: str, user_prompt: str, temperature: float = 0.85,
              frequency_penalty: float = 0.8, presence_penalty: float = 0.6) -> str:
    def _call():
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=MAX_TOKENS * 5,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
        )
        return response.choices[0].message.content.strip()

    return _retry_with_backoff(_call)


def _parse_json(raw: str) -> dict | list:
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    start_brace = raw.find("{")
    start_bracket = raw.find("[")
    if start_bracket >= 0 and (start_brace < 0 or start_bracket < start_brace):
        start = start_bracket
        end = raw.rfind("]") + 1
    else:
        start = start_brace
        end = raw.rfind("}") + 1
    if start >= 0 and end > start:
        raw = raw[start:end]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    depth_brace = raw.count('{') - raw.count('}')
    depth_bracket = raw.count('[') - raw.count(']')
    fixed = raw.rstrip()
    fixed += ']' * max(0, depth_bracket)
    fixed += '}' * max(0, depth_brace)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass
    raise ValueError(f"JSON 解析失败: {len(raw)} chars")


def generate_timeline(topic: str | None = None) -> dict:
    prompt = get_timeline_prompt(topic)
    print(f"[*] 生成三层时间线...")
    raw = _call_api(KANGEL_SYSTEM_PROMPT, prompt)
    data = _parse_json(raw)
    if "timeline" not in data:
        raise ValueError(f"API 返回缺少 timeline: {list(data.keys())}")
    data.setdefault("hidden_pool", [])
    data.setdefault("event", topic or "随机")
    return data


def generate_and_save(topic: str | None = None) -> dict:
    from prompts import _pick_topic
    topic = topic or _pick_topic()
    data = generate_timeline(topic)
    event = data.get("event", topic)
    save_timeline(data["timeline"], event)
    pool = data.get("hidden_pool", [])
    if pool:
        save_hidden_pool(pool)
    for item in data["timeline"]:
        layer_tag = {"poketter": "💖", "diary": "💊", "jine": "💬"}.get(item.get("layer"), "?")
        print(f"  {layer_tag} [{item.get('time', '??:??')}] {item.get('text', '')[:50]}...")
    return data


def generate_single(topic: str | None = None) -> tuple[str, str, str]:
    from prompts import _pick_topic
    topic = topic or _pick_topic()
    kangel = _call_api(KANGEL_SYSTEM_PROMPT, get_kangel_user_prompt(topic), 0.9)
    ame = _call_api(AME_SYSTEM_PROMPT, get_ame_user_prompt(topic), 0.7)
    return kangel, ame, topic


# ============================================================
# F8: JINE 互动回复
# ============================================================
_STICKER_STRESS_DELTA = {
    "sticker_1": 0, "sticker_2": -3, "sticker_3": -5, "sticker_4": +7,
    "sticker_5": -2, "sticker_6": -4, "sticker_7": -8, "sticker_8": +5,
}


def _calc_stress_level(chat_history: list[dict]) -> int:
    stress = 50
    if not chat_history: return stress
    for i, msg in enumerate(reversed(chat_history[-8:])):
        sid = msg.get("sticker", "")
        delta = _STICKER_STRESS_DELTA.get(sid, 0)
        weight = 1.5 - (i * 0.15)
        stress += delta * max(weight, 0.3)
    if len(chat_history) > 10:
        stress += 3
    return max(0, min(100, int(stress)))


def _parse_stamp_reply(raw: str) -> tuple[str, str | None]:
    import re
    stamp_match = re.search(r'\[stamp:\s*([a-zA-Z_]+)\]', raw)
    if stamp_match:
        stamp_id = stamp_match.group(1)
        text = re.sub(r'\[stamp:\s*[a-zA-Z_]+\]', '', raw).strip()
        if stamp_id in set(AME_STAMP_POOL):
            return (text, stamp_id)
    return (raw, None)


def generate_jine_reply(sticker_id: str) -> tuple[str, str | None]:
    chat_history = get_jine_chat(limit=10)
    stress = _calc_stress_level(chat_history)
    recent = []
    for msg in chat_history:
        recent.append(f"玩家: [{msg.get('sticker', '?')}]")
        recent.append(f"糖糖: {msg.get('reply', '')}")
    prompt = get_jine_reply_prompt(sticker_id, recent, stress)
    print(f"[*] JINE 回复 | sticker: {sticker_id} | stress: {stress}")
    try:
        raw = _call_api(JINE_REPLY_SYSTEM, prompt, temperature=0.85)
        raw = raw.strip().strip('"').strip("'").strip('「').strip('」')
        text, ame_sticker = _parse_stamp_reply(raw)
        if text and len(text) > 60: text = text[:60] + "..."
        return (text, ame_sticker)
    except Exception as e:
        print(f"  [X] JINE 回复失败: {e}")
        fallbacks = {"sticker_1": ["嘿嘿！就是这样", "揍你哦！"], "sticker_2": ["一丁点诚意都感受不到"],
                     "sticker_3": ["我才是该哭的那个吧！"], "sticker_4": ["再也不看你的JINE了"],
                     "sticker_5": ["要不……就原谅你吧"], "sticker_6": ["我现在就让你复活"],
                     "sticker_7": ["你心里一定不是这么想的对吧"], "sticker_8": ["我是不会原谅你的"]}
        text = random.choice(fallbacks.get(sticker_id, ["嗯", "哼", "笨蛋"]))
        return (text, None)


def generate_jine_text_reply(player_text: str) -> tuple[str, str | None]:
    chat_history = get_jine_chat(limit=10)
    stress = _calc_stress_level(chat_history)
    recent = []
    for msg in chat_history:
        recent.append(f"玩家: {msg.get('player_text', msg.get('sticker', '?'))}")
        recent.append(f"糖糖: {msg.get('reply', '')}")
    prompt = get_jine_text_prompt(player_text, recent, stress)
    print(f"[*] JINE 文字回复 | stress: {stress}")
    try:
        raw = _call_api(JINE_TEXT_REPLY_SYSTEM, prompt, temperature=0.85)
        raw = raw.strip().strip('"').strip("'").strip('「').strip('」')
        text, ame_sticker = _parse_stamp_reply(raw)
        if text and len(text) > 80: text = text[:80] + "..."
        return (text, ame_sticker)
    except Exception as e:
        print(f"  [X] JINE 文字回复失败: {e}")
        return (random.choice(["嗯", "哼", "笨蛋", "知道了", "哦"]), None)


# ============================================================
# F7 JINE 联动消息 — 单次API JSON数组 (v2.7.1)
# ============================================================
def generate_jine_release_msgs(poke_text: str, diary_text: str = "", count: int = 3) -> list[dict]:
    chat_history = get_jine_chat(limit=10)
    stress = _calc_stress_level(chat_history)
    recent_ame = [msg.get("reply", "") for msg in chat_history if msg.get("reply")]
    prompt = get_jine_release_prompt(poke_text, diary_text, stress, recent_ame)
    print(f"[*] JINE 联动消息 (单次API) | stress: {stress}")
    msgs = []
    try:
        raw = _call_api(JINE_RELEASE_SYSTEM, prompt, temperature=0.7,
                      frequency_penalty=0.95, presence_penalty=0.8)
        data = _parse_json(raw)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, str) and item.strip():
                    text = item.strip().strip('"').strip("'")
                    if len(text) > 60: text = text[:60] + "..."
                    msgs.append({"reply": text, "ame_sticker": None})
        elif isinstance(data, dict):
            text = str(data).strip()
            if text and len(text) < 200:
                msgs.append({"reply": text[:60], "ame_sticker": None})
    except Exception as e:
        print(f"  [X] 联动消息失败: {e}")
        for t in ["喂喂", "又不理我", "笨蛋阿P"][:count]:
            msgs.append({"reply": t, "ame_sticker": None})
    return msgs


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else None
    generate_and_save(topic)
