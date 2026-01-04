#!/usr/bin/env python3
"""
스케줄러 신규 기능 테스트
- 타임존 자동 감지
- 즉시 업로드 옵션
"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from upload_scheduler import get_scheduler, TIMEZONE

print("=" * 60)
print("✅ 스케줄러 신규 기능 테스트")
print("=" * 60)

scheduler = get_scheduler()

# 1. 타임존 자동 감지 확인
print(f"\n1️⃣ 타임존 자동 감지:")
print(f"   감지된 타임존: {TIMEZONE}")
print(f"   현재 시간: {datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')}")

# 2. 즉시 업로드 옵션 확인
print(f"\n2️⃣ 즉시 업로드 옵션:")
current_immediate = scheduler.get_upload_immediately()
print(f"   현재 상태: {'ON ⚡' if current_immediate else 'OFF ⏳'}")

# 3. 즉시 업로드 옵션 토글 테스트
print(f"\n3️⃣ 즉시 업로드 옵션 토글 테스트:")
print(f"   ON으로 변경...")
scheduler.set_upload_immediately(True)
print(f"   현재 상태: {'ON ⚡' if scheduler.get_upload_immediately() else 'OFF ⏳'}")

print(f"\n   OFF로 변경...")
scheduler.set_upload_immediately(False)
print(f"   현재 상태: {'ON ⚡' if scheduler.get_upload_immediately() else 'OFF ⏳'}")

# 4. 설정 파일 확인
print(f"\n4️⃣ 설정 파일 확인:")
print(f"   모드: {scheduler.get_mode()}")
print(f"   업로드 간격: {scheduler.config.get('interval_hours', 5)}시간")
print(f"   일시정지: {scheduler.is_paused()}")
print(f"   즉시 업로드: {scheduler.get_upload_immediately()}")

# 5. 큐 상태 확인
print(f"\n5️⃣ 큐 상태:")
queue_status = scheduler.get_queue_status()
print(f"   전체: {queue_status['total']}개")
print(f"   승인됨: {queue_status['approved']}개")
print(f"   대기 중: {queue_status['pending']}개")

# 6. 다음 업로드 시간
print(f"\n6️⃣ 다음 업로드 예정 시간:")
next_upload = scheduler.get_next_upload_time()
if next_upload:
    print(f"   {next_upload.strftime('%Y-%m-%d %H:%M:%S %Z')}")
else:
    print(f"   N/A")

print("\n" + "=" * 60)
print("✅ 테스트 완료!")
print("=" * 60)
