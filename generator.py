"""
推文生成器 v2 — 单事件驱动三层时间线 + hidden_pool
可独立运行：python generator.py [话题]
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
from prompts import get_timeline_prompt, get_kangel_user_prompt, get_ame_user_prompt, get_jine_reply_prompt, get_jine_text_prompt
from prompts import KANGEL_SYSTEM_PROMPT, AME_SYSTEM_PROMPT, JINE_REPLY_SYSTEM, JINE_TEXT_REPLY_SYSTEM, AME_STAMP_POOL
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
# F8: JINE 互动回复生成
# ============================================================

# Stress level 变化规则（基于玩家发的 sticker）
_STICKER_STRESS_DELTA = {
    "sticker_1": 0,     # 好 — 中性
    "sticker_2": -3,    # 太强了 — 被认可，减压
    "sticker_3": -5,    # 嘤嘤 — 共享脆弱，减压
    "sticker_4": +7,    # 关我屁事 — 被敷衍，加压
    "sticker_5": -2,    # 抱歉抱歉 — 道歉，微减压
    "sticker_6": -4,    # 原地去世 — 共鸣摆烂，减压
    "sticker_7": -8,    # 永远爱你 — 最想听也最怕听，大减压
    "sticker_8": +5,    # 啊对对 — 敷衍附和，加压
}


def _calc_stress_level(chat_history: list[dict]) -> int:
    """
    基于最近的 JINE 聊天记录计算糖糖的情绪压力值 (0-100)。
    基础值 50，根据最近的 sticker 类型累积调整。
    """
    stress = 50
    if not chat_history:
        return stress

    # 最近的消息权重更高
    recent_weight = 1.5
    for i, msg in enumerate(reversed(chat_history[-8:])):  # 最近 8 条
        sid = msg.get("sticker", "")
        delta = _STICKER_STRESS_DELTA.get(sid, 0)
        # 越近的消息权重越高
        weight = recent_weight - (i * 0.15)
        stress += delta * max(weight, 0.3)

    # 如果长时间没有互动（10+条无回复），缓慢加压
    if len(chat_history) > 10:
        stress += 3

    return max(0, min(100, int(stress)))


def _parse_stamp_reply(raw: str) -> tuple[str, str | None]:
    """从 AI 回复中解析 [stamp: xxx] 标记。
    返回 (text_reply, stamp_id | None)。
    如果回复只是 [stamp:xxx]（无文字），text_reply 为 ''。
    """
    import re
    stamp_match = re.search(r'\[stamp:\s*([a-zA-Z_]+)\]', raw)
    if stamp_match:
        stamp_id = stamp_match.group(1)
        # 移除 stamp 标记，剩余为纯文本
        text = re.sub(r'\[stamp:\s*[a-zA-Z_]+\]', '', raw).strip()
        # 验证 stamp_id 是否在已知池中
        valid_stamps = set(AME_STAMP_POOL)
        if stamp_id in valid_stamps:
            return (text, stamp_id)
        else:
            print(f"  [!] 未知 stamp_id: {stamp_id}，当作纯文本")
            return (raw, None)
    return (raw, None)


def generate_jine_reply(sticker_id: str) -> tuple[str, str | None]:
    """
    根据玩家发送的 sticker，生成糖糖的 JINE 回复。
    返回 (reply_text: str, ame_sticker: str | None)。

    读取最近的 JINE 聊天记录以维持语境连贯 + 计算 stress_level。
    糖糖 ~25% 概率回复贴图，stress 低时更倾向于贴图。
    """
    # 获取最近聊天历史
    chat_history = get_jine_chat(limit=10)
    stress = _calc_stress_level(chat_history)

    recent = []
    for msg in chat_history:
        recent.append(f"玩家: [{msg.get('sticker', '?')}]")
        recent.append(f"糖糖: {msg.get('reply', '')}")

    prompt = get_jine_reply_prompt(sticker_id, recent, stress)
    print(f"[*] JINE 回复生成 | sticker: {sticker_id} | stress: {stress}")

    try:
        raw = _call_api(JINE_REPLY_SYSTEM, prompt, temperature=0.85)
        raw = raw.strip().strip('"').strip("'").strip('"').strip('「').strip('」')

        # 解析 [stamp:] 标记
        text, ame_sticker = _parse_stamp_reply(raw)

        # 限制文字长度
        if text and len(text) > 60:
            text = text[:60] + "..."

        if ame_sticker:
            print(f"  [OK] 糖糖回复贴图: {ame_sticker}" + (f" + 文字: {text[:30]}..." if text else ""))
        else:
            print(f"  [OK] 糖糖回复 (stress={stress}): {text[:40]}...")
        return (text, ame_sticker)
    except Exception as e:
        print(f"  [X] JINE 回复生成失败: {e}")
        # 降级回复（偏 tsundere + 小概率贴图）
        fallback_texts = [
            "...",
            "嗯",
            "知道了",
            "哼",
            "笨蛋",
            "揍你哦!",
            "算了",
            "不说这个了",
            "哦",
            "好哦",
        ]
        text = random.choice(fallback_texts)
        # 低 stress 时 ~20% 概率回退到随机贴图
        ame_sticker = None
        if stress < 40 and random.random() < 0.2:
            ame_sticker = random.choice(AME_STAMP_POOL)
        return (text, ame_sticker)


# ============================================================
# F8b: JINE 文字消息回复
# ============================================================

def generate_jine_text_reply(player_text: str) -> tuple[str, str | None]:
    """
    根据玩家发送的文字消息，生成糖糖的 JINE 回复。
    返回 (reply_text: str, ame_sticker: str | None)。
    """
    chat_history = get_jine_chat(limit=10)
    stress = _calc_stress_level(chat_history)

    recent = []
    for msg in chat_history:
        text_info = msg.get('player_text', msg.get('sticker', '?'))
        recent.append(f"玩家: {text_info}")
        recent.append(f"糖糖: {msg.get('reply', '')}")

    prompt = get_jine_text_prompt(player_text, recent, stress)
    print(f"[*] JINE 文字回复生成 | text: {player_text[:20]}... | stress: {stress}")

    try:
        raw = _call_api(JINE_TEXT_REPLY_SYSTEM, prompt, temperature=0.85)
        raw = raw.strip().strip('"').strip("'").strip('"').strip('「').strip('」')
        text, ame_sticker = _parse_stamp_reply(raw)

        if text and len(text) > 80:
            text = text[:80] + "..."
        if ame_sticker:
            print(f"  [OK] 糖糖回复贴图: {ame_sticker}" + (f" + 文字: {text[:30]}..." if text else ""))
        else:
            print(f"  [OK] 糖糖回复 (stress={stress}): {text[:40]}...")
        return (text, ame_sticker)
    except Exception as e:
        print(f"  [X] JINE 文字回复生成失败: {e}")
        fallbacks = ["嗯", "知道了", "然后呢", "哼", "哦", "说完了？", "揍你哦!", "...", "好哦"]
        text = random.choice(fallbacks)
        ame_sticker = None
        if random.random() < 0.15:
            ame_sticker = random.choice(AME_STAMP_POOL)
        return (text, ame_sticker)


# ============================================================
# 独立运行
# ============================================================
if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else None
    generate_and_save(topic)
