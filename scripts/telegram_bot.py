#!/usr/bin/env python3
"""
텔레그램 봇 - 퀴즈 영상 즉시 생성 v2

기능:
- 인라인 키보드 버튼으로 퀴즈 유형 선택
- 예제 이미지 미리보기
- 결과물 분리 전송 (영상, 제목, 해설 각각 복사 가능)
"""

import sys
import os
import asyncio
import logging
import random
from pathlib import Path
from typing import Optional
from datetime import datetime

# Windows 콘솔 인코딩 문제 해결
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 스크립트 디렉토리
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
RESOURCES_DIR = BASE_DIR / "resources"
EXAMPLES_DIR = RESOURCES_DIR / "examples"
sys.path.insert(0, str(SCRIPT_DIR))

from dotenv import load_dotenv
load_dotenv(SCRIPT_DIR.parent / ".env")

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# 스케줄러 import
from upload_scheduler import get_scheduler, UploadMode, extract_comment_text

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 퀴즈 유형 정의
QUIZ_TYPES = {
    "치매": {
        "name": "치매 예방 테스트",
        "emoji": "🧠",
        "description": "그림 속 숨겨진 얼굴 찾기",
        "example_title": "認知症が始まった人は\n違って見える絵",
        "keywords": ["치매", "인지", "dementia", "認知症", "얼굴"],
    },
    "IQ": {
        "name": "IQ 테스트", 
        "emoji": "🎯",
        "description": "숫자가 몇 개 보이는지 테스트",
        "example_title": "IQが130以上なら\nすべての数字が見える",
        "keywords": ["iq", "아이큐", "IQ", "지능지수"],
    },
    "관찰력": {
        "name": "관찰력 테스트",
        "emoji": "👁",
        "description": "그림 속 숨겨진 숫자 찾기",
        "example_title": "観察力が優れていれば\n数字が9個すべて見える",
        "keywords": ["관찰력", "관찰", "observation", "観察"],
    },
    "노안": {
        "name": "노안 테스트",
        "emoji": "👓",
        "description": "착시 이미지에서 숫자 찾기",
        "example_title": "老眼が始まっている人は\n数字が3つ以下に見えます",
        "keywords": ["노안", "시력", "presbyopia", "老眼", "눈"],
    },
    "성격": {
        "name": "성격 테스트",
        "emoji": "🦆",
        "description": "동물 개수로 성격 파악",
        "example_title": "繊細な性格の持ち主は\n違って見える絵",
        "keywords": ["성격", "personality", "性格", "동물"],
    },
    "우울": {
        "name": "우울증 테스트",
        "emoji": "🐸",
        "description": "이중 이미지에서 무엇이 보이는지",
        "example_title": "現在、うつ状態の人には\n馬が見える絵",
        "keywords": ["우울", "우울증", "depression", "うつ", "심리"],
    },
    "지능": {
        "name": "지능 테스트",
        "emoji": "✨",
        "description": "고지능자만 보이는 숫자",
        "example_title": "知能が高い人だけに\n見える絵",
        "keywords": ["지능", "intelligence", "知能", "천재"],
    },
    "겸손": {
        "name": "겸손함 테스트",
        "emoji": "🏔",
        "description": "무엇이 먼저 보이는지로 성격 파악",
        "example_title": "謙虚な人は\n違って見える絵",
        "keywords": ["겸손", "humility", "謙虚", "성품"],
    },
}


def get_main_keyboard() -> InlineKeyboardMarkup:
    """메인 키보드 생성"""
    keyboard = [
        [
            InlineKeyboardButton(f"🧠 치매", callback_data="quiz_치매"),
            InlineKeyboardButton(f"🎯 IQ", callback_data="quiz_IQ"),
            InlineKeyboardButton(f"👁 관찰력", callback_data="quiz_관찰력"),
            InlineKeyboardButton(f"👓 노안", callback_data="quiz_노안"),
        ],
        [
            InlineKeyboardButton(f"🦆 성격", callback_data="quiz_성격"),
            InlineKeyboardButton(f"🐸 우울", callback_data="quiz_우울"),
            InlineKeyboardButton(f"✨ 지능", callback_data="quiz_지능"),
            InlineKeyboardButton(f"🏔 겸손", callback_data="quiz_겸손"),
        ],
        [
            InlineKeyboardButton("🎲 랜덤 생성", callback_data="quiz_랜덤"),
        ],
        [
            InlineKeyboardButton("⚙️ 설정 및 관리", callback_data="show_settings"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """설정 메뉴 키보드 (재구조화)"""
    keyboard = [
        [
            InlineKeyboardButton("📊 상태 보기", callback_data="view_status"),
        ],
        [
            InlineKeyboardButton("🎬 자동 생성 설정", callback_data="auto_gen_settings"),
        ],
        [
            InlineKeyboardButton("🔄 모드 및 스케줄러", callback_data="scheduler_settings"),
        ],
        [
            InlineKeyboardButton("📋 큐 관리", callback_data="queue_management"),
        ],
        [
            InlineKeyboardButton("📈 통계", callback_data="view_statistics"),
        ],
        [
            InlineKeyboardButton("◀️ 메인 메뉴로", callback_data="back_to_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_quiz_detail_keyboard(quiz_type: str) -> InlineKeyboardMarkup:
    """퀴즈 상세 페이지 키보드"""
    keyboard = [
        [
            InlineKeyboardButton("🎬 이 유형으로 생성하기", callback_data=f"generate_{quiz_type}"),
        ],
        [
            InlineKeyboardButton("◀️ 목록으로 돌아가기", callback_data="back_to_list"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_auto_gen_settings_keyboard() -> InlineKeyboardMarkup:
    """자동 생성 설정 키보드"""
    auto_generate = bot.scheduler.config.get("auto_generate", False)
    auto_gen_text = "🟢 켜짐" if auto_generate else "🔴 꺼짐"
    auto_gen_action = "off" if auto_generate else "on"

    keyboard = [
        [
            InlineKeyboardButton(f"자동 생성: {auto_gen_text}", callback_data=f"toggle_auto_gen_{auto_gen_action}"),
        ],
        [
            InlineKeyboardButton("🎯 주제 선택", callback_data="select_topics"),
        ],
        [
            InlineKeyboardButton("◀️ 설정 메뉴로", callback_data="show_settings"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_topics_selection_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    """주제 선택 키보드 (페이지네이션)"""
    current_topics = bot.scheduler.config.get("topics", [])
    all_quiz_types = list(QUIZ_TYPES.keys())

    # 페이지네이션 (한 페이지당 4개)
    items_per_page = 4
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_items = all_quiz_types[start_idx:end_idx]

    keyboard = []

    # 주제 버튼들
    for quiz_type in page_items:
        is_selected = quiz_type in current_topics
        icon = "✅" if is_selected else "⬜"
        emoji = QUIZ_TYPES[quiz_type]['emoji']
        keyboard.append([
            InlineKeyboardButton(
                f"{icon} {emoji} {quiz_type}",
                callback_data=f"toggle_topic_{quiz_type}"
            )
        ])

    # 페이지 네비게이션
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ 이전", callback_data=f"topics_page_{page-1}"))
    if end_idx < len(all_quiz_types):
        nav_buttons.append(InlineKeyboardButton("다음 ▶️", callback_data=f"topics_page_{page+1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([
        InlineKeyboardButton("◀️ 자동 생성 설정으로", callback_data="auto_gen_settings")
    ])

    return InlineKeyboardMarkup(keyboard)


def get_scheduler_settings_keyboard() -> InlineKeyboardMarkup:
    """모드 및 스케줄러 설정 키보드"""
    mode = bot.scheduler.get_mode()
    paused = bot.scheduler.is_paused()

    pause_icon = "▶️ 재개" if paused else "⏸️ 일시정지"
    pause_data = "btn_resume" if paused else "btn_pause"

    keyboard = [
        [
            InlineKeyboardButton("🔄 모드 변경", callback_data="btn_mode"),
        ],
        [
            InlineKeyboardButton("⏱️ 업로드 간격 변경", callback_data="btn_change_interval"),
        ],
        [
            InlineKeyboardButton("🚀 즉시 업로드", callback_data="btn_upload_now"),
            InlineKeyboardButton(f"{pause_icon}", callback_data=pause_data),
        ],
        [
            InlineKeyboardButton("◀️ 설정 메뉴로", callback_data="show_settings"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_interval_selection_keyboard() -> InlineKeyboardMarkup:
    """업로드 간격 선택 키보드"""
    current_interval = bot.scheduler.config.get('interval_hours', 5)

    intervals = [
        (1, "1시간"),
        (2, "2시간"),
        (3, "3시간"),
        (5, "5시간"),
        (12, "12시간"),
        (24, "24시간"),
    ]

    keyboard = []

    # 간격 버튼들 (2개씩 배치)
    for i in range(0, len(intervals), 2):
        row = []
        for j in range(2):
            if i + j < len(intervals):
                hours, label = intervals[i + j]
                icon = "✅" if hours == current_interval else "⚪"
                row.append(InlineKeyboardButton(
                    f"{icon} {label}",
                    callback_data=f"set_interval_{hours}"
                ))
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton("◀️ 스케줄러 설정으로", callback_data="scheduler_settings")
    ])

    return InlineKeyboardMarkup(keyboard)


def get_queue_management_keyboard() -> InlineKeyboardMarkup:
    """큐 관리 키보드"""
    keyboard = [
        [
            InlineKeyboardButton("📋 전체 큐 보기", callback_data="btn_queue_page_0"),
        ],
        [
            InlineKeyboardButton("⚠️ 실패한 영상 보기", callback_data="view_failed_videos"),
        ],
        [
            InlineKeyboardButton("🗑️ 큐 비우기", callback_data="btn_clear_queue"),
        ],
        [
            InlineKeyboardButton("◀️ 설정 메뉴로", callback_data="show_settings"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_queue_page_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    """큐 페이지 키보드 (페이지네이션 + 개별 삭제)"""
    keyboard = []

    # 개별 항목 삭제 버튼 (현재 페이지의 항목들만)
    items_per_page = 5
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(bot.scheduler.queue))

    for i in range(start_idx, end_idx):
        item = bot.scheduler.queue[i]
        title = item.get('title', 'N/A').replace('\n', ' ')[:20]
        status = "✅" if item.get('approved_at') else "⏳"
        keyboard.append([
            InlineKeyboardButton(
                f"{i+1}. {status} {title}...",
                callback_data=f"view_queue_item_{i}"
            )
        ])

    # 페이지 네비게이션
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ 이전", callback_data=f"btn_queue_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("다음 ▶️", callback_data=f"btn_queue_page_{page+1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([
        InlineKeyboardButton("◀️ 큐 관리로", callback_data="queue_management")
    ])

    return InlineKeyboardMarkup(keyboard)


def get_help_message() -> str:
    """도움말 메시지 생성"""
    lines = [
        "🎬 **퀴즈 영상 생성 봇**",
        "",
        "아래 버튼을 눌러 원하는 퀴즈 유형을 선택하세요!",
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        ""
    ]
    
    for key, info in QUIZ_TYPES.items():
        lines.append(f"{info['emoji']} **{key}** - {info['name']}")
    
    lines.extend([
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
        "💡 버튼을 클릭하면 예시를 확인할 수 있습니다",
        "⏱️ 영상 생성에는 1~2분 정도 소요됩니다",
    ])
    
    return "\n".join(lines)


def get_quiz_detail_message(quiz_type: str) -> str:
    """퀴즈 상세 메시지"""
    info = QUIZ_TYPES[quiz_type]

    lines = [
        f"{info['emoji']} **{info['name']}**",
        "",
        f"📝 {info['description']}",
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
        "📌 **예시 제목:**",
        f"```",
        f"{info['example_title']}",
        f"```",
        "",
        "⬇️ 아래 버튼을 눌러 영상을 생성하세요!",
    ]

    return "\n".join(lines)


def get_settings_message() -> str:
    """설정 메뉴 메시지 (재구조화)"""
    lines = [
        "⚙️ **설정 및 관리**",
        "",
        "아래 메뉴에서 원하는 항목을 선택하세요:",
        "",
        "📊 **상태 보기** - 큐 및 스케줄러 현황",
        "🎬 **자동 생성 설정** - 자동 영상 생성 설정",
        "🔄 **모드 및 스케줄러** - 업로드 모드 및 스케줄러 제어",
        "📋 **큐 관리** - 업로드 큐 관리",
        "📈 **통계** - 업로드 통계 및 이력",
    ]
    return "\n".join(lines)


def get_status_message() -> str:
    """상태 보기 메시지"""
    mode = bot.scheduler.get_mode()
    paused = bot.scheduler.is_paused()
    queue_status = bot.scheduler.get_queue_status()
    next_upload = bot.scheduler.get_next_upload_time()
    interval = bot.scheduler.config.get('interval_hours', 5)
    auto_generate = bot.scheduler.config.get('auto_generate', False)

    mode_text = "🔄 자동 모드" if mode == UploadMode.AUTO else "🔍 검수 모드"
    status_text = "⏸️ 일시정지" if paused else "▶️ 실행 중"
    auto_gen_text = "🟢 켜짐" if auto_generate else "🔴 꺼짐"

    lines = [
        "📊 **현재 상태**",
        "",
        f"**스케줄러**",
        f"  • 상태: {status_text}",
        f"  • 모드: {mode_text}",
        f"  • 업로드 간격: {interval}시간",
        f"  • 다음 업로드: {next_upload.strftime('%Y-%m-%d %H:%M') if next_upload else 'N/A'}",
        "",
        f"**자동 생성**",
        f"  • 자동 생성: {auto_gen_text}",
        "",
        f"**큐 현황**",
        f"  • 전체: {queue_status['total']}개",
        f"  • 승인됨: {queue_status['approved']}개",
        f"  • 대기 중: {queue_status['pending']}개",
        f"  • 실패: {queue_status['failed']}개",
    ]
    return "\n".join(lines)


def get_auto_gen_settings_message() -> str:
    """자동 생성 설정 메시지"""
    auto_generate = bot.scheduler.config.get("auto_generate", False)
    topics = bot.scheduler.config.get("topics", [])

    auto_gen_text = "🟢 켜짐" if auto_generate else "🔴 꺼짐"

    lines = [
        "🎬 **자동 생성 설정**",
        "",
        f"현재 상태: {auto_gen_text}",
        "",
        "**자동 생성이란?**",
        "큐가 비어있을 때 자동으로 영상을 생성하여",
        "업로드 큐에 추가하는 기능입니다.",
        "",
        f"**선택된 주제 ({len(topics)}개):**",
    ]

    if topics:
        for topic in topics:
            emoji = QUIZ_TYPES.get(topic, {}).get("emoji", "📌")
            lines.append(f"  • {emoji} {topic}")
    else:
        lines.append("  (선택된 주제 없음)")

    return "\n".join(lines)


def get_statistics_message() -> str:
    """통계 메시지"""
    queue_status = bot.scheduler.get_queue_status()
    last_upload = bot.scheduler.config.get("last_upload")

    # 큐 기록에서 통계 계산
    total_items = len(bot.scheduler.queue)
    approved_items = queue_status['approved']
    failed_items = queue_status['failed']

    lines = [
        "📈 **업로드 통계**",
        "",
        f"**전체 통계**",
        f"  • 현재 큐: {total_items}개",
        f"  • 승인됨: {approved_items}개",
        f"  • 실패: {failed_items}개",
        "",
        f"**최근 활동**",
        f"  • 마지막 업로드: {datetime.fromisoformat(last_upload).strftime('%Y-%m-%d %H:%M') if last_upload else 'N/A'}",
    ]

    return "\n".join(lines)


def resolve_quiz_type(text: str) -> Optional[str]:
    """입력 텍스트를 퀴즈 유형으로 변환"""
    text_lower = text.lower().strip()
    
    # 직접 매칭
    for key in QUIZ_TYPES.keys():
        if key.lower() == text_lower:
            return key
    
    # 키워드 매칭
    for key, info in QUIZ_TYPES.items():
        for keyword in info["keywords"]:
            if keyword.lower() == text_lower or keyword.lower() in text_lower:
                return key
    
    return None


class QuizBot:
    def __init__(self):
        self.generating = False
        self.scheduler = get_scheduler()
        self.bot_instance = None  # Application 인스턴스 (나중에 설정)
        
    async def send_upload_notification(self, title: str, video_url: str, remaining: int):
        """
        업로드 완료 알림 전송 (모든 사용자에게)

        Args:
            title: 영상 제목
            video_url: YouTube URL
            remaining: 남은 큐 크기
        """
        if not self.bot_instance:
            logger.warning("봇 인스턴스가 없어 알림을 전송할 수 없습니다")
            return

        message = (
            f"📺 **YouTube 업로드 완료!**\n\n"
            f"제목: {title}\n"
            f"링크: {video_url}\n\n"
            f"남은 큐: {remaining}개"
        )

        # 관리자 채팅 ID 목록 가져오기
        admin_chat_ids = self.scheduler.config.get("admin_chat_ids", [])

        if not admin_chat_ids:
            logger.warning("관리자 채팅 ID가 설정되지 않아 알림을 전송할 수 없습니다. /start 명령어를 사용하여 봇과 대화를 시작하세요.")
            return

        # 모든 관리자에게 알림 전송
        for chat_id in admin_chat_ids:
            try:
                await self.bot_instance.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
                logger.info(f"업로드 알림 전송 완료: {chat_id}")
            except Exception as e:
                logger.error(f"알림 전송 실패 (chat_id: {chat_id}): {e}")

    def generate_quiz_video_sync(self, quiz_type: str) -> tuple[str, str, str]:
        """
        퀴즈 영상 생성 (동기)

        Returns:
            (video_path, title, description) 튜플
        """
        from quiz_pipeline import generate_quiz_video
        from quiz_json_generator import generate_quiz_json

        logger.info(f"🎬 {quiz_type} 퀴즈 영상 생성 시작...")

        # JSON 생성
        quiz_json = generate_quiz_json(quiz_type)

        # 타이틀 및 설명 추출
        ui = quiz_json.get("ui_elements", {})
        title = ui.get("top_title", "퀴즈テスト")
        if isinstance(title, dict):
            title = str(title)
        title = title.replace("\\n", "\n")

        description = quiz_json.get("detailed_analysis_comment", "")
        # 딕셔너리인 경우 JSON 문자열로 변환
        if isinstance(description, dict):
            import json
            description = json.dumps(description, ensure_ascii=False, indent=2)
        elif not isinstance(description, str):
            description = str(description)

        # 영상 생성
        video_path = generate_quiz_video(quiz_json)

        if video_path:
            logger.info(f"✅ 영상 생성 완료: {video_path}")
            return video_path, title, description
        else:
            raise Exception("영상 생성 실패")


# 봇 인스턴스
bot = QuizBot()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """시작 명령어"""
    # 현재 채팅 ID를 관리자 목록에 추가
    chat_id = update.effective_chat.id
    admin_chat_ids = bot.scheduler.config.get("admin_chat_ids", [])

    if chat_id not in admin_chat_ids:
        admin_chat_ids.append(chat_id)
        bot.scheduler.config["admin_chat_ids"] = admin_chat_ids
        bot.scheduler._save_config(bot.scheduler.config)
        logger.info(f"관리자 채팅 ID 추가: {chat_id}")

    await update.message.reply_text(
        get_help_message(),
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """도움말 명령어"""
    await update.message.reply_text(
        get_help_message(),
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )


async def quiz_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """퀴즈 유형 선택 콜백"""
    query = update.callback_query
    await query.answer()

    data = query.data

    # 메인 메뉴로
    if data == "back_to_main":
        await query.edit_message_text(
            get_help_message(),
            reply_markup=get_main_keyboard(),
            parse_mode='Markdown'
        )
        return

    # 목록으로 돌아가기
    if data == "back_to_list":
        await query.edit_message_text(
            get_help_message(),
            reply_markup=get_main_keyboard(),
            parse_mode='Markdown'
        )
        return

    # 설정 메뉴 표시
    if data == "show_settings":
        await query.edit_message_text(
            get_settings_message(),
            reply_markup=get_settings_keyboard(),
            parse_mode='Markdown'
        )
        return

    # 상태 보기
    if data == "view_status":
        keyboard = [[InlineKeyboardButton("◀️ 설정 메뉴로", callback_data="show_settings")]]
        await query.edit_message_text(
            get_status_message(),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return

    # 자동 생성 설정 메뉴
    if data == "auto_gen_settings":
        await query.edit_message_text(
            get_auto_gen_settings_message(),
            reply_markup=get_auto_gen_settings_keyboard(),
            parse_mode='Markdown'
        )
        return

    # 자동 생성 토글
    if data.startswith("toggle_auto_gen_"):
        action = data.replace("toggle_auto_gen_", "")
        new_value = (action == "on")
        bot.scheduler.config["auto_generate"] = new_value
        bot.scheduler._save_config(bot.scheduler.config)

        status_text = "켜졌습니다" if new_value else "꺼졌습니다"
        await query.edit_message_text(f"✅ 자동 생성이 {status_text}!")
        await asyncio.sleep(1)
        await query.edit_message_text(
            get_auto_gen_settings_message(),
            reply_markup=get_auto_gen_settings_keyboard(),
            parse_mode='Markdown'
        )
        return

    # 주제 선택 메뉴
    if data == "select_topics":
        await query.edit_message_text(
            "🎯 **주제 선택**\n\n버튼을 눌러 주제를 선택/해제하세요:",
            reply_markup=get_topics_selection_keyboard(0),
            parse_mode='Markdown'
        )
        return

    # 주제 페이지 이동
    if data.startswith("topics_page_"):
        page = int(data.replace("topics_page_", ""))
        await query.edit_message_text(
            "🎯 **주제 선택**\n\n버튼을 눌러 주제를 선택/해제하세요:",
            reply_markup=get_topics_selection_keyboard(page),
            parse_mode='Markdown'
        )
        return

    # 주제 토글
    if data.startswith("toggle_topic_"):
        topic = data.replace("toggle_topic_", "")
        current_topics = bot.scheduler.config.get("topics", [])

        if topic in current_topics:
            current_topics.remove(topic)
        else:
            current_topics.append(topic)

        bot.scheduler.config["topics"] = current_topics
        bot.scheduler._save_config(bot.scheduler.config)

        # 현재 페이지 유지 (메시지만 업데이트)
        await query.answer(f"{'✅ 선택됨' if topic in current_topics else '⬜ 해제됨'}: {topic}")
        await query.edit_message_reply_markup(
            reply_markup=get_topics_selection_keyboard(0)
        )
        return

    # 스케줄러 설정 메뉴
    if data == "scheduler_settings":
        await query.edit_message_text(
            get_status_message(),
            reply_markup=get_scheduler_settings_keyboard(),
            parse_mode='Markdown'
        )
        return

    # 큐 관리 메뉴
    if data == "queue_management":
        await query.edit_message_text(
            "📋 **큐 관리**\n\n아래 메뉴에서 원하는 작업을 선택하세요:",
            reply_markup=get_queue_management_keyboard(),
            parse_mode='Markdown'
        )
        return

    # 통계 보기
    if data == "view_statistics":
        keyboard = [[InlineKeyboardButton("◀️ 설정 메뉴로", callback_data="show_settings")]]
        await query.edit_message_text(
            get_statistics_message(),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return

    # 버튼: 모드 변경
    if data == "btn_mode":
        current_mode = bot.scheduler.get_mode()
        mode_text = "자동 모드 (Auto)" if current_mode == UploadMode.AUTO else "검수 모드 (Review)"

        keyboard = [
            [
                InlineKeyboardButton("🔄 자동 모드로 변경", callback_data="set_mode_auto"),
                InlineKeyboardButton("🔍 검수 모드로 변경", callback_data="set_mode_review"),
            ],
            [
                InlineKeyboardButton("◀️ 설정으로 돌아가기", callback_data="show_settings"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = (
            f"**현재 모드: {mode_text}**\n\n"
            f"🔄 **자동 모드**: 영상 생성 시 자동으로 큐에 추가\n"
            f"🔍 **검수 모드**: 영상 생성 후 승인/거부 선택\n\n"
            f"아래 버튼으로 모드를 변경하세요:"
        )

        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        return

    # 버튼: 큐 보기 (페이지네이션)
    if data.startswith("btn_queue_page_"):
        page = int(data.replace("btn_queue_page_", ""))
        queue_status = bot.scheduler.get_queue_status()

        if queue_status['total'] == 0:
            keyboard = [[InlineKeyboardButton("◀️ 큐 관리로", callback_data="queue_management")]]
            await query.edit_message_text(
                "📭 큐가 비어있습니다.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        items_per_page = 5
        total_pages = (len(bot.scheduler.queue) + items_per_page - 1) // items_per_page

        lines = [
            f"📋 **업로드 큐 ({page+1}/{total_pages} 페이지)**\n",
            f"전체: {queue_status['total']}개",
            f"승인됨: {queue_status['approved']}개",
            f"대기 중: {queue_status['pending']}개",
            f"실패: {queue_status['failed']}개\n",
            "━━━━━━━━━━━━━━━━\n"
        ]

        start_idx = page * items_per_page
        end_idx = min(start_idx + items_per_page, len(bot.scheduler.queue))

        for i in range(start_idx, end_idx):
            item = bot.scheduler.queue[i]
            status = "✅" if item.get('approved_at') else "⏳"
            retry = item.get('retry_count', 0)
            retry_text = f" (재시도:{retry})" if retry > 0 else ""
            title = item.get('title', 'N/A').replace('\n', ' ')[:25]
            lines.append(f"{i+1}. {status} {title}...{retry_text}")

        await query.edit_message_text(
            '\n'.join(lines),
            reply_markup=get_queue_page_keyboard(page, total_pages),
            parse_mode='Markdown'
        )
        return

    # 큐 아이템 상세보기
    if data.startswith("view_queue_item_"):
        idx = int(data.replace("view_queue_item_", ""))
        if idx >= len(bot.scheduler.queue):
            await query.answer("항목을 찾을 수 없습니다")
            return

        item = bot.scheduler.queue[idx]
        status = "✅ 승인됨" if item.get('approved_at') else "⏳ 대기 중"
        retry = item.get('retry_count', 0)
        last_error = item.get('last_error', '없음')

        message = (
            f"📋 **큐 항목 #{idx+1}**\n\n"
            f"**제목:** {item.get('title', 'N/A')}\n"
            f"**유형:** {item.get('quiz_type', 'N/A')}\n"
            f"**상태:** {status}\n"
            f"**재시도 횟수:** {retry}\n"
            f"**마지막 에러:** {last_error[:50]}...\n"
        )

        keyboard = [
            [InlineKeyboardButton("🗑️ 이 항목 삭제", callback_data=f"delete_queue_item_{idx}")],
            [InlineKeyboardButton("◀️ 큐 목록으로", callback_data="btn_queue_page_0")]
        ]

        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return

    # 큐 아이템 삭제
    if data.startswith("delete_queue_item_"):
        idx = int(data.replace("delete_queue_item_", ""))
        if idx >= len(bot.scheduler.queue):
            await query.answer("항목을 찾을 수 없습니다")
            return

        item = bot.scheduler.queue.pop(idx)
        bot.scheduler._save_queue(bot.scheduler.queue)

        await query.edit_message_text(f"✅ 항목이 삭제되었습니다: {item.get('title', 'N/A')[:30]}...")
        await asyncio.sleep(1)

        # 큐 목록으로 돌아가기
        await query.edit_message_text(
            "📋 **큐 관리**\n\n아래 메뉴에서 원하는 작업을 선택하세요:",
            reply_markup=get_queue_management_keyboard(),
            parse_mode='Markdown'
        )
        return

    # 실패한 영상 보기
    if data == "view_failed_videos":
        failed_videos = [item for item in bot.scheduler.queue if item.get('retry_count', 0) >= 3]

        if not failed_videos:
            keyboard = [[InlineKeyboardButton("◀️ 큐 관리로", callback_data="queue_management")]]
            await query.edit_message_text(
                "✅ 실패한 영상이 없습니다!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        lines = [
            "⚠️ **실패한 영상 목록**\n",
            f"총 {len(failed_videos)}개\n",
            "━━━━━━━━━━━━━━━━\n"
        ]

        for i, item in enumerate(failed_videos[:10], 1):
            title = item.get('title', 'N/A').replace('\n', ' ')[:30]
            error = item.get('last_error', 'N/A')[:40]
            lines.append(f"{i}. {title}...")
            lines.append(f"   에러: {error}...\n")

        if len(failed_videos) > 10:
            lines.append(f"... 외 {len(failed_videos) - 10}개")

        keyboard = [[InlineKeyboardButton("◀️ 큐 관리로", callback_data="queue_management")]]
        await query.edit_message_text(
            '\n'.join(lines),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return

    # 버튼: 스케줄 상태
    if data == "btn_schedule":
        queue_status = bot.scheduler.get_queue_status()
        next_upload = bot.scheduler.get_next_upload_time()
        paused = bot.scheduler.is_paused()
        mode = bot.scheduler.get_mode()
        interval = bot.scheduler.config.get('interval_hours', 5)

        mode_text = "자동 모드" if mode == UploadMode.AUTO else "검수 모드"
        status_text = "⏸️ 일시정지" if paused else "▶️ 실행 중"

        message = (
            f"📊 **스케줄러 상태**\n\n"
            f"상태: {status_text}\n"
            f"모드: {mode_text}\n"
            f"업로드 간격: {interval}시간\n"
            f"다음 업로드: {next_upload.strftime('%Y-%m-%d %H:%M') if next_upload else 'N/A'}\n\n"
            f"승인된 영상: {queue_status['approved']}개\n"
            f"대기 중: {queue_status['pending']}개"
        )

        keyboard = [[InlineKeyboardButton("◀️ 설정으로 돌아가기", callback_data="show_settings")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return

    # 버튼: 즉시 업로드
    if data == "btn_upload_now":
        await query.edit_message_text("⏳ 업로드 시작...")

        video_url = await bot.scheduler.upload_next_video(telegram_bot=bot)

        if video_url:
            queue_status = bot.scheduler.get_queue_status()
            keyboard = [[InlineKeyboardButton("◀️ 설정으로 돌아가기", callback_data="show_settings")]]
            await query.edit_message_text(
                f"✅ 업로드 완료!\n\n{video_url}\n\n남은 큐: {queue_status['approved']}개",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            keyboard = [[InlineKeyboardButton("◀️ 설정으로 돌아가기", callback_data="show_settings")]]
            await query.edit_message_text(
                "❌ 업로드할 영상이 없거나 업로드에 실패했습니다.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        return

    # 버튼: 일시정지
    if data == "btn_pause":
        bot.scheduler.pause()
        await query.edit_message_text(
            "⏸️ 스케줄러가 일시정지되었습니다.",
        )
        # 설정 메뉴로 다시 이동
        await asyncio.sleep(1)
        await query.edit_message_text(
            get_settings_message(),
            reply_markup=get_settings_keyboard(),
            parse_mode='Markdown'
        )
        return

    # 버튼: 재개
    if data == "btn_resume":
        bot.scheduler.resume()
        await query.edit_message_text(
            "▶️ 스케줄러가 재개되었습니다.",
        )
        # 설정 메뉴로 다시 이동
        await asyncio.sleep(1)
        await query.edit_message_text(
            get_settings_message(),
            reply_markup=get_settings_keyboard(),
            parse_mode='Markdown'
        )
        return

    # 버튼: 업로드 간격 변경
    if data == "btn_change_interval":
        current_interval = bot.scheduler.config.get('interval_hours', 5)
        await query.edit_message_text(
            f"⏱️ **업로드 간격 변경**\n\n"
            f"현재 간격: {current_interval}시간\n\n"
            f"원하는 간격을 선택하세요:",
            reply_markup=get_interval_selection_keyboard(),
            parse_mode='Markdown'
        )
        return

    # 간격 설정
    if data.startswith("set_interval_"):
        new_interval = int(data.replace("set_interval_", ""))
        old_interval = bot.scheduler.config.get('interval_hours', 5)

        if new_interval == old_interval:
            await query.answer(f"이미 {new_interval}시간으로 설정되어 있습니다")
            return

        # 간격 변경 및 스케줄러 재시작
        bot.scheduler.config['interval_hours'] = new_interval
        bot.scheduler._save_config(bot.scheduler.config)

        # 스케줄러 재시작
        bot.scheduler.restart_scheduler()

        await query.edit_message_text(
            f"✅ 업로드 간격이 {new_interval}시간으로 변경되었습니다!\n\n"
            f"스케줄러가 재시작되었습니다."
        )
        await asyncio.sleep(1.5)
        await query.edit_message_text(
            get_status_message(),
            reply_markup=get_scheduler_settings_keyboard(),
            parse_mode='Markdown'
        )
        return

    # 버튼: 큐 비우기
    if data == "btn_clear_queue":
        # 확인 버튼 표시
        keyboard = [
            [
                InlineKeyboardButton("⚠️ 네, 비웁니다", callback_data="confirm_clear_queue"),
                InlineKeyboardButton("❌ 취소", callback_data="show_settings"),
            ]
        ]
        await query.edit_message_text(
            "⚠️ **정말로 큐를 비우시겠습니까?**\n\n모든 대기 중인 영상이 삭제됩니다.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return

    # 확인: 큐 비우기
    if data == "confirm_clear_queue":
        bot.scheduler.clear_queue()
        await query.edit_message_text("🗑️ 큐가 비워졌습니다.")
        await asyncio.sleep(1)
        await query.edit_message_text(
            get_settings_message(),
            reply_markup=get_settings_keyboard(),
            parse_mode='Markdown'
        )
        return

    # 모드 변경 버튼 처리
    if data == "set_mode_auto":
        bot.scheduler.set_mode(UploadMode.AUTO)
        await query.edit_message_text("✅ 자동 모드로 변경되었습니다!\n\n영상 생성 시 자동으로 큐에 추가됩니다.")
        await asyncio.sleep(1)
        await query.edit_message_text(
            get_settings_message(),
            reply_markup=get_settings_keyboard(),
            parse_mode='Markdown'
        )
        return

    if data == "set_mode_review":
        bot.scheduler.set_mode(UploadMode.REVIEW)
        await query.edit_message_text("✅ 검수 모드로 변경되었습니다!\n\n영상 생성 후 승인/거부를 선택할 수 있습니다.")
        await asyncio.sleep(1)
        await query.edit_message_text(
            get_settings_message(),
            reply_markup=get_settings_keyboard(),
            parse_mode='Markdown'
        )
        return

    # 승인/거부 버튼 처리 (폴더명으로 찾기)
    if data.startswith("approve_"):
        video_folder = data.replace("approve_", "")
        success = bot.scheduler.approve_video_by_folder(video_folder)

        if success:
            queue_status = bot.scheduler.get_queue_status()
            await query.edit_message_text(
                f"✅ 영상이 승인되어 업로드 큐에 추가되었습니다!\n\n"
                f"승인된 영상: {queue_status['approved']}개\n"
                f"대기 중: {queue_status['pending']}개\n"
                f"다음 업로드: {bot.scheduler.get_next_upload_time().strftime('%Y-%m-%d %H:%M') if bot.scheduler.get_next_upload_time() else 'N/A'}",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("❌ 승인 실패: 해당 영상을 찾을 수 없습니다.")
        return

    if data.startswith("reject_"):
        video_folder = data.replace("reject_", "")
        success = bot.scheduler.remove_from_queue_by_folder(video_folder)

        if success:
            await query.edit_message_text("❌ 영상이 거부되어 큐에서 제거되었습니다.")
        else:
            await query.edit_message_text("❌ 거부 실패: 해당 영상을 찾을 수 없습니다.")
        return

    if data.startswith("quiz_"):
        quiz_type = data.replace("quiz_", "")

        if quiz_type == "랜덤":
            # 랜덤 선택 후 바로 생성
            quiz_type = random.choice(list(QUIZ_TYPES.keys()))
            await query.edit_message_text(
                f"🎲 랜덤 선택: **{quiz_type}** ({QUIZ_TYPES[quiz_type]['name']})\n\n"
                f"🎬 영상 생성을 시작합니다...",
                parse_mode='Markdown'
            )
            await generate_and_send(update, context, quiz_type, query.message.chat_id)
        else:
            # 퀴즈 상세 페이지 표시
            await query.edit_message_text(
                get_quiz_detail_message(quiz_type),
                reply_markup=get_quiz_detail_keyboard(quiz_type),
                parse_mode='Markdown'
            )

            # 예제 이미지가 있으면 전송
            example_image = EXAMPLES_DIR / f"{quiz_type}.png"
            if example_image.exists():
                with open(example_image, 'rb') as img:
                    await context.bot.send_photo(
                        chat_id=query.message.chat_id,
                        photo=img,
                        caption=f"📷 {quiz_type} 테스트 예시 이미지"
                    )

    elif data.startswith("generate_"):
        quiz_type = data.replace("generate_", "")
        await query.edit_message_text(
            f"🎬 **{QUIZ_TYPES[quiz_type]['name']}** 영상 생성 시작!\n\n"
            f"⏱️ 약 1~2분 소요됩니다...",
            parse_mode='Markdown'
        )
        await generate_and_send(update, context, quiz_type, query.message.chat_id)


async def generate_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE, quiz_type: str, chat_id: int):
    """영상 생성 및 전송 (진행 상태 표시 개선)"""
    if bot.generating:
        await context.bot.send_message(
            chat_id=chat_id,
            text="⏳ 이미 영상 생성 중입니다. 잠시만 기다려주세요..."
        )
        return

    bot.generating = True
    status_message = None

    try:
        # 상태 메시지 전송
        status_message = await context.bot.send_message(
            chat_id=chat_id,
            text="🎬 **영상 생성 시작**\n\n⏳ 1/4 단계: JSON 생성 중..."
        )

        # JSON 생성 단계
        await asyncio.sleep(0.5)
        await status_message.edit_text(
            "🎬 **영상 생성 진행 중**\n\n"
            "✅ 1/4 단계: JSON 생성 완료\n"
            "⏳ 2/4 단계: 이미지 생성 중..."
        )

        # 비동기로 영상 생성 (별도 스레드에서)
        loop = asyncio.get_event_loop()

        # 이미지 생성 단계 (실제 생성은 generate_quiz_video_sync에서)
        await asyncio.sleep(1)
        await status_message.edit_text(
            "🎬 **영상 생성 진행 중**\n\n"
            "✅ 1/4 단계: JSON 생성 완료\n"
            "✅ 2/4 단계: 이미지 생성 완료\n"
            "⏳ 3/4 단계: TTS 음성 생성 중..."
        )

        # TTS 생성 단계
        await asyncio.sleep(1)
        await status_message.edit_text(
            "🎬 **영상 생성 진행 중**\n\n"
            "✅ 1/4 단계: JSON 생성 완료\n"
            "✅ 2/4 단계: 이미지 생성 완료\n"
            "✅ 3/4 단계: TTS 음성 생성 완료\n"
            "⏳ 4/4 단계: 영상 렌더링 중..."
        )

        # 실제 영상 생성
        video_path, title, description = await loop.run_in_executor(
            None,
            bot.generate_quiz_video_sync,
            quiz_type
        )

        # 완료
        await status_message.edit_text(
            "🎬 **영상 생성 완료!**\n\n"
            "✅ 1/4 단계: JSON 생성 완료\n"
            "✅ 2/4 단계: 이미지 생성 완료\n"
            "✅ 3/4 단계: TTS 음성 생성 완료\n"
            "✅ 4/4 단계: 영상 렌더링 완료\n\n"
            "📤 전송 준비 중..."
        )

        # 1. 영상 전송
        await context.bot.send_message(
            chat_id=chat_id,
            text="📹 영상 전송 중..."
        )
        
        with open(video_path, 'rb') as video_file:
            await context.bot.send_video(
                chat_id=chat_id,
                video=video_file,
                caption="🎬 생성된 영상",
                supports_streaming=True
            )
        
        # 2. 제목 전송 (복사 가능한 코드 블록)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"📌 **제목** (클릭하여 복사):\n```\n{title}\n```",
            parse_mode='Markdown'
        )
        
        # 3. 해설 전송 (복사 가능한 코드 블록, 길면 분할)
        if description:
            # 한국어 메타데이터 제거 (YouTube 댓글과 동일하게)
            clean_description = extract_comment_text(description)

            # 텔레그램 메시지 길이 제한 (4096자), 코드 블록 마크업 고려
            max_len = 3900

            if len(clean_description) > max_len:
                chunks = []
                current = ""
                for line in clean_description.split('\n'):
                    if len(current) + len(line) + 1 > max_len:
                        chunks.append(current)
                        current = line
                    else:
                        current = current + '\n' + line if current else line
                if current:
                    chunks.append(current)

                for i, chunk in enumerate(chunks):
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"💬 **해설 ({i+1}/{len(chunks)})** (클릭하여 복사):\n```\n{chunk.strip()}\n```",
                        parse_mode='Markdown'
                    )
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"💬 **해설** (클릭하여 복사):\n```\n{clean_description}\n```",
                    parse_mode='Markdown'
                )
        
        # 4. 큐에 추가 (모드에 따라)
        mode = bot.scheduler.get_mode()
        quiz_type_for_queue = quiz_type  # 현재 퀴즈 유형

        if mode == UploadMode.AUTO:
            # 자동 모드: 즉시 큐에 추가
            bot.scheduler.add_to_queue(
                video_path=video_path,
                title=title,
                description=description,
                quiz_type=quiz_type_for_queue
            )
            queue_status = bot.scheduler.get_queue_status()
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"✅ 큐에 자동 추가되었습니다!\n\n"
                     f"승인된 영상: {queue_status['approved']}개\n"
                     f"다음 업로드: {bot.scheduler.get_next_upload_time().strftime('%Y-%m-%d %H:%M') if bot.scheduler.get_next_upload_time() else 'N/A'}",
                reply_markup=get_main_keyboard()
            )
        else:
            # 검수 모드: 먼저 큐에 추가 (미승인 상태), 승인/거부 버튼 표시
            bot.scheduler.add_to_queue(
                video_path=video_path,
                title=title,
                description=description,
                quiz_type=quiz_type_for_queue
            )

            # 승인/거부 버튼 (video_path 대신 폴더명만 사용 - 텔레그램 64바이트 제한)
            from pathlib import Path
            video_folder = Path(video_path).parent.name

            keyboard = [
                [
                    InlineKeyboardButton("✅ 승인 (큐에 추가)", callback_data=f"approve_{video_folder}"),
                    InlineKeyboardButton("❌ 거부 (삭제)", callback_data=f"reject_{video_folder}"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🔍 **검수 모드**\n\n이 영상을 업로드 큐에 추가하시겠습니까?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        # 5. 완료 메시지 + 다시 시작 버튼
        await context.bot.send_message(
            chat_id=chat_id,
            text="✨ 모든 전송 완료!\n\n다른 영상을 만들려면 아래 버튼을 누르세요.",
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"영상 생성 오류: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ 영상 생성 실패: {e}\n\n다시 시도해주세요.",
            reply_markup=get_main_keyboard()
        )
    
    finally:
        bot.generating = False


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """메시지 처리"""
    text = update.message.text.strip()
    
    # 도움말/시작 키워드
    if text in ["도움말", "도움", "help", "?", "목록", "리스트", "시작", "start", "메뉴"]:
        await update.message.reply_text(
            get_help_message(),
            reply_markup=get_main_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # 랜덤 퀴즈
    if text in ["랜덤", "random", "아무거나"]:
        quiz_type = random.choice(list(QUIZ_TYPES.keys()))
        await update.message.reply_text(
            f"🎲 랜덤 선택: **{quiz_type}** ({QUIZ_TYPES[quiz_type]['name']})\n\n"
            f"🎬 영상 생성을 시작합니다...",
            parse_mode='Markdown'
        )
        await generate_and_send(update, context, quiz_type, update.effective_chat.id)
        return
    
    # 퀴즈 유형 확인
    quiz_type = resolve_quiz_type(text)
    
    if quiz_type:
        # 퀴즈 상세 페이지 표시
        await update.message.reply_text(
            get_quiz_detail_message(quiz_type),
            reply_markup=get_quiz_detail_keyboard(quiz_type),
            parse_mode='Markdown'
        )
        
        # 예제 이미지가 있으면 전송
        example_image = EXAMPLES_DIR / f"{quiz_type}.png"
        if example_image.exists():
            with open(example_image, 'rb') as img:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=img,
                    caption=f"📷 {quiz_type} 테스트 예시 이미지"
                )
    else:
        # 알 수 없는 명령어 - 메뉴 표시
        await update.message.reply_text(
            "❓ 아래 버튼에서 퀴즈 유형을 선택해주세요!",
            reply_markup=get_main_keyboard()
        )


async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """모드 확인 및 변경"""
    current_mode = bot.scheduler.get_mode()
    mode_text = "자동 모드 (Auto)" if current_mode == UploadMode.AUTO else "검수 모드 (Review)"

    keyboard = [
        [
            InlineKeyboardButton("🔄 자동 모드로 변경", callback_data="set_mode_auto"),
            InlineKeyboardButton("🔍 검수 모드로 변경", callback_data="set_mode_review"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"**현재 모드: {mode_text}**\n\n"
        f"🔄 **자동 모드**: 영상 생성 시 자동으로 큐에 추가\n"
        f"🔍 **검수 모드**: 영상 생성 후 승인/거부 선택\n\n"
        f"아래 버튼으로 모드를 변경하세요:"
    )

    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')


async def queue_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """큐 목록 표시"""
    queue_status = bot.scheduler.get_queue_status()

    if queue_status['total'] == 0:
        await update.message.reply_text("📭 큐가 비어있습니다.")
        return

    # 큐 목록 생성
    lines = [
        f"📋 **업로드 큐 현황**\n",
        f"전체: {queue_status['total']}개",
        f"승인됨: {queue_status['approved']}개",
        f"대기 중: {queue_status['pending']}개\n",
        "━━━━━━━━━━━━━━━━\n"
    ]

    for i, item in enumerate(bot.scheduler.queue[:10], 1):  # 최대 10개
        status = "✅" if item.get('approved_at') else "⏳"
        title = item.get('title', 'N/A').replace('\n', ' ')[:30]
        lines.append(f"{i}. {status} {title}...")

    if len(bot.scheduler.queue) > 10:
        lines.append(f"\n... 외 {len(bot.scheduler.queue) - 10}개")

    await update.message.reply_text('\n'.join(lines), parse_mode='Markdown')


async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """스케줄러 상태 표시"""
    queue_status = bot.scheduler.get_queue_status()
    next_upload = bot.scheduler.get_next_upload_time()
    paused = bot.scheduler.is_paused()
    mode = bot.scheduler.get_mode()
    interval = bot.scheduler.config.get('interval_hours', 5)

    mode_text = "자동 모드" if mode == UploadMode.AUTO else "검수 모드"
    status_text = "⏸️ 일시정지" if paused else "▶️ 실행 중"

    message = (
        f"📊 **스케줄러 상태**\n\n"
        f"상태: {status_text}\n"
        f"모드: {mode_text}\n"
        f"업로드 간격: {interval}시간\n"
        f"다음 업로드: {next_upload.strftime('%Y-%m-%d %H:%M') if next_upload else 'N/A'}\n\n"
        f"승인된 영상: {queue_status['approved']}개\n"
        f"대기 중: {queue_status['pending']}개"
    )

    await update.message.reply_text(message, parse_mode='Markdown')


async def upload_now_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """즉시 업로드"""
    await update.message.reply_text("⏳ 업로드 시작...")

    video_url = await bot.scheduler.upload_next_video(telegram_bot=bot)

    if video_url:
        queue_status = bot.scheduler.get_queue_status()
        await update.message.reply_text(
            f"✅ 업로드 완료!\n\n{video_url}\n\n남은 큐: {queue_status['approved']}개"
        )
    else:
        await update.message.reply_text("❌ 업로드할 영상이 없거나 업로드에 실패했습니다.")


async def pause_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """스케줄러 일시정지"""
    bot.scheduler.pause()
    await update.message.reply_text("⏸️ 스케줄러가 일시정지되었습니다.")


async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """스케줄러 재개"""
    bot.scheduler.resume()
    await update.message.reply_text("▶️ 스케줄러가 재개되었습니다.")


async def clear_queue_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """큐 비우기"""
    bot.scheduler.clear_queue()
    await update.message.reply_text("🗑️ 큐가 비워졌습니다.")


async def post_init(application: Application):
    """봇 초기화 후 실행되는 콜백"""
    # 텔레그램 봇 인스턴스 설정
    bot.scheduler.set_telegram_bot(bot)
    # 스케줄러 시작 (event loop가 실행된 후)
    bot.scheduler.start()
    print(f"⏰ 스케줄러 시작 (5시간 간격)")


def main():
    """봇 실행"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
        print("   .env 파일에 TELEGRAM_BOT_TOKEN=your_token 추가하세요.")
        return

    # 예제 이미지 디렉토리 생성
    EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    print("🤖 텔레그램 봇 시작...")
    print(f"📁 예제 이미지 디렉토리: {EXAMPLES_DIR}")
    print("\n사용 가능한 퀴즈 유형:")
    for key, info in QUIZ_TYPES.items():
        print(f"  {info['emoji']} {key}: {info['name']}")

    # 봇 생성
    application = Application.builder().token(token).build()

    # 봇 인스턴스 설정
    bot.bot_instance = application.bot

    # 핸들러 등록
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("mode", mode_command))
    application.add_handler(CommandHandler("queue", queue_command))
    application.add_handler(CommandHandler("schedule", schedule_command))
    application.add_handler(CommandHandler("upload_now", upload_now_command))
    application.add_handler(CommandHandler("pause", pause_command))
    application.add_handler(CommandHandler("resume", resume_command))
    application.add_handler(CommandHandler("clear_queue", clear_queue_command))
    application.add_handler(CallbackQueryHandler(quiz_type_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 초기화 후 콜백 설정
    application.post_init = post_init

    # 봇 실행
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
