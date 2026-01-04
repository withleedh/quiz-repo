#!/usr/bin/env python3
"""
퀴즈 영상 자동 생성 파이프라인

실행하면 타임스탬프 기반 폴더를 생성하고
그 안에 모든 결과물(영상, 이미지, TTS, JSON 등)을 저장합니다.

사용법:
  python quiz_pipeline.py --auto                    # 완전 자동 생성
  python quiz_pipeline.py --auto --theme "테마"     # 테마 지정
  python quiz_pipeline.py quiz.json                 # JSON 파일 사용
"""

import sys

# Windows 콘솔 인코딩 문제 해결
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import json
import os
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# 스크립트 디렉토리를 path에 추가
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

BASE_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = BASE_DIR / "output"
RESOURCES_DIR = BASE_DIR / "resources"
SOUNDS_DIR = RESOURCES_DIR / "sounds"

# 기본 효과음
DEFAULT_INTRO_SOUND = str(SOUNDS_DIR / "intro_sound.wav")
DEFAULT_POPUP_SOUND = str(SOUNDS_DIR / "popup_sound.wav")


def load_preset_config() -> dict:
    """GUI 에디터에서 저장한 기본 설정 로드"""
    preset_path = RESOURCES_DIR / "quiz_config.json"
    
    if preset_path.exists():
        with open(preset_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 상대 경로를 절대 경로로 변환
        for key in ["intro_sound", "popup_sound"]:
            if key in config and config[key]:
                sound_path = Path(config[key])
                if not sound_path.is_absolute():
                    config[key] = str(BASE_DIR / sound_path)
        
        return config
    
    # 기본 설정
    return {
        "bg_top_color": "#C2B299",
        "bg_middle_color": "#C2B299",
        "bg_bottom_color": "#C2B299",
        "title_y": 250,
        "title_font_size": 90,
        "title_color1": "#FFC800",
        "title_color2": "#FF6496",
        "title_outline_color": "#323232",
        "title_outline_width": 5,
        "image_y": 500,
        "image_max_width": 900,
        "image_max_height": 800,
        "image_remove_bg": True,
        "image_bg_threshold": 240,
        "button_y": 1400,
        "button_width": 220,
        "button_height": 120,
        "button_spacing": 20,
        "button_color": "#FFE600",
        "button_border_color": "#c1b299",
        "button_font_size": 45,
        "button_text_color": "#000000",
        "badge_color": "#619cf4",
        "badge_size": 78,
        "badge_offset_y": -85,
        "badge_font_size": 60,
        "badge_text_color": "#f5ffe2",
        "sparkle_count": 50,
        "sparkle_color": "#FFFFC8",
        "tts_speaker_id": 2,
        "tts_speed": 1.0,
        "intro_sound": DEFAULT_INTRO_SOUND,
        "popup_sound": DEFAULT_POPUP_SOUND,
        "button_fade_start": 0.5,
        "button_fade_duration": 0.2,
        "badge_fade_start": 2.0,
        "badge_fade_duration": 0.2,
    }


def generate_quiz_video(quiz_json: dict, output_name: str = None, skip_image_gen: bool = False) -> str:
    """
    퀴즈 영상 전체 생성 파이프라인
    
    실행시점 기준으로 폴더를 생성하고 모든 결과물을 해당 폴더에 저장합니다.
    
    폴더 구조:
    output/YYYYMMDD_HHMMSS_테마/
    ├── quiz_video.mp4        # 최종 영상
    ├── image.png             # 생성된 이미지
    ├── narration.wav         # TTS 음성
    ├── narration.srt         # 자막
    ├── quiz_config.json      # 퀴즈 설정 JSON
    └── analysis.txt          # 해석 텍스트
    
    Args:
        quiz_json: 퀴즈 설정 JSON
        output_name: 출력 폴더명 (지정하지 않으면 자동 생성)
        skip_image_gen: 이미지 생성 건너뛰기
    
    Returns:
        생성된 영상 파일 경로
    """
    print("=" * 60)
    print("🎬 퀴즈 영상 자동 생성 파이프라인")
    print("=" * 60)
    
    # 기본 설정 로드 및 병합
    config = load_preset_config()
    
    # 메타데이터 추출
    metadata = quiz_json.get("quiz_metadata", {})
    theme = metadata.get("theme", "Mystery")
    target_n = metadata.get("target_answer_n", metadata.get("total_hidden_objects", 10))
    generated_faces = metadata.get("generated_faces_count", target_n + 1)
    
    # UI 요소 추출
    ui = quiz_json.get("ui_elements", {})
    title_text = ui.get("top_title", "")
    narration_script = ui.get("narration_script", "")
    buttons = ui.get("selection_buttons", [])
    
    # TTS/사운드 설정 추출
    tts_config = quiz_json.get("tts_config", {})
    sound_config = quiz_json.get("sound_config", {})
    
    # 설정 업데이트
    config["title_text"] = title_text
    config["buttons"] = buttons
    config["narration_script"] = narration_script
    
    if tts_config:
        config["tts_speaker_id"] = tts_config.get("speaker_id", config.get("tts_speaker_id", 2))
        config["tts_speed"] = tts_config.get("speed", config.get("tts_speed", 1.0))
    
    if sound_config:
        config["intro_sound"] = sound_config.get("intro_sound", DEFAULT_INTRO_SOUND)
        config["popup_sound"] = sound_config.get("popup_sound", DEFAULT_POPUP_SOUND)
    
    # ==================== 출력 폴더 생성 ====================
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_theme = theme.replace(" ", "_").lower()[:20]
    
    if output_name:
        folder_name = f"{timestamp}_{output_name}"
    else:
        folder_name = f"{timestamp}_{safe_theme}"
    
    # 실행시점 기준 폴더 생성
    run_output_dir = OUTPUT_DIR / folder_name
    run_output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📁 출력 폴더: {run_output_dir}")
    
    # 파일 경로 설정
    video_path = run_output_dir / "quiz_video.mp4"
    image_path_out = run_output_dir / "image.png"
    narration_wav_path = run_output_dir / "narration.wav"
    narration_srt_path = run_output_dir / "narration.srt"
    config_json_path = run_output_dir / "quiz_config.json"
    analysis_txt_path = run_output_dir / "analysis.txt"
    
    # ==================== 1단계: 이미지 생성 ====================
    image_path = quiz_json.get("image_path")
    
    if not image_path or not os.path.exists(image_path):
        if skip_image_gen:
            print("⚠️ 이미지가 없고 생성도 건너뛰기 설정됨. 기본 이미지 필요.")
            return None
        
        print("\n📷 [1/3] 이미지 생성 중...")
        
        image_config = quiz_json.get("image_generation", {})
        prompt = image_config.get("prompt", "")
        
        if not prompt:
            # 기본 프롬프트 생성
            prompt = f"""An intricate optical illusion of {theme}. 
Using advanced pareidolia techniques, masterfully hide EXACTLY {generated_faces} human faces within the textures and shapes of the scene. 
The composition must contain strictly {generated_faces} identifiable silhouettes, no more and no less. 
Ensure high contrast and clean artistic lines to prevent unintentional facial shapes. 
Style: monochromatic vintage aesthetic, 4k, ultra-detailed."""
        
        try:
            from image_generator import generate_image
            
            image_path = generate_image(prompt, str(image_path_out), aspect_ratio="1:1")
            
            if not image_path:
                print("❌ 이미지 생성 실패")
                return None
                
        except Exception as e:
            print(f"❌ 이미지 생성 오류: {e}")
            return None
    else:
        print(f"\n📷 [1/3] 기존 이미지 사용: {image_path}")
        # 기존 이미지를 출력 폴더로 복사
        shutil.copy(image_path, image_path_out)
        image_path = str(image_path_out)
    
    config["image_path"] = image_path
    
    # ==================== 2단계: TTS 생성 ====================
    print("\n🎤 [2/3] TTS 나레이션 준비 중...")
    
    narration_audio = None
    if narration_script:
        try:
            import subprocess
            
            # 임시 스크립트 파일 생성
            temp_script = run_output_dir / "narration_temp.txt"
            temp_script.write_text(narration_script, encoding="utf-8")
            
            # 별도 프로세스에서 TTS 실행
            speaker_id = config.get("tts_speaker_id", 2)
            speed = config.get("tts_speed", 1.0)
            
            result = subprocess.run([
                sys.executable, str(SCRIPT_DIR / "api.py"),
                "--speaker", str(speaker_id),
                "--speed", str(speed),
                "--output", str(run_output_dir / "narration"),
                "--split", "line",
                str(temp_script)
            ], capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=str(SCRIPT_DIR))
            
            # TTS 출력 표시
            if result.stdout:
                print(result.stdout)
            
            if result.returncode == 0:
                narration_audio = str(narration_wav_path)
            else:
                print(f"   ⚠️ TTS 생성 실패: {result.stderr}")
            
            # 임시 파일 삭제
            temp_script.unlink(missing_ok=True)
            
            if narration_audio and os.path.exists(narration_audio):
                file_size = os.path.getsize(narration_audio)
                print(f"   ✅ 나레이션 생성 완료 (크기: {file_size} bytes)")
                if file_size < 1000:
                    print(f"   ⚠️ 파일이 너무 작습니다! TTS 생성에 문제가 있을 수 있습니다.")
                    narration_audio = None
            else:
                print("   ⚠️ 나레이션 생성 실패 (VOICEVOX 실행 확인 필요)")
        except Exception as e:
            print(f"   ⚠️ TTS 생성 건너뜀: {e}")
    else:
        print("   ⏭️ 나레이션 스크립트 없음, 건너뜀")
    
    # ==================== 3단계: 영상 생성 ====================
    print("\n🎬 [3/3] 영상 생성 중...")
    
    try:
        from quiz_generator import QuizVideoGenerator
        
        generator = QuizVideoGenerator(config)
        generator.generate(
            output_path=str(video_path),
            duration=5.0,
            narration_audio=narration_audio,
            intro_sound=config.get("intro_sound"),
            popup_sound=config.get("popup_sound")
        )
        
    except Exception as e:
        print(f"❌ 영상 생성 오류: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # ==================== 4단계: 추가 파일 저장 ====================
    print("\n📦 [4/4] 추가 파일 저장 중...")
    
    # 퀴즈 설정 JSON 저장
    with open(config_json_path, 'w', encoding='utf-8') as f:
        json.dump(quiz_json, f, ensure_ascii=False, indent=2)
    print(f"   💾 퀴즈 설정: {config_json_path.name}")
    
    # 해석 텍스트 저장
    analysis = quiz_json.get("detailed_analysis_comment", "")
    if analysis:
        # 딕셔너리인 경우 JSON 문자열로 변환
        if isinstance(analysis, dict):
            analysis = json.dumps(analysis, ensure_ascii=False, indent=2)
        elif not isinstance(analysis, str):
            analysis = str(analysis)
        
        # buttons가 리스트인지 확인
        buttons_str = ', '.join(buttons) if isinstance(buttons, list) else str(buttons)
        
        with open(analysis_txt_path, 'w', encoding='utf-8') as f:
            f.write(f"테마: {theme}\n")
            f.write(f"정답 (N): {target_n}개\n")
            f.write(f"생성된 얼굴 수: {generated_faces}개\n")
            f.write(f"선택지: {buttons_str}\n")
            f.write("=" * 40 + "\n\n")
            f.write(analysis)
        print(f"   📄 해석 텍스트: {analysis_txt_path.name}")
    
    # ==================== 완료 ====================
    print("\n" + "=" * 60)
    print(f"🎉 완료! 생성된 폴더: {run_output_dir}")
    print("=" * 60)
    print(f"\n📂 폴더 내용:")
    for f in run_output_dir.iterdir():
        size = f.stat().st_size
        if size > 1024 * 1024:
            size_str = f"{size / 1024 / 1024:.1f} MB"
        elif size > 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size} B"
        print(f"   - {f.name} ({size_str})")
    
    return str(video_path)


def main():
    parser = argparse.ArgumentParser(
        description="퀴즈 영상 자동 생성 파이프라인",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 🚀 완전 자동 생성 (JSON도 AI가 생성)
  python quiz_pipeline.py --auto
  
  # 테마 지정하여 자동 생성
  python quiz_pipeline.py --auto --theme "Steampunk City"
  
  # JSON 파일로 영상 생성
  python quiz_pipeline.py quiz.json
  
  # 출력 폴더명 지정
  python quiz_pipeline.py quiz.json -o my_quiz
  
  # 이미지 생성 건너뛰기 (기존 이미지 사용)
  python quiz_pipeline.py quiz.json --skip-image
        """
    )
    
    parser.add_argument("json_file", nargs="?", help="퀴즈 설정 JSON 파일 (--auto 사용시 생략 가능)")
    parser.add_argument("-o", "--output", help="출력 폴더명")
    parser.add_argument("--skip-image", action="store_true", help="이미지 생성 건너뛰기")
    parser.add_argument("--auto", action="store_true", help="JSON 자동 생성 (Gemini API)")
    parser.add_argument("--type", default="치매", help="퀴즈 유형 (치매/IQ/관찰력/노안/성격/우울/지능/겸손)")
    parser.add_argument("--theme", "-t", help="자동 생성시 테마 지정")
    
    args = parser.parse_args()
    
    # 자동 생성 모드
    if args.auto:
        print("\n🤖 완전 자동 모드 - JSON부터 영상까지 모두 자동 생성")
        print("=" * 60)
        
        try:
            from quiz_json_generator import generate_quiz_json
            
            # JSON 생성 (템플릿 유형 + 선택적 테마)
            quiz_json = generate_quiz_json(args.type, args.theme)
            
        except ImportError as e:
            print(f"❌ 모듈 로드 오류: {e}")
            print("   google-genai 설치: pip install google-genai")
            sys.exit(1)
        except Exception as e:
            print(f"❌ JSON 생성 오류: {e}")
            sys.exit(1)
    
    # JSON 파일에서 로드
    elif args.json_file:
        json_path = Path(args.json_file)
        if not json_path.exists():
            print(f"❌ 파일을 찾을 수 없습니다: {json_path}")
            sys.exit(1)
        
        with open(json_path, 'r', encoding='utf-8') as f:
            quiz_json = json.load(f)
    
    else:
        print("❌ JSON 파일 경로를 지정하거나 --auto 옵션을 사용하세요.")
        parser.print_help()
        sys.exit(1)
    
    # 영상 생성
    result = generate_quiz_video(
        quiz_json,
        output_name=args.output,
        skip_image_gen=args.skip_image
    )
    
    if not result:
        sys.exit(1)


if __name__ == "__main__":
    main()
