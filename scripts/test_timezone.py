#!/usr/bin/env python3
"""
타임존 테스트 스크립트
"""
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent))

from upload_scheduler import get_scheduler, TIMEZONE

print("=" * 60)
print("⏰ 타임존 테스트")
print("=" * 60)

# 1. 시스템 시간
now_system = datetime.now()
print(f"\n1️⃣ 시스템 시간 (timezone 없음):")
print(f"   {now_system}")
print(f"   {now_system.isoformat()}")

# 2. UTC 시간
now_utc = datetime.now(ZoneInfo("UTC"))
print(f"\n2️⃣ UTC 시간:")
print(f"   {now_utc}")
print(f"   {now_utc.isoformat()}")

# 3. Asia/Seoul 시간
now_seoul = datetime.now(ZoneInfo("Asia/Seoul"))
print(f"\n3️⃣ Asia/Seoul 시간 (코드에서 사용):")
print(f"   {now_seoul}")
print(f"   {now_seoul.isoformat()}")

# 4. 스케줄러 설정 확인
scheduler = get_scheduler()
print(f"\n4️⃣ 스케줄러 설정:")
print(f"   타임존: {TIMEZONE}")
print(f"   스케줄러 타임존: {scheduler.scheduler.timezone}")

# 5. 다음 업로드 시간
next_upload = scheduler.get_next_upload_time()
if next_upload:
    print(f"\n5️⃣ 다음 업로드 시간:")
    print(f"   {next_upload}")
    print(f"   {next_upload.isoformat()}")
    print(f"   타임존: {next_upload.tzinfo}")
else:
    print(f"\n5️⃣ 다음 업로드 시간: N/A")

# 6. 마지막 업로드 시간
last_upload = scheduler.config.get("last_upload")
if last_upload:
    print(f"\n6️⃣ 마지막 업로드 시간 (설정 파일):")
    print(f"   원본: {last_upload}")
    last_dt = datetime.fromisoformat(last_upload)
    if last_dt.tzinfo is None:
        last_dt = last_dt.replace(tzinfo=TIMEZONE)
    print(f"   파싱: {last_dt}")
    print(f"   타임존: {last_dt.tzinfo}")
else:
    print(f"\n6️⃣ 마지막 업로드 시간: N/A")

print("\n" + "=" * 60)
print("✅ 테스트 완료")
print("=" * 60)

# 텔레그램으로 전송
import asyncio
import os
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

async def send_to_telegram():
    from telegram import Bot

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")  # 본인의 chat_id 설정 필요

    if not token:
        print("\n⚠️ TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
        return

    bot = Bot(token)

    # 메시지 작성
    message = f"""⏰ **타임존 테스트 결과**

1️⃣ 시스템 시간: `{now_system.strftime('%Y-%m-%d %H:%M:%S')}`

2️⃣ UTC 시간: `{now_utc.strftime('%Y-%m-%d %H:%M:%S')}`

3️⃣ Asia/Seoul: `{now_seoul.strftime('%Y-%m-%d %H:%M:%S')}`

4️⃣ 스케줄러 타임존: `{scheduler.scheduler.timezone}`

5️⃣ 다음 업로드: `{next_upload.strftime('%Y-%m-%d %H:%M:%S') if next_upload else 'N/A'}`

6️⃣ 마지막 업로드: `{last_upload if last_upload else 'N/A'}`
"""

    try:
        # 최근 대화에서 chat_id 가져오기
        updates = await bot.get_updates()
        if updates:
            chat_id = updates[-1].message.chat_id
            await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
            print(f"\n✅ 텔레그램 전송 완료 (chat_id: {chat_id})")
        else:
            print(f"\n⚠️ 텔레그램 대화 없음. 먼저 봇에게 메시지를 보내주세요.")
    except Exception as e:
        print(f"\n❌ 텔레그램 전송 실패: {e}")

# 텔레그램 전송 실행
asyncio.run(send_to_telegram())
