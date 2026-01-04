#!/usr/bin/env python3
"""
YouTube 업로드 테스트 스크립트
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from upload_scheduler import get_scheduler

# 테스트할 영상 정보
VIDEO_DIR = Path("/Users/songjin-ug/Desktop/japan/output/20251227_032753_cute_animals_count")
VIDEO_PATH = str(VIDEO_DIR / "quiz_video.mp4")

# quiz_config.json 읽기
with open(VIDEO_DIR / "quiz_config.json", 'r', encoding='utf-8') as f:
    config = json.load(f)

# 제목과 설명 추출
title = config["ui_elements"]["top_title"]  # 줄바꿈 포함
description = config["detailed_analysis_comment"]  # 해석 내용

print("=" * 60)
print("📋 테스트 영상 정보")
print("=" * 60)
print(f"영상 경로: {VIDEO_PATH}")
print(f"\n원본 제목 (줄바꿈 포함):")
print(f'"{title}"')
print(f"\n해석 내용 (앞부분):")
print(f'"{description[:100]}..."')
print("=" * 60)

# 큐에 추가
scheduler = get_scheduler()
print("\n📥 큐에 영상 추가 중...")
scheduler.add_to_queue(
    video_path=VIDEO_PATH,
    title=title,
    description=description,
    quiz_type="personality"
)

# 자동 모드로 설정 (자동 승인)
scheduler.set_mode("auto")
print("✅ 자동 모드 설정 완료")

# 큐 상태 확인
queue_status = scheduler.get_queue_status()
print(f"\n📊 큐 상태:")
print(f"  - 전체: {queue_status['total']}개")
print(f"  - 승인됨: {queue_status['approved']}개")

# 비동기 실행을 위한 코드
import asyncio

async def test_upload():
    print("\n" + "=" * 60)
    print("🚀 YouTube 업로드 시작")
    print("=" * 60)

    video_url = await scheduler.upload_next_video(telegram_bot=None)

    print("\n" + "=" * 60)
    if video_url:
        print("✅ 업로드 성공!")
        print(f"🔗 URL: {video_url}")
        print("\n📝 업로드된 내용 확인:")
        print("  1. 제목: 줄바꿈이 공백으로 변경되었는지 확인")
        print("  2. 설명: 제목과 동일한지 확인")
        print("  3. 댓글: 해석 내용이 작성되었는지 확인")
    else:
        print("❌ 업로드 실패")
    print("=" * 60)

# 실행
asyncio.run(test_upload())
