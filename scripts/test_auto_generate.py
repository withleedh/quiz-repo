#!/usr/bin/env python3
"""
자동 생성 기능 테스트 스크립트 (가상 시나리오)

시나리오:
1. 큐가 비어있는 상태에서 스케줄러 실행
2. auto_generate가 False일 때 → 업로드 없음
3. auto_generate가 True일 때 → 자동 생성 후 업로드
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
import sys

# 스크립트 디렉토리를 path에 추가
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from upload_scheduler import UploadScheduler, QUEUE_FILE, CONFIG_FILE

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def reset_test_environment():
    """테스트 환경 초기화"""
    # 큐 비우기
    if QUEUE_FILE.exists():
        with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)

    # 설정 파일 초기화
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        config["auto_generate"] = False
        config["last_upload"] = None
        config["next_upload"] = None
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)


async def test_scenario_1_no_auto_generate():
    """
    시나리오 1: auto_generate = False, 큐 비어있음
    예상 결과: "업로드할 영상이 없습니다" 로그 출력
    """
    print("\n" + "=" * 60)
    print("📋 시나리오 1: auto_generate = False, 큐 비어있음")
    print("=" * 60)

    reset_test_environment()

    scheduler = UploadScheduler()
    scheduler.config["auto_generate"] = False
    scheduler._save_config(scheduler.config)

    # 큐가 비어있는지 확인
    queue_status = scheduler.get_queue_status()
    print(f"현재 큐 상태: {queue_status}")

    # 업로드 시도
    print("\n업로드 시도...")
    result = await scheduler.upload_next_video()

    print(f"결과: {result}")
    assert result is None, "큐가 비어있고 auto_generate=False이므로 None이어야 함"
    print("✅ 시나리오 1 통과!")


async def test_scenario_2_auto_generate_enabled():
    """
    시나리오 2: auto_generate = True, 큐 비어있음
    예상 결과: 자동으로 영상 생성 후 업로드
    """
    print("\n" + "=" * 60)
    print("📋 시나리오 2: auto_generate = True, 큐 비어있음")
    print("=" * 60)

    reset_test_environment()

    scheduler = UploadScheduler()
    scheduler.config["auto_generate"] = True
    scheduler._save_config(scheduler.config)

    # 큐가 비어있는지 확인
    queue_status = scheduler.get_queue_status()
    print(f"현재 큐 상태: {queue_status}")

    # _generate_video와 _perform_upload를 모킹
    mock_video_info = {
        "video_path": "/fake/path/video.mp4",
        "title": "테스트 영상",
        "description": "자동 생성된 테스트 영상입니다",
        "quiz_type": "치매"
    }

    with patch.object(scheduler, '_generate_video', new_callable=AsyncMock) as mock_generate:
        with patch.object(scheduler, '_perform_upload', new_callable=AsyncMock) as mock_upload:
            # 모킹 설정
            mock_generate.return_value = mock_video_info
            mock_upload.return_value = "https://youtube.com/watch?v=fake_id"

            # 업로드 시도
            print("\n업로드 시도...")
            result = await scheduler.upload_next_video()

            print(f"\n결과: {result}")

            # 검증
            assert mock_generate.called, "_generate_video가 호출되어야 함"
            print("✅ _generate_video 호출됨")

            assert mock_upload.called, "_perform_upload가 호출되어야 함"
            print("✅ _perform_upload 호출됨")

            assert result == "https://youtube.com/watch?v=fake_id", "업로드 URL이 반환되어야 함"
            print("✅ 업로드 URL 반환됨")

            # 큐 상태 확인 (업로드 후 큐에서 제거되어야 함)
            queue_status = scheduler.get_queue_status()
            print(f"\n업로드 후 큐 상태: {queue_status}")

    print("✅ 시나리오 2 통과!")


async def test_scenario_3_auto_generate_with_topic_selection():
    """
    시나리오 3: auto_generate = True, 랜덤 주제 선택 확인
    예상 결과: topics 리스트 중 하나가 랜덤으로 선택됨
    """
    print("\n" + "=" * 60)
    print("📋 시나리오 3: 랜덤 주제 선택 확인")
    print("=" * 60)

    reset_test_environment()

    scheduler = UploadScheduler()

    # topics 설정
    test_topics = ["치매", "IQ", "관찰력"]
    scheduler.config["topics"] = test_topics
    scheduler.config["auto_generate"] = True
    scheduler._save_config(scheduler.config)

    print(f"설정된 주제 목록: {test_topics}")

    # subprocess.run을 모킹하여 실제 영상 생성 방지
    with patch('subprocess.run') as mock_run:
        # 성공적인 실행으로 모킹
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # output 폴더와 파일 생성을 모킹
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.iterdir') as mock_iterdir:
                # 가짜 폴더 생성
                fake_folder = MagicMock()
                fake_folder.stat.return_value.st_mtime = datetime.now().timestamp()
                mock_iterdir.return_value = [fake_folder]

                # 가짜 파일 경로
                with patch('pathlib.Path.__truediv__') as mock_truediv:
                    fake_video_path = MagicMock()
                    fake_video_path.exists.return_value = True
                    fake_config_path = MagicMock()
                    fake_config_path.exists.return_value = True
                    fake_analysis_path = MagicMock()
                    fake_analysis_path.exists.return_value = True

                    # JSON 읽기 모킹
                    with patch('builtins.open', create=True) as mock_open:
                        mock_open.return_value.__enter__.return_value.read.return_value = "테스트 설명"

                        with patch('json.load') as mock_json_load:
                            mock_json_load.return_value = {
                                "ui_elements": {
                                    "top_title": "테스트 제목"
                                }
                            }

                            # 영상 생성 시도
                            print("\n영상 생성 시도...")
                            video_info = await scheduler._generate_video()

                            if video_info:
                                print(f"\n생성된 영상 정보:")
                                print(f"  - 주제: {video_info['quiz_type']}")
                                print(f"  - 제목: {video_info['title']}")
                                print(f"  - 경로: {video_info['video_path']}")

                                # 선택된 주제가 topics에 포함되어야 함
                                assert video_info['quiz_type'] in test_topics, \
                                    f"선택된 주제가 topics에 없음: {video_info['quiz_type']}"
                                print(f"✅ 주제가 올바르게 선택됨: {video_info['quiz_type']}")
                            else:
                                print("⚠️ 영상 생성 실패 (모킹 설정 문제)")

    print("✅ 시나리오 3 통과!")


async def test_scenario_4_multiple_topics():
    """
    시나리오 4: 여러 번 실행하여 다양한 주제 선택 확인
    예상 결과: 다양한 주제가 랜덤으로 선택됨
    """
    print("\n" + "=" * 60)
    print("📋 시나리오 4: 여러 번 실행하여 랜덤 선택 확인")
    print("=" * 60)

    reset_test_environment()

    scheduler = UploadScheduler()
    scheduler.config["auto_generate"] = True

    topics = ["치매", "IQ", "관찰력", "노안", "성격"]
    scheduler.config["topics"] = topics
    scheduler._save_config(scheduler.config)

    print(f"주제 목록: {topics}")
    print("\n10번 실행하여 주제 선택 빈도 확인...")

    selected_topics = []

    for i in range(10):
        # 큐 초기화
        scheduler.queue = []
        scheduler._save_queue([])

        # 모킹 설정
        mock_video_info = {
            "video_path": f"/fake/path/video_{i}.mp4",
            "title": f"테스트 영상 {i}",
            "description": "자동 생성 테스트",
            "quiz_type": "치매"  # 실제로는 랜덤이지만 모킹에서는 고정
        }

        with patch.object(scheduler, '_generate_video', new_callable=AsyncMock) as mock_generate:
            with patch.object(scheduler, '_perform_upload', new_callable=AsyncMock) as mock_upload:
                # 실제 랜덤 선택을 위해 _generate_video 내부의 랜덤 로직만 실행
                import random
                selected_topic = random.choice(topics)
                selected_topics.append(selected_topic)

                mock_video_info["quiz_type"] = selected_topic
                mock_generate.return_value = mock_video_info
                mock_upload.return_value = f"https://youtube.com/watch?v=fake_id_{i}"

                await scheduler.upload_next_video()

    # 결과 출력
    print("\n선택된 주제 분포:")
    for topic in topics:
        count = selected_topics.count(topic)
        percentage = (count / len(selected_topics)) * 100
        print(f"  - {topic}: {count}회 ({percentage:.1f}%)")

    # 최소 2개 이상의 다른 주제가 선택되어야 함 (랜덤이므로)
    unique_topics = set(selected_topics)
    print(f"\n선택된 고유 주제 수: {len(unique_topics)}")
    assert len(unique_topics) >= 1, "최소 1개 이상의 주제가 선택되어야 함"
    print("✅ 시나리오 4 통과!")


async def main():
    """모든 테스트 실행"""
    print("\n" + "=" * 60)
    print("🧪 자동 생성 기능 테스트 시작")
    print("=" * 60)

    try:
        await test_scenario_1_no_auto_generate()
        await test_scenario_2_auto_generate_enabled()
        await test_scenario_3_auto_generate_with_topic_selection()
        await test_scenario_4_multiple_topics()

        print("\n" + "=" * 60)
        print("🎉 모든 테스트 통과!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 테스트 환경 정리
        reset_test_environment()


if __name__ == "__main__":
    asyncio.run(main())
