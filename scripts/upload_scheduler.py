#!/usr/bin/env python3
"""
YouTube 업로드 스케줄러 (재작성 버전)

기능:
- 업로드 큐 관리 (JSON 파일)
- 5시간 간격 자동 업로드
- 모드: Auto (자동 큐잉) vs Review (승인 후 큐잉)
- 스케줄러 일시정지/재개
- 업로드 실패 시 재시도 로직
- 개선된 에러 처리 및 상태 관리
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import asyncio
from zoneinfo import ZoneInfo
import tzlocal
import random
import subprocess
import sys

logger = logging.getLogger(__name__)

# 타임존 자동 감지 (시스템 로컬 타임존)
def get_local_timezone() -> ZoneInfo:
    """시스템의 로컬 타임존 자동 감지"""
    try:
        local_tz = tzlocal.get_localzone()
        logger.info(f"자동 감지된 타임존: {local_tz}")
        return local_tz
    except Exception as e:
        logger.warning(f"타임존 자동 감지 실패, Asia/Seoul로 대체: {e}")
        return ZoneInfo("Asia/Seoul")

TIMEZONE = get_local_timezone()

# 경로 설정
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
QUEUE_FILE = BASE_DIR / "upload_queue.json"
CONFIG_FILE = BASE_DIR / "scheduler_config.json"

# 재시도 설정
MAX_RETRY_COUNT = 3


def extract_comment_text(full_text: str) -> str:
    """
    analysis.txt에서 댓글로 사용할 부분만 추출
    (한국어 메타데이터 제거)

    Args:
        full_text: analysis.txt 전체 내용

    Returns:
        댓글로 사용할 일본어 부분만
    """
    if not full_text:
        return ""

    # "========================================" 구분선을 기준으로 분리
    separator = "========================================"

    if separator in full_text:
        parts = full_text.split(separator, 1)
        if len(parts) > 1:
            # 구분선 이후 내용만 반환 (앞뒤 공백 제거)
            return parts[1].strip()

    # 구분선이 없으면 원본 반환
    return full_text


class UploadMode:
    """업로드 모드"""
    AUTO = "auto"      # 자동 큐잉
    REVIEW = "review"  # 검수 후 큐잉


class UploadScheduler:
    """YouTube 업로드 스케줄러"""

    def __init__(self, telegram_bot=None):
        """
        Args:
            telegram_bot: 텔레그램 봇 인스턴스 (알림 전송용)
        """
        self.scheduler = AsyncIOScheduler(timezone=TIMEZONE)
        self.telegram_bot = telegram_bot
        self.config = self._load_config()
        self.queue = self._load_queue()
        self._upload_lock = asyncio.Lock()

    def set_telegram_bot(self, telegram_bot):
        """텔레그램 봇 인스턴스 설정"""
        self.telegram_bot = telegram_bot

    def _load_config(self) -> Dict[str, Any]:
        """설정 파일 로드"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # 불필요한 필드 제거
            config.pop("upload_immediately", None)
            return config
        else:
            # 기본 설정
            default_config = {
                "mode": UploadMode.REVIEW,      # 기본: 검수 모드
                "interval_hours": 5,             # 업로드 간격: 5시간
                "paused": False,                 # 스케줄러 상태
                "last_upload": None,             # 마지막 업로드 시간
                "next_upload": None,             # 다음 업로드 예정 시간
                "auto_generate": False,          # 자동 영상 생성 여부
                "topics": ["치매", "IQ", "관찰력", "노안", "성격", "우울", "지능", "겸손"],  # 주제 목록
                "admin_chat_ids": [],            # 알림을 받을 관리자 채팅 ID 목록
            }
            self._save_config(default_config)
            return default_config

    def _save_config(self, config: Dict[str, Any]):
        """설정 파일 저장"""
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def _load_queue(self) -> List[Dict[str, Any]]:
        """큐 파일 로드"""
        if QUEUE_FILE.exists():
            with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
                queue = json.load(f)
            # 기존 큐 항목에 retry_count, last_error 추가 (없으면)
            for item in queue:
                item.setdefault("retry_count", 0)
                item.setdefault("last_error", None)
            return queue
        else:
            self._save_queue([])
            return []

    def _save_queue(self, queue: List[Dict[str, Any]]):
        """큐 파일 저장"""
        with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
            json.dump(queue, f, ensure_ascii=False, indent=2)

    def get_mode(self) -> str:
        """현재 모드 반환"""
        return self.config.get("mode", UploadMode.REVIEW)

    def set_mode(self, mode: str):
        """모드 변경"""
        if mode not in [UploadMode.AUTO, UploadMode.REVIEW]:
            raise ValueError(f"Invalid mode: {mode}")
        self.config["mode"] = mode
        self._save_config(self.config)
        logger.info(f"모드 변경: {mode}")

    def is_paused(self) -> bool:
        """일시정지 상태 확인"""
        return self.config.get("paused", False)

    def pause(self):
        """스케줄러 일시정지"""
        self.config["paused"] = True
        self._save_config(self.config)
        logger.info("스케줄러 일시정지")

    def resume(self):
        """스케줄러 재개"""
        self.config["paused"] = False
        self._save_config(self.config)
        logger.info("스케줄러 재개")

    def add_to_queue(
        self,
        video_path: str,
        title: str,
        description: str,
        quiz_type: str
    ) -> Dict[str, Any]:
        """
        큐에 영상 추가

        Returns:
            추가된 항목
        """
        item = {
            "video_path": video_path,
            "title": title,
            "description": description,
            "quiz_type": quiz_type,
            "created_at": datetime.now(TIMEZONE).isoformat(),
            "approved_at": datetime.now(TIMEZONE).isoformat() if self.get_mode() == UploadMode.AUTO else None,
            "retry_count": 0,
            "last_error": None,
        }

        self.queue.append(item)
        self._save_queue(self.queue)
        logger.info(f"큐에 추가: {title} (총 {len(self.queue)}개)")

        return item

    def approve_video(self, video_path: str) -> bool:
        """
        검수 모드: 영상 승인

        Returns:
            승인 성공 여부
        """
        for item in self.queue:
            if item["video_path"] == video_path and item["approved_at"] is None:
                item["approved_at"] = datetime.now(TIMEZONE).isoformat()
                self._save_queue(self.queue)
                logger.info(f"영상 승인: {item['title']}")
                return True
        return False

    def approve_video_by_folder(self, video_folder: str) -> bool:
        """
        검수 모드: 폴더명으로 영상 승인

        Args:
            video_folder: 영상 폴더명 (예: "20251227_032753_cute_animals_count")

        Returns:
            승인 성공 여부
        """
        for item in self.queue:
            if video_folder in item["video_path"] and item["approved_at"] is None:
                item["approved_at"] = datetime.now(TIMEZONE).isoformat()
                self._save_queue(self.queue)
                logger.info(f"영상 승인: {item['title']}")
                return True
        return False

    def remove_from_queue(self, video_path: str) -> bool:
        """
        큐에서 영상 제거 (최근 추가된 영상 하나만 삭제)

        Returns:
            제거 성공 여부
        """
        # 매칭되는 항목들을 찾아서 가장 최근 것만 삭제
        matching_items = [(idx, item) for idx, item in enumerate(self.queue)
                         if item["video_path"] == video_path]

        if not matching_items:
            return False

        # created_at 기준으로 정렬하여 가장 최근 항목 찾기
        matching_items.sort(key=lambda x: x[1]["created_at"], reverse=True)
        idx_to_remove = matching_items[0][0]

        removed_item = self.queue.pop(idx_to_remove)
        self._save_queue(self.queue)
        logger.info(f"큐에서 제거: {removed_item['title']} (created_at: {removed_item['created_at']})")
        return True

    def remove_from_queue_by_folder(self, video_folder: str) -> bool:
        """
        큐에서 폴더명으로 영상 제거 (최근 추가된 영상 하나만 삭제)

        Args:
            video_folder: 영상 폴더명 (예: "20251227_032753_cute_animals_count")

        Returns:
            제거 성공 여부
        """
        # 매칭되는 항목들을 찾아서 가장 최근 것만 삭제
        matching_items = [(idx, item) for idx, item in enumerate(self.queue)
                         if video_folder in item["video_path"]]

        if not matching_items:
            return False

        # created_at 기준으로 정렬하여 가장 최근 항목 찾기
        matching_items.sort(key=lambda x: x[1]["created_at"], reverse=True)
        idx_to_remove = matching_items[0][0]

        removed_item = self.queue.pop(idx_to_remove)
        self._save_queue(self.queue)
        logger.info(f"큐에서 제거: {removed_item['title']} (created_at: {removed_item['created_at']})")
        return True

    def get_next_video(self) -> Optional[Dict[str, Any]]:
        """
        다음 업로드할 영상 반환 (승인된 영상 중 가장 오래된 것, 재시도 횟수 초과 제외)

        Returns:
            다음 영상 정보 또는 None
        """
        # 승인된 영상만 필터링 (재시도 횟수 초과 제외)
        approved = [
            item for item in self.queue
            if item.get("approved_at") is not None
            and item.get("retry_count", 0) < MAX_RETRY_COUNT
        ]

        if not approved:
            return None

        # created_at 기준 정렬 (가장 오래된 것)
        approved.sort(key=lambda x: x["created_at"])
        return approved[0]

    def get_queue_status(self) -> Dict[str, Any]:
        """
        큐 상태 반환

        Returns:
            {
                "total": 전체 큐 크기,
                "approved": 승인된 영상 수,
                "pending": 대기 중인 영상 수 (검수 모드만),
                "failed": 재시도 횟수 초과 영상 수,
            }
        """
        approved = [item for item in self.queue if item.get("approved_at") is not None]
        pending = [item for item in self.queue if item.get("approved_at") is None]
        failed = [item for item in self.queue if item.get("retry_count", 0) >= MAX_RETRY_COUNT]

        return {
            "total": len(self.queue),
            "approved": len(approved),
            "pending": len(pending),
            "failed": len(failed),
        }

    def clear_queue(self):
        """큐 비우기"""
        self.queue = []
        self._save_queue(self.queue)
        logger.info("큐 초기화")

    def get_next_upload_time(self) -> Optional[datetime]:
        """
        다음 업로드 예정 시간 반환 (config에서 읽기)

        Returns:
            다음 업로드 시간 또는 None
        """
        next_upload = self.config.get("next_upload")
        if next_upload:
            next_time = datetime.fromisoformat(next_upload)
            # timezone이 없으면 추가
            if next_time.tzinfo is None:
                next_time = next_time.replace(tzinfo=TIMEZONE)
            return next_time
        return None

    def _update_next_upload_time(self, next_time: datetime):
        """다음 업로드 시간 업데이트"""
        self.config["next_upload"] = next_time.isoformat()
        self._save_config(self.config)

    async def _generate_video(self) -> Optional[Dict[str, Any]]:
        """
        자동으로 영상 생성 (랜덤 주제)

        Returns:
            생성된 영상 정보 또는 None
        """
        topics = self.config.get("topics", [])
        if not topics:
            logger.warning("주제 목록이 비어있습니다")
            return None

        # 랜덤 주제 선택
        quiz_type = random.choice(topics)
        logger.info(f"자동 생성 시작: {quiz_type} 주제")

        try:
            # quiz_pipeline.py를 subprocess로 실행
            quiz_pipeline_path = SCRIPT_DIR / "quiz_pipeline.py"

            result = subprocess.run(
                [
                    sys.executable,
                    str(quiz_pipeline_path),
                    "--auto",
                    "--type", quiz_type
                ],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=str(SCRIPT_DIR)
            )

            if result.returncode != 0:
                logger.error(f"영상 생성 실패: {result.stderr}")
                return None

            # 생성된 폴더 찾기 (가장 최근)
            output_dir = BASE_DIR / "output"
            if not output_dir.exists():
                logger.error("output 폴더가 존재하지 않습니다")
                return None

            # 가장 최근 폴더 찾기
            folders = sorted(output_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
            if not folders:
                logger.error("생성된 폴더를 찾을 수 없습니다")
                return None

            latest_folder = folders[0]
            video_path = latest_folder / "quiz_video.mp4"
            config_path = latest_folder / "quiz_config.json"
            analysis_path = latest_folder / "analysis.txt"

            if not video_path.exists():
                logger.error(f"영상 파일을 찾을 수 없습니다: {video_path}")
                return None

            # 제목과 설명 읽기
            title = ""
            description = ""

            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    quiz_config = json.load(f)
                    ui_elements = quiz_config.get("ui_elements", {})
                    title = ui_elements.get("top_title", "")

            if analysis_path.exists():
                with open(analysis_path, 'r', encoding='utf-8') as f:
                    description = f.read()

            if not title:
                title = f"{quiz_type} 테스트"

            logger.info(f"영상 생성 완료: {video_path}")

            return {
                "video_path": str(video_path),
                "title": title,
                "description": description,
                "quiz_type": quiz_type,
            }

        except Exception as e:
            logger.error(f"영상 생성 오류: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _perform_upload(self, video_item: Dict[str, Any]) -> Optional[str]:
        """
        실제 업로드 수행

        Args:
            video_item: 업로드할 영상 정보

        Returns:
            업로드된 영상 URL 또는 None
        """
        video_path = video_item["video_path"]

        # 파일 존재 확인
        if not Path(video_path).exists():
            error_msg = f"파일이 존재하지 않습니다: {video_path}"
            logger.error(error_msg)
            video_item["last_error"] = error_msg
            video_item["retry_count"] = MAX_RETRY_COUNT  # 재시도 안함
            self._save_queue(self.queue)
            return None

        try:
            # YouTube 업로드
            from youtube_uploader import upload_with_comment

            raw_title = video_item["title"]
            detailed_analysis = video_item["description"]

            # 제목: 줄바꿈을 공백으로 변경 (YouTube는 제목에 줄바꿈 불가)
            title = raw_title.replace('\n', ' ').strip()

            # 설명: 제목과 동일
            description = title

            # 댓글: detailed_analysis_comment (해석 내용)
            # 한국어 메타데이터 제거 후 일본어 부분만 사용
            comment_text = extract_comment_text(detailed_analysis) if detailed_analysis else None

            logger.info(f"업로드 시작: {title}")

            video_id, comment_id = upload_with_comment(
                video_path=video_path,
                title=title,
                description=description,
                comment_text=comment_text,
                tags=["치매예방", "認知症", "퀴즈", "テスト"],
                category_id="22",  # People & Blogs
                privacy_status="public"
            )

            video_url = f"https://youtube.com/watch?v={video_id}"
            logger.info(f"업로드 완료: {video_url}")

            return video_url

        except Exception as e:
            error_msg = f"업로드 실패: {str(e)}"
            logger.error(error_msg)

            # 재시도 카운트 증가 및 에러 기록
            video_item["retry_count"] = video_item.get("retry_count", 0) + 1
            video_item["last_error"] = error_msg
            self._save_queue(self.queue)

            if video_item["retry_count"] >= MAX_RETRY_COUNT:
                logger.error(f"최대 재시도 횟수 초과: {title} (retry_count: {video_item['retry_count']})")

            return None

    async def upload_next_video(self) -> Optional[str]:
        """
        다음 영상 업로드 (스케줄러에서 호출)

        Returns:
            업로드된 영상 URL 또는 None
        """
        # 일시정지 상태 확인
        if self.is_paused():
            logger.info("스케줄러 일시정지 상태 - 업로드 건너뜀")
            return None

        # 락 획득 (중복 업로드 방지)
        if self._upload_lock.locked():
            logger.warning("이미 업로드 진행 중")
            return None

        async with self._upload_lock:
            # 다음 영상 가져오기
            next_video = self.get_next_video()

            if not next_video:
                # 자동 생성 옵션 확인
                auto_generate = self.config.get("auto_generate", False)

                if auto_generate:
                    logger.info("큐가 비어있어 자동으로 영상 생성을 시도합니다")

                    # 영상 자동 생성
                    video_info = await self._generate_video()

                    if video_info:
                        # 큐에 추가
                        item = self.add_to_queue(
                            video_path=video_info["video_path"],
                            title=video_info["title"],
                            description=video_info["description"],
                            quiz_type=video_info["quiz_type"]
                        )

                        # 다음 영상으로 설정
                        next_video = item
                        logger.info(f"자동 생성된 영상이 큐에 추가되었습니다: {item['title']}")
                    else:
                        logger.error("자동 영상 생성 실패")
                        return None
                else:
                    logger.info("업로드할 영상이 없습니다")
                    return None

            # 업로드 수행
            video_url = await self._perform_upload(next_video)

            if video_url:
                # 업로드 성공 - 큐에서 제거
                self.remove_from_queue(next_video["video_path"])

                # 마지막 업로드 시간 및 다음 업로드 시간 업데이트
                now = datetime.now(TIMEZONE)
                self.config["last_upload"] = now.isoformat()

                interval_hours = self.config.get("interval_hours", 5)
                next_upload_time = now + timedelta(hours=interval_hours)
                self._update_next_upload_time(next_upload_time)

                logger.info(f"다음 업로드 예정: {next_upload_time.strftime('%Y-%m-%d %H:%M')}")

                # 텔레그램 알림 전송
                if self.telegram_bot:
                    try:
                        await self.telegram_bot.send_upload_notification(
                            title=next_video["title"],
                            video_url=video_url,
                            remaining=len(self.queue)
                        )
                    except Exception as e:
                        logger.error(f"텔레그램 알림 실패: {e}")

            return video_url

    def start(self):
        """스케줄러 시작"""
        interval_hours = self.config.get("interval_hours", 5)
        last_upload = self.config.get("last_upload")

        # 다음 업로드 시점 계산
        if last_upload:
            last_time = datetime.fromisoformat(last_upload)
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=TIMEZONE)
            next_upload_time = last_time + timedelta(hours=interval_hours)
        else:
            # 마지막 업로드가 없으면 즉시 시작 (5초 후)
            next_upload_time = datetime.now(TIMEZONE) + timedelta(seconds=5)

        # 다음 업로드 시간 저장
        self._update_next_upload_time(next_upload_time)

        # 단일 IntervalTrigger 사용 (자동 반복)
        self.scheduler.add_job(
            func=self.upload_next_video,  # async 함수 직접 등록
            trigger=IntervalTrigger(hours=interval_hours, start_date=next_upload_time),
            id="youtube_upload",
            name="YouTube 업로드",
            replace_existing=True,
        )

        self.scheduler.start()

        next_run = next_upload_time.strftime('%Y-%m-%d %H:%M')
        logger.info(f"스케줄러 시작 (첫 실행: {next_run}, 이후 {interval_hours}시간 간격)")

    def stop(self):
        """스케줄러 중지"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("스케줄러 중지")

    def restart_scheduler(self):
        """스케줄러 재시작 (간격 변경 시 사용)"""
        logger.info("스케줄러 재시작 중...")

        # 기존 스케줄러 중지
        if self.scheduler.running:
            # 기존 job 제거
            if self.scheduler.get_job("youtube_upload"):
                self.scheduler.remove_job("youtube_upload")

        # 새로운 설정으로 스케줄러 재시작
        interval_hours = self.config.get("interval_hours", 5)
        last_upload = self.config.get("last_upload")

        # 다음 업로드 시점 계산
        if last_upload:
            last_time = datetime.fromisoformat(last_upload)
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=TIMEZONE)
            next_upload_time = last_time + timedelta(hours=interval_hours)
        else:
            # 마지막 업로드가 없으면 즉시 시작 (5초 후)
            next_upload_time = datetime.now(TIMEZONE) + timedelta(seconds=5)

        # 다음 업로드 시간 저장
        self._update_next_upload_time(next_upload_time)

        # 새로운 job 추가
        self.scheduler.add_job(
            func=self.upload_next_video,
            trigger=IntervalTrigger(hours=interval_hours, start_date=next_upload_time),
            id="youtube_upload",
            name="YouTube 업로드",
            replace_existing=True,
        )

        next_run = next_upload_time.strftime('%Y-%m-%d %H:%M')
        logger.info(f"스케줄러 재시작 완료 (첫 실행: {next_run}, 이후 {interval_hours}시간 간격)")


# 싱글톤 인스턴스
_scheduler_instance: Optional[UploadScheduler] = None


def get_scheduler(telegram_bot=None) -> UploadScheduler:
    """스케줄러 인스턴스 반환 (싱글톤)"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = UploadScheduler(telegram_bot)
    elif telegram_bot is not None:
        _scheduler_instance.set_telegram_bot(telegram_bot)
    return _scheduler_instance
