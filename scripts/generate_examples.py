#!/usr/bin/env python3
"""
예제 이미지 생성 스크립트
각 퀴즈 유형별 예제 이미지를 생성합니다.
"""

import sys
import os
from pathlib import Path

# 스크립트 디렉토리
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
EXAMPLES_DIR = BASE_DIR / "resources" / "examples"
sys.path.insert(0, str(SCRIPT_DIR))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

# 퀴즈 유형별 이미지 프롬프트
EXAMPLE_PROMPTS = {
    "치매": """An intricate optical illusion artwork. Using pareidolia, hide exactly 8 human faces naturally within an ancient forest scene with twisted trees. Each face should be distinct but blended into the tree bark, leaves, and shadows. Monochromatic sepia tone, vintage aesthetic, high contrast, 4k, detailed.""",
    
    "IQ": """A minimalist chalk drawing on a black chalkboard. Numbers 6, 8, and 4 are overlapping each other vertically, creating an optical illusion. White chalk on black background, clean lines, artistic typography, high contrast.""",
    
    "관찰력": """A line art portrait of a person wearing a wide-brimmed hat. Numbers 0-9 are cleverly hidden within the lines of the face, hat, and collar. Black ink on white background, artistic sketch style, detailed pen drawing.""",
    
    "노안": """An optical illusion with spiral zigzag black and white pattern creating a rotating visual effect. Hidden numbers are subtly embedded within the geometric pattern. High contrast, mesmerizing spiral design.""",
    
    "성격": """Cute cartoon ducks in various poses on a warm beige background. Approximately 15-18 adorable ducks scattered across the image, some overlapping. Kawaii style illustration, soft pastel colors, adorable expressions.""",
    
    "우울": """A famous dual-image optical illusion that shows both a frog sitting on a lily pad and a horse head depending on how you look at it. Vintage illustration style, sepia tones, artistic ambiguous image.""",
    
    "지능": """Elegant overlapping numbers in gold/cream color on black background. Numbers like 6, 8, 4, 1 are stacked vertically creating an artistic composition. Minimalist style, high contrast, sophisticated typography.""",
    
    "겸손": """A snowy mountain landscape photograph where the rock formations naturally resemble both a dog's profile and a person's silhouette. Natural photography, winter atmosphere, pareidolia in nature.""",
}


def generate_example_image(quiz_type: str, prompt: str) -> bool:
    """단일 예제 이미지 생성"""
    from image_generator import generate_image
    
    output_path = EXAMPLES_DIR / f"{quiz_type}.png"
    
    print(f"\n{'='*50}")
    print(f"🎨 {quiz_type} 예제 이미지 생성 중...")
    print(f"{'='*50}")
    
    result = generate_image(prompt, str(output_path), aspect_ratio="1:1")
    
    if result:
        print(f"✅ {quiz_type} 이미지 생성 완료: {output_path}")
        return True
    else:
        print(f"❌ {quiz_type} 이미지 생성 실패")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="예제 이미지 생성")
    parser.add_argument("--type", "-t", help="특정 유형만 생성 (예: 치매, IQ)")
    parser.add_argument("--list", "-l", action="store_true", help="사용 가능한 유형 목록")
    
    args = parser.parse_args()
    
    # 디렉토리 생성
    EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    
    if args.list:
        print("📋 사용 가능한 퀴즈 유형:")
        for quiz_type in EXAMPLE_PROMPTS.keys():
            exists = "✅" if (EXAMPLES_DIR / f"{quiz_type}.png").exists() else "❌"
            print(f"  {exists} {quiz_type}")
        return
    
    if args.type:
        # 특정 유형만 생성
        if args.type not in EXAMPLE_PROMPTS:
            print(f"❌ 알 수 없는 유형: {args.type}")
            print(f"사용 가능한 유형: {', '.join(EXAMPLE_PROMPTS.keys())}")
            return
        
        generate_example_image(args.type, EXAMPLE_PROMPTS[args.type])
    else:
        # 전체 생성
        print("🚀 모든 예제 이미지 생성 시작...")
        print(f"📁 저장 위치: {EXAMPLES_DIR}")
        
        success = 0
        failed = 0
        
        for quiz_type, prompt in EXAMPLE_PROMPTS.items():
            # 이미 존재하면 스킵
            if (EXAMPLES_DIR / f"{quiz_type}.png").exists():
                print(f"⏭️ {quiz_type}: 이미 존재함, 스킵")
                success += 1
                continue
            
            if generate_example_image(quiz_type, prompt):
                success += 1
            else:
                failed += 1
        
        print(f"\n{'='*50}")
        print(f"📊 결과: 성공 {success}개, 실패 {failed}개")
        print(f"{'='*50}")


if __name__ == "__main__":
    main()

