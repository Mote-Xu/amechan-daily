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
from prompts import get_timeline_prompt, get_kangel_user_prompt, get_ame_user_prompt, get_jine_reply_prompt, get_jine_text_prompt, get_jine_release_prompt
from prompts import KANGEL_SYSTEM_PROMPT, AME_SYSTEM_PROMPT, JINE_REPLY_SYSTEM, JINE_TEXT_REPLY_SYSTEM, JINE_RELEASE_SYSTEM, AME_STAMP_POOL, STICKER_ACTION
from feed import get_jine_chat  # stub: returns [] in stateless mode

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
            max_tokens=MAX_TOKENS * 5,  # v2 timeline + hidden_pool needs ~1500 tokens
            frequency_penalty=frequency_penalty,   # 惩罚高频重复词汇 (0.0-2.0)
            presence_penalty=presence_penalty,      # 鼓励引入新话题 (0.0-2.0)
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
    """v4 stateless: 生成时间线并打印预览（不写盘）。"""
    from prompts import _pick_topic
    topic = topic or _pick_topic()

    data = generate_timeline(topic)
    event = data.get("event", topic)

    # 打印预览
    print(f"\n  === 预览 ({event}) ===")
    for item in data.get("timeline", []):
        layer_tag = {"poketter": "💖", "diary": "💊", "jine": "💬"}.get(item.get("layer"), "?")
        print(f"  {layer_tag} [{item.get('time', '??:??')}] {item.get('text', '')[:50]}...")
    if data.get("hidden_pool"):
        print(f"  [pool] {len(data['hidden_pool'])} 条")

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
# F8: JINE 互动回复生成 (v2.8 — 无状态统一入口)
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


def _calc_stress_from_history(history: list[dict]) -> int:
    """
    基于前端传来的 JINE 聊天记录计算糖糖的情绪压力值 (0-100)。
    v2.8: 接受前端传来的 history 列表，不再读取 feed.json。
    """
    stress = 50
    if not history:
        return stress

    recent_weight = 1.5
    for i, msg in enumerate(reversed(history[-8:])):
        sid = msg.get("sticker", "")
        delta = _STICKER_STRESS_DELTA.get(sid, 0)
        weight = recent_weight - (i * 0.15)
        stress += delta * max(weight, 0.3)

    if len(history) > 10:
        stress += 3

    return max(0, min(100, int(stress)))


# 冷感表达的替换池（避免"手冰"模板化）
_COLD_ALTERNATIVES = [
    "好冷", "冷死了", "被窝里全是冷的", "一个人冷得发抖",
    "脚也好冷", "全身都在发抖", "冷到骨头里了",
    "没有你的被窝好冷", "空调开太大了...冷",
    "冷得睡不着", "越来越冷了",
]


def _sanitize_template_phrases(text: str) -> str:
    """后处理：替换模型顽固输出的模板化短语。"""
    if not text:
        return text
    import re as _re
    # 替换"手冰了/手好冰/手还冰着"等变体
    text = _re.sub(r'手[还也]?[好]?冰[着了呢]?', lambda m: random.choice(_COLD_ALTERNATIVES), text)
    return text


def _parse_stamp_reply(raw: str) -> tuple[str, str | None]:
    """从 AI 回复中解析 [stamp: xxx] 标记。
    返回 (text_reply, stamp_id | None)。
    如果回复只是 [stamp:xxx]（无文字），text_reply 为 ''。
    """
    import re
    stamp_match = re.search(r'\[stamp:\s*([a-zA-Z_]+)\]', raw)
    if stamp_match:
        stamp_id = stamp_match.group(1)
        text = re.sub(r'\[stamp:\s*[a-zA-Z_]+\]', '', raw).strip()
        valid_stamps = set(AME_STAMP_POOL)
        if stamp_id in valid_stamps:
            return (text, stamp_id)
        else:
            print(f"  [!] 未知 stamp_id: {stamp_id}，当作纯文本")
            return (raw, None)
    return (raw, None)


def _format_history_for_prompt(history: list[dict]) -> list[str]:
    """将前端传来的 history 格式化为 prompt 可用的字符串列表。"""
    lines = []
    for msg in history:
        if msg.get("sticker"):
            from prompts import STICKER_MAP
            label = STICKER_MAP.get(msg["sticker"], "贴图")
            lines.append(f"阿P: [{label}]")
        elif msg.get("player_text"):
            lines.append(f"阿P: {msg['player_text']}")
        if msg.get("reply"):
            lines.append(f"糖糖: {msg['reply']}")
    return lines


def generate_jine_chat(text: str = "", sticker: str = "", history: list[dict] | None = None) -> dict:
    """
    v3.3 统一入口：根据玩家消息生成糖糖的 JINE 回复。
    - 纯贴图 → Few-Shot 贴图 prompt，温度 0.85，~50% 概率回贴图
    - 文字/混合 → 文字 prompt，温度 0.85（v3.3 提升防模式崩塌）
    - 回复包含负面情绪词 → 强制附加贴图
    - 后端无状态：不读不写 feed.json，完全依赖前端传来的 history

    返回 {"reply": str, "ame_sticker": str|None}
    """
    if history is None:
        history = []

    is_pure_sticker = bool(sticker) and not text.replace("[...]", "").strip()
    stress = _calc_stress_from_history(history)
    recent = _format_history_for_prompt(history)

    if is_pure_sticker:
        # Pure sticker → Few-Shot prompt. AI decides text/sticker/both (~50% sticker)
        prompt = get_jine_reply_prompt(sticker, recent, stress)
        temperature = 0.85
        print(f"[*] JINE 贴图回复 | sticker: {sticker} | stress: {stress}")
    else:
        # Text or mixed → text prompt. v3.3: raised for richer vocabulary
        effective_text = text if text else f"[{sticker}]"
        prompt = get_jine_text_prompt(effective_text, recent, stress)
        temperature = 0.85  # v3.3: raised from 0.7 to avoid mode collapse
        print(f"[*] JINE 文字回复 | text: {effective_text[:30]}... | stress: {stress} | temp: {temperature}")

    try:
        system = JINE_REPLY_SYSTEM if is_pure_sticker else JINE_TEXT_REPLY_SYSTEM
        raw = _call_api(system, prompt, temperature=temperature)
        raw = raw.strip().strip('"').strip("'").strip('"').strip('「').strip('」')

        reply_text, ame_sticker = _parse_stamp_reply(raw)
        reply_text = _sanitize_template_phrases(reply_text)

        max_len = 60 if is_pure_sticker else 80
        if reply_text and len(reply_text) > max_len:
            reply_text = reply_text[:max_len] + "..."

        if ame_sticker:
            print(f"  [OK] 糖糖回复贴图: {ame_sticker}" + (f" + 文字: {reply_text[:30]}..." if reply_text else ""))
        else:
            print(f"  [OK] 糖糖回复 (stress={stress}): {reply_text[:40]}...")
        return {"reply": reply_text, "ame_sticker": ame_sticker}
    except Exception as e:
        print(f"  [X] JINE 回复生成失败: {e}")
        # 降级回复
        if is_pure_sticker:
            _sticker_fallbacks = {
                "sticker_1": ["嘿嘿！就是这样", "你就这张嘴甜", "你懂就好"],
                "sticker_2": ["你就这张嘴甜", "一丁点诚意都感受不到", "讨厌你的回答！"],
                "sticker_3": ["我才是该哭的那个吧！", "烦！！！！死！！！！啦！！！！！！！！！！！！"],
                "sticker_4": ["再也不看你的JINE了", "看到你这张脸我就来气！", "一脸发自内心的冷漠啊你"],
                "sticker_5": ["好吧，原谅……个屁啦！", "要不……就原谅你吧", "下次再这样，我就拉黑你。"],
                "sticker_6": ["我现在就让你复活 等着我", "确认死亡"],
                "sticker_7": ["你心里一定不是这么想的对吧", "不跟你过了！我有阿宅们宠，我要去找阿宅了再见……算了还是阿P好"],
                "sticker_8": ["我是不会原谅你的 绝对不会", "再不肯好好听我说话咱们就分手 没有啦……我不想分手"],
            }
            _ai_fallbacks = ["嗯", "烦死了", "算了", "...", "哦", "好哦", "知道了", "然后呢"]
            if sticker in _sticker_fallbacks and random.random() < 0.4:
                text = random.choice(_sticker_fallbacks[sticker])
            else:
                text = random.choice(_ai_fallbacks)
        else:
            _game_lines = [
                "嘿嘿！就是这样", "你就这张嘴甜", "一丁点诚意都感受不到",
                "讨厌你的回答！", "看到你这张脸我就来气！", "要不……就原谅你吧",
                "我是不会原谅你的 绝对不会", "你懂就好", "一脸发自内心的冷漠啊你",
                "下次再这样，我就拉黑你。",
            ]
            _ai_lines = ["嗯", "知道了", "然后呢", "烦死了", "哦", "说完了？", "...", "好哦", "算了"]
            if random.random() < 0.35:
                text = random.choice(_game_lines)
            else:
                text = random.choice(_ai_lines)
        ame_sticker = None
        if random.random() < 0.15:
            ame_sticker = random.choice(AME_STAMP_POOL)
        return {"reply": text, "ame_sticker": ame_sticker}


# ============================================================
# Legacy: kept for backward compatibility (F7 release messages)
# ============================================================

def generate_jine_reply(sticker_id: str) -> tuple[str, str | None]:
    """
    [DEPRECATED] 旧版贴图回复。v2.8 请用 generate_jine_chat()。
    保留以支持 F7 release 消息生成（generate_jine_release_msgs 内部调用）。
    """
    chat_history = get_jine_chat(limit=10)
    stress = _calc_stress_from_history(chat_history)
    recent = _format_history_for_prompt(chat_history)
    prompt = get_jine_reply_prompt(sticker_id, recent, stress)
    print(f"[*] JINE 回复生成 | sticker: {sticker_id} | stress: {stress}")

    try:
        raw = _call_api(JINE_REPLY_SYSTEM, prompt, temperature=0.85)
        raw = raw.strip().strip('"').strip("'").strip('"').strip('「').strip('」')
        text, ame_sticker = _parse_stamp_reply(raw)
        if text and len(text) > 60:
            text = text[:60] + "..."
        if ame_sticker:
            print(f"  [OK] 糖糖回复贴图: {ame_sticker}" + (f" + 文字: {text[:30]}..." if text else ""))
        else:
            print(f"  [OK] 糖糖回复 (stress={stress}): {text[:40]}...")
        return (text, ame_sticker)
    except Exception as e:
        print(f"  [X] JINE 回复生成失败: {e}")
        _sticker_fallbacks = {
            "sticker_1": ["嘿嘿！就是这样", "你就这张嘴甜", "你懂就好"],
            "sticker_2": ["你就这张嘴甜", "一丁点诚意都感受不到", "讨厌你的回答！"],
            "sticker_3": ["我才是该哭的那个吧！", "烦！！！！死！！！！啦！！！！！！！！！！！！"],
            "sticker_4": ["再也不看你的JINE了", "看到你这张脸我就来气！", "一脸发自内心的冷漠啊你"],
            "sticker_5": ["好吧，原谅……个屁啦！", "要不……就原谅你吧", "下次再这样，我就拉黑你。"],
            "sticker_6": ["我现在就让你复活 等着我", "确认死亡"],
            "sticker_7": ["你心里一定不是这么想的对吧", "不跟你过了！我有阿宅们宠，我要去找阿宅了再见……算了还是阿P好"],
            "sticker_8": ["我是不会原谅你的 绝对不会", "再不肯好好听我说话咱们就分手 没有啦……我不想分手"],
        }
        _ai_fallbacks = ["嗯", "烦死了", "算了", "...", "哦", "好哦", "知道了", "然后呢"]
        if sticker_id in _sticker_fallbacks and random.random() < 0.4:
            text = random.choice(_sticker_fallbacks[sticker_id])
        else:
            text = random.choice(_ai_fallbacks)
        ame_sticker = None
        if random.random() < 0.15:
            ame_sticker = random.choice(AME_STAMP_POOL)
        return (text, ame_sticker)


def generate_jine_text_reply(player_text: str) -> tuple[str, str | None]:
    """
    [DEPRECATED] 旧版文字回复。v2.8 请用 generate_jine_chat()。
    """
    chat_history = get_jine_chat(limit=10)
    stress = _calc_stress_from_history(chat_history)
    recent = _format_history_for_prompt(chat_history)
    prompt = get_jine_text_prompt(player_text, recent, stress)
    print(f"[*] JINE 文字回复生成 | text: {player_text[:20]}... | stress: {stress}")

    try:
        raw = _call_api(JINE_TEXT_REPLY_SYSTEM, prompt, temperature=0.7)
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
        _game_lines = [
            "嘿嘿！就是这样", "你就这张嘴甜", "一丁点诚意都感受不到",
            "讨厌你的回答！", "看到你这张脸我就来气！", "要不……就原谅你吧",
            "我是不会原谅你的 绝对不会", "你懂就好", "一脸发自内心的冷漠啊你",
            "下次再这样，我就拉黑你。",
        ]
        _ai_lines = ["嗯", "知道了", "然后呢", "烦死了", "哦", "说完了？", "...", "好哦", "算了"]
        if random.random() < 0.35:
            text = random.choice(_game_lines)
        else:
            text = random.choice(_ai_lines)
        ame_sticker = None
        if random.random() < 0.15:
            ame_sticker = random.choice(AME_STAMP_POOL)
        return (text, ame_sticker)


# ============================================================
# F7 JINE 联动消息 — 糖糖主动轰炸
# ============================================================

def generate_jine_release_msgs(poke_text: str, diary_text: str = "", count: int = 3) -> list[dict]:
    """
    生成 F7 释放后糖糖主动轰炸的消息列表。
    v2.7.1: 单次 API 调用返回 JSON 数组，彻底消除同批重复。
    返回 [{"reply": str, "ame_sticker": str|None}, ...]
    """
    chat_history = get_jine_chat(limit=10)
    stress = _calc_stress_from_history(chat_history)

    # Extract recent ame replies for cross-batch anti-repeat
    recent_ame = []
    for msg in chat_history:
        reply = msg.get("reply", "")
        if reply:
            recent_ame.append(reply)

    prompt = get_jine_release_prompt(poke_text, diary_text, stress, recent_ame)
    print(f"[*] JINE 联动消息生成 (单次API) | stress: {stress}")

    msgs = []
    try:
        raw = _call_api(JINE_RELEASE_SYSTEM, prompt, temperature=0.5,
                      frequency_penalty=0.95, presence_penalty=0.8)
        # Parse JSON array
        data = _parse_json(raw)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, str) and item.strip():
                    text = item.strip().strip('"').strip("'").strip('「').strip('」')
                    text = _sanitize_template_phrases(text)
                    if len(text) > 60:
                        text = text[:60] + "..."
                    msgs.append({"reply": text, "ame_sticker": None})
                    print(f"  [{len(msgs)}] {text[:40]}...")
        elif isinstance(data, dict) and "messages" in data:
            for item in data["messages"]:
                if isinstance(item, str) and item.strip():
                    text = item.strip()
                    if len(text) > 60:
                        text = text[:60] + "..."
                    msgs.append({"reply": text, "ame_sticker": None})
        else:
            # Fallback: treat as single message
            text = str(data).strip()
            if text and len(text) < 200:
                msgs.append({"reply": text[:60], "ame_sticker": None})
    except Exception as e:
        print(f"  [X] 联动消息生成失败: {e}")
        # Fallback: use game-original lines
        fallbacks = ["喂喂", "又不理我", "算了", "好累", "那条超可爱的吧"]
        for i in range(min(count, len(fallbacks))):
            msgs.append({"reply": fallbacks[i], "ame_sticker": None})

    return msgs


# ============================================================
# 独立运行
# ============================================================
if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else None
    generate_and_save(topic)
