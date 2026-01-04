#!/usr/bin/env python3
"""
YouTube 업로드 재테스트 (댓글 포함)
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from upload_scheduler import get_scheduler

# 다른 영상으로 테스트
VIDEO_DIR = Path("/Users/songjin-ug/Desktop/japan/output/20251227_032417_cloud_illusion")
VIDEO_PATH = str(VIDEO_DIR / "quiz_video.mp4")

# quiz_config.json 읽기
with open(VIDEO_DIR / "quiz_config.json", 'r', encoding='utf-8') as f:
    config = json.load(f)

# 제목과 설명 추출
title = config["ui_elements"]["top_title"]
description = config["detailed_analysis_comment"]

print("=" * 60)
print("📋 테스트 영상 정보 (2차)")
print("=" * 60)
print(f"영상 경로: {VIDEO_PATH}")
print(f"\n원본 제목:")
print(f'"{title}"')
has_newline = '\n' in title
print(f"\n제목 줄바꿈 확인: {'포함됨' if has_newline else '없음'}")
print("=" * 60)

# 큐 초기화
scheduler = get_scheduler()
scheduler.clear_queue()

# 큐에 추가
print("\n📥 큐에 영상 추가 중...")
scheduler.add_to_queue(
    video_path=VIDEO_PATH,
    title=title,
    description=description,
    quiz_type="depression"
)

# 비동기 실행
import asyncio

async def test_upload():
    print("\n" + "=" * 60)
    print("🚀 YouTube 업로드 시작 (댓글 권한 재인증)")
    print("=" * 60)
    print("\n⚠️ 브라우저가 열리면 Google 로그인을 진행하세요!")
    print("   모든 권한(업로드 + 댓글)을 허용해주세요.\n")

    video_url = await scheduler.upload_next_video(telegram_bot=None)

    print("\n" + "=" * 60)
    if video_url:
        print("✅ 업로드 성공!")
        print(f"🔗 URL: {video_url}")
        print("\n📋 YouTube에서 확인사항:")
        print("  1. ✅ 제목: 한 줄로 표시되는지")
        print("  2. ✅ 설명: 제목과 동일한지")
        print("  3. ✅ 댓글: 해석 내용이 작성되었는지")
        print("\n위 URL을 직접 확인해주세요!")
    else:
        print("❌ 업로드 실패")
    print("=" * 60)

asyncio.run(test_upload())
