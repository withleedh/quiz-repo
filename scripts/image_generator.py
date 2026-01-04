#!/usr/bin/env python3
"""
이미지 생성 모듈
Gemini API를 사용하여 퀴즈용 이미지를 생성합니다.
"""

import sys

# Windows 콘솔 인코딩 문제 해결
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import mimetypes
from pathlib import Path
from typing import Optional


def generate_image(prompt: str, output_path: str = None, aspect_ratio: str = "1:1") -> Optional[str]:
    """
    Gemini API를 사용하여 이미지 생성 (항상 1:1 비율)
    
    Args:
        prompt: 이미지 생성 프롬프트
        output_path: 출력 파일 경로 (None이면 자동 생성)
        aspect_ratio: 이미지 비율 (무시됨, 항상 "1:1" 사용)
    
    Returns:
        생성된 이미지 파일 경로 (실패 시 None)
    """
    # 모든 이미지는 1:1 비율로 고정
    aspect_ratio = "1:1"
    try:
        from google import genai
        from google.genai import types
        from dotenv import load_dotenv
    except ImportError:
        print("⚠️ 필요한 패키지 설치: pip install google-genai python-dotenv")
        return None
    
    # .env 파일에서 API 키 로드
    load_dotenv()
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return None
    
    print(f"🎨 이미지 생성 시작...")
    print(f"   프롬프트: {prompt[:100]}...")
    
    client = genai.Client(api_key=api_key)
    
    model = "gemini-3-pro-image-preview"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    
    tools = [
        types.Tool(googleSearch=types.GoogleSearch()),
    ]
    
    generate_content_config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
        image_config=types.ImageConfig(
            image_size="1K",
            aspect_ratio="1:1",
        ),
        tools=tools,
    )
    
    generated_path = None
    
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if (
            chunk.candidates is None
            or chunk.candidates[0].content is None
            or chunk.candidates[0].content.parts is None
        ):
            continue
        
        part = chunk.candidates[0].content.parts[0]
        if part.inline_data and part.inline_data.data:
            inline_data = part.inline_data
            data_buffer = inline_data.data
            file_extension = mimetypes.guess_extension(inline_data.mime_type) or ".png"
            
            if output_path:
                # 확장자가 없으면 추가
                if not any(output_path.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
                    generated_path = output_path + file_extension
                else:
                    generated_path = output_path
            else:
                generated_path = f"generated_image{file_extension}"
            
            with open(generated_path, "wb") as f:
                f.write(data_buffer)
            
            print(f"✅ 이미지 생성 완료: {generated_path}")
            return generated_path
        
        else:
            if hasattr(part, 'text') and part.text:
                print(f"   📝 응답: {part.text}")
    
    print("❌ 이미지 생성 실패")
    return None


def generate_quiz_image(theme: str, hidden_objects: int, style: str = "monochromatic vintage aesthetic", output_dir: str = None) -> Optional[str]:
    """
    퀴즈용 착시 이미지 생성
    
    Args:
        theme: 이미지 테마 (예: "Vintage Clockwork and Gears")
        hidden_objects: 숨겨진 얼굴 개수
        style: 아트 스타일
        output_dir: 출력 디렉토리
    
    Returns:
        생성된 이미지 파일 경로
    """
    prompt = f"""An intricate optical illusion of {theme}. 
Using advanced pareidolia techniques, masterfully hide EXACTLY {hidden_objects} human faces within the textures and shapes of the scene. 
The composition must contain strictly {hidden_objects} identifiable silhouettes, no more and no less. 
Ensure high contrast and clean artistic lines to prevent unintentional facial shapes. 
Style: {style}, 4k, ultra-detailed."""
    
    if output_dir:
        output_path = str(Path(output_dir) / f"quiz_{theme.replace(' ', '_').lower()}")
    else:
        output_path = None
    
    return generate_image(prompt, output_path, aspect_ratio="1:1")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="이미지 생성기")
    parser.add_argument("--prompt", "-p", help="이미지 생성 프롬프트")
    parser.add_argument("--theme", "-t", help="퀴즈 테마")
    parser.add_argument("--objects", "-n", type=int, default=10, help="숨겨진 얼굴 개수")
    parser.add_argument("--output", "-o", help="출력 파일 경로")
    parser.add_argument("--ratio", "-r", default="1:1", help="이미지 비율")
    
    args = parser.parse_args()
    
    if args.prompt:
        generate_image(args.prompt, args.output, args.ratio)
    elif args.theme:
        generate_quiz_image(args.theme, args.objects, output_dir=args.output or ".")
    else:
        print("사용법: python image_generator.py --prompt '프롬프트' 또는 --theme '테마'")
