
import os
import sys
import json
import subprocess
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# 로컬의 .env 파일 로드
load_dotenv(Path(__file__).parent.parent / ".env")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY가 설정되지 않았습니다.")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)

# 모델 설정
MODEL_NAME = "gemini-2.5-flash"
generation_config = {
    "temperature": 0.4,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 2048,
}

def transcribe_audio(video_path: Path):
    """Whisper를 사용하여 오디오 추출 및 자막 생성"""
    print("🔊 오디오 추출 및 자막 생성 중 (Whisper)...")
    try:
        import whisper
    except ImportError:
        print("Whisper가 설치되지 않았습니다. pip install openai-whisper")
        return None

    model = whisper.load_model("base")
    result = model.transcribe(str(video_path), language="ko")
    return result["segments"]

def extract_frame(video_path: Path, timestamp: float, output_path: Path):
    """지정된 시간의 프레임 추출"""
    cmd = [
        "ffmpeg", "-y", "-ss", str(timestamp), "-i", str(video_path),
        "-frames:v", "1", "-q:v", "2", str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path

def analyze_frame(image_path: Path, script_text: str):
    """Gemini를 사용하여 프레임 분석"""
    model = genai.GenerativeModel(model_name=MODEL_NAME, generation_config=generation_config)
    
    prompt = f"""
    이 이미지는 유튜브 쇼츠 영상의 한 장면입니다.
    현재 대사: "{script_text}"
    
    이 장면을 '이라스토야(Irasutoya)' 스타일의 일러스트로 다시 그리려고 합니다.
    다음 항목을 상세하게 분석해서 설명해주세요:
    1. 상황 묘사 (누가, 어디서, 무엇을 하고 있나)
    2. 캐릭터의 표정과 감정 (이모지 포함)
    3. 주요 행동이나 동작
    4. 배경 요소
    5. 이라스토야 스타일 생성을 위한 추천 프롬프트 (영어)
    
    형식:
    - 상황: ...
    - 감정: ...
    - 행동: ...
    - 프롬프트: irasutoya style, flat illustration, ...
    """
    
    image_part = {
        "mime_type": "image/jpeg",
        "data": image_path.read_bytes()
    }
    
    try:
        response = model.generate_content([prompt, image_part])
        return response.text
    except Exception as e:
        return f"분석 실패: {e}"

def main():
    video_path = Path("/Users/songjin-ug/Desktop/japan/shorts.mp4")
    output_dir = Path("/Users/songjin-ug/Desktop/japan/analysis_output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not video_path.exists():
        print(f"❌ 영상 파일이 없습니다: {video_path}")
        return

    # 1. 자막 생성
    segments = transcribe_audio(video_path)
    if not segments:
        return

    print(f"✅ 총 {len(segments)}개 대사 구간 분석 시작")
    
    analysis_results = []
    
    for i, seg in enumerate(segments):
        start = seg['start']
        end = seg['end']
        text = seg['text']
        midpoint = (start + end) / 2
        
        print(f"\n[{i+1}/{len(segments)}] {start:.1f}s ~ {end:.1f}s: {text}")
        
        # 2. 프레임 추출
        frame_path = output_dir / f"frame_{i:03d}.jpg"
        extract_frame(video_path, midpoint, frame_path)
        
        # 3. 이미지 분석
        if frame_path.exists():
            analysis = analyze_frame(frame_path, text)
            print("-" * 40)
            print(analysis)
            print("-" * 40)
            
            analysis_results.append({
                "time": f"{start:.1f}-{end:.1f}",
                "text": text,
                "analysis": analysis
            })
        else:
            print("❌ 프레임 추출 실패")

    # 결과 저장
    with open(output_dir / "full_analysis.json", "w", encoding="utf-8") as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 분석 완료! 결과 저장됨: {output_dir / 'full_analysis.json'}")

if __name__ == "__main__":
    main()

