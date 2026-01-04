#!/usr/bin/env python3
"""
YouTube Data API를 사용한 영상 업로더

사용 전 설정:
1. Google Cloud Console에서 YouTube Data API v3 활성화
2. OAuth 2.0 클라이언트 ID 생성 (데스크톱 앱)
3. client_secrets.json 다운로드하여 scripts 폴더에 저장
4. 첫 실행 시 브라우저에서 인증
"""

import sys
import os
import pickle
import logging
from pathlib import Path

# Windows 콘솔 인코딩 문제 해결
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 로깅
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 경로 설정
SCRIPT_DIR = Path(__file__).parent
CLIENT_SECRETS_FILE = SCRIPT_DIR / "client_secrets.json"
TOKEN_FILE = SCRIPT_DIR / "youtube_token.pickle"

# YouTube API 스코프
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"  # 댓글 작성용
]


def get_authenticated_service():
    """인증된 YouTube 서비스 객체 반환"""
    credentials = None
    
    # 기존 토큰 로드
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, 'rb') as token:
            credentials = pickle.load(token)
    
    # 토큰이 없거나 만료됨
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            if not CLIENT_SECRETS_FILE.exists():
                raise FileNotFoundError(
                    f"client_secrets.json 파일이 없습니다.\n"
                    f"Google Cloud Console에서 OAuth 클라이언트 ID를 생성하고\n"
                    f"{CLIENT_SECRETS_FILE} 경로에 저장하세요."
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRETS_FILE), SCOPES
            )
            credentials = flow.run_local_server(port=8080)
        
        # 토큰 저장
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(credentials, token)
    
    return build("youtube", "v3", credentials=credentials)


def upload_video(
    video_path: str,
    title: str,
    description: str = "",
    tags: list = None,
    category_id: str = "22",
    privacy_status: str = "public"
) -> str:
    """
    YouTube에 영상 업로드
    
    Args:
        video_path: 영상 파일 경로
        title: 영상 제목
        description: 영상 설명
        tags: 태그 리스트
        category_id: 카테고리 ID (22 = People & Blogs)
        privacy_status: 공개 상태 (public, private, unlisted)
    
    Returns:
        업로드된 영상 ID
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"영상 파일이 없습니다: {video_path}")
    
    youtube = get_authenticated_service()
    
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }
    
    # 미디어 업로드
    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024  # 1MB 청크
    )
    
    logger.info(f"📤 업로드 시작: {title}")
    
    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            logger.info(f"   업로드 진행: {progress}%")
    
    video_id = response.get("id")
    logger.info(f"✅ 업로드 완료: https://youtube.com/watch?v={video_id}")
    
    return video_id


def post_comment(video_id: str, comment_text: str) -> str:
    """
    영상에 댓글 작성
    
    Args:
        video_id: 영상 ID
        comment_text: 댓글 내용
    
    Returns:
        댓글 ID
    """
    youtube = get_authenticated_service()
    
    body = {
        "snippet": {
            "videoId": video_id,
            "topLevelComment": {
                "snippet": {
                    "textOriginal": comment_text
                }
            }
        }
    }
    
    logger.info(f"💬 댓글 작성 중...")
    
    response = youtube.commentThreads().insert(
        part="snippet",
        body=body
    ).execute()
    
    comment_id = response.get("id")
    logger.info(f"✅ 댓글 작성 완료 (ID: {comment_id})")
    
    return comment_id


def upload_with_comment(
    video_path: str,
    title: str,
    description: str = "",
    comment_text: str = None,
    tags: list = None,
    category_id: str = "22",
    privacy_status: str = "public"
) -> tuple:
    """
    영상 업로드 후 댓글 작성
    
    Args:
        video_path: 영상 파일 경로
        title: 영상 제목
        description: 영상 설명
        comment_text: 고정할 댓글 내용
        tags: 태그 리스트
        category_id: 카테고리 ID
        privacy_status: 공개 상태
    
    Returns:
        (video_id, comment_id) 튜플
    """
    # 영상 업로드
    video_id = upload_video(
        video_path=video_path,
        title=title,
        description=description,
        tags=tags,
        category_id=category_id,
        privacy_status=privacy_status
    )
    
    # 댓글 작성
    comment_id = None
    if comment_text:
        try:
            comment_id = post_comment(video_id, comment_text)
        except Exception as e:
            logger.error(f"❌ 댓글 작성 실패: {e}")
    
    return video_id, comment_id


def main():
    """테스트 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(description="YouTube 영상 업로더")
    parser.add_argument("video", help="업로드할 영상 파일")
    parser.add_argument("-t", "--title", required=True, help="영상 제목")
    parser.add_argument("-d", "--description", default="", help="영상 설명")
    parser.add_argument("--tags", nargs="+", help="태그 리스트")
    parser.add_argument("--private", action="store_true", help="비공개로 업로드")
    
    args = parser.parse_args()
    
    privacy = "private" if args.private else "public"
    
    video_id = upload_video(
        video_path=args.video,
        title=args.title,
        description=args.description or args.title,
        tags=args.tags,
        privacy_status=privacy
    )
    
    print(f"\n🎬 업로드 완료!")
    print(f"🔗 https://youtube.com/watch?v={video_id}")


if __name__ == "__main__":
    main()

