"""
全局配置模块 — 超天酱日常推文小站
从 .env 文件加载环境变量，定义所有可配置常量。
"""
import os
import sys
from pathlib import Path

# --- 修复 Windows 控制台 UTF-8 编码 ---
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# --- 项目根目录 ---
ROOT_DIR = Path(__file__).resolve().parent

# --- 加载 .env ---
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / ".env")
except ImportError:
    print("[!] python-dotenv 未安装，尝试使用系统环境变量")

# --- API 配置 ---
API_KEY = os.environ.get("DEEPSEEK_API_KEY")
if not API_KEY or API_KEY == "your_api_key_here":
    print("[X] 未设置 DEEPSEEK_API_KEY")
    print("    请在 .env 文件中设置 DEEPSEEK_API_KEY=your_key")
    sys.exit(1)

BASE_URL = "https://api.deepseek.com/v1"
MODEL = "deepseek-v4-pro"
MAX_RETRIES = 3

# --- 推文生成参数 ---
KANGEL_TEMPERATURE = 0.9   # 超天酱：偏高温度让语气更活泼多变
AME_TEMPERATURE = 0.7      # 糖糖：稍低温度保持压抑感的一贯性
MAX_TOKENS = 300           # 单条推文最大 token（~280 字符以内）

# --- 专属话题池（以 ~10% 概率混入）---
PERSONAL_TOPICS = [
    "NANA",
    "星露谷",
    "音乐会",
    "雨天",
    "深夜",
    "咖啡厅",
]

# --- 通用选题池 ---
GENERAL_TOPICS = [
    "直播",
    "天气",
    "粉丝互动",
    "新游戏",
    "零食",
    "自拍",
    "睡不着",
    "今天的心情",
    "穿搭",
    "宅家日常",
    "网购",
    "打游戏",
    "宠物",
    "周末计划",
    "美食",
    "追番",
]

# --- 文件路径 ---
DATA_DIR = ROOT_DIR / "data"
FEED_FILE = DATA_DIR / "feed.json"
STATIC_DIR = ROOT_DIR / "static"

# --- Feed 约束 ---
MAX_FEED_ITEMS = 50

# --- 服务器配置 ---
HOST = "127.0.0.1"
PORT = 8930
