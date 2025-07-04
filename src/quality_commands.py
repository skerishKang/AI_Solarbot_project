from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
import logging
from intelligent_content_analyzer import IntelligentContentAnalyzer
from web_content_fetcher import fetch_content_with_fallback

logger = logging.getLogger(__name__)

def safe_markdown(text: str) -> str:
    """마크다운 특수 문자를 이스케이프 처리"""
    escape_chars = ["_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"]
    for char in escape_chars:
        text = text.replace(char, f"\\{char}")
    return text

def get_quality_grade(score: float) -> str:
    """품질 점수를 등급으로 변환"""
    if score >= 95:
        return "A+"
    elif score >= 90:
        return "A"
    elif score >= 85:
        return "A-"
    elif score >= 80:
        return "B+"
    elif score >= 75:
        return "B"
    elif score >= 70:
        return "B-"
    elif score >= 65:
        return "C+"
    elif score >= 60:
        return "C"
    elif score >= 55:
        return "C-"
    elif score >= 50:
        return "D+"
    elif score >= 45:
        return "D"
    elif score >= 40:
        return "D-"
    else:
        return "F"

def get_grade_emoji(grade: str) -> str:
    """등급에 해당하는 이모지 반환"""
    grade_emojis = {
        "A+": "🌟", "A": "⭐", "A-": "✨",
        "B+": "🔥", "B": "👍", "B-": "👌",
        "C+": "😊", "C": "😐", "C-": "😕",
        "D+": "😟", "D": "😞", "D-": "😢",
        "F": "💥"
    }
    return grade_emojis.get(grade, "📊")
