#!/usr/bin/env python3
"""
퀴즈 JSON 자동 생성기 v2
Gemini API를 사용하여 다양한 유형의 심리/IQ 테스트 퀴즈 JSON을 생성합니다.

지원 템플릿:
- 치매: 치매 예방 얼굴 찾기
- IQ: IQ 테스트 숫자 찾기  
- 관찰력: 관찰력 테스트 숫자 찾기
- 노안: 노안 테스트 착시 이미지
- 성격: 성격 테스트 동물 세기
- 우울: 우울증 테스트 이중 이미지
- 지능: 지능 테스트 숫자 찾기
- 겸손: 겸손함 테스트 이중 이미지
"""

import sys

# Windows 콘솔 인코딩 문제 해결
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import json
import re
import random
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 템플릿 정의
QUIZ_TEMPLATES = {
    "치매": {
        "name": "치매 예방 테스트",
        "description": "그림 속 숨겨진 얼굴 찾기",
        "prompt_template": """### 치매 예방 퀴즈 생성

당신은 치매 예방 퀴즈를 만드는 전문가입니다. 다음 규칙에 따라 퀴즈 JSON을 생성하세요.

**규칙:**
1. N은 3~11 사이의 랜덤 정수 (정답으로 보여야 할 얼굴 수)
2. 이미지에는 N+1개의 얼굴을 숨김 (정답 N개 + 숨겨진 1개)
3. 테마는 랜덤으로 선택 (예: 고대 유적, 숲, 도서관, 정원, 구름 등)

**버튼 범위 계산:**
- Range ④ (최고/정답): [N-1] ~ [N+1] 個
- Range ③: [N-3] ~ [N-2] 個 (최소 1)
- Range ②: [N-5] ~ [N-4] 個 (최소 1)  
- Range ①: [N-6] 個以下 (결과가 1 미만이면 "1個以下")

**JSON 구조:**
```json
{
  "quiz_metadata": {
    "theme": "[영어 테마명]",
    "target_answer_n": [N],
    "total_prompted_count": [N+1],
    "quiz_type": "dementia"
  },
  "image_generation": {
    "prompt": "An intricate optical illusion of [Theme]. Using pareidolia, hide EXACTLY [N+1] human faces naturally within the scene. Each face must be distinct and identifiable. Style: monochromatic vintage aesthetic, 4k, detailed."
  },
  "ui_elements": {
    "top_title": "認知症が始まった人は\\n違って見える絵",
    "narration_script": "認知症が始まった人には違って見えます。見えた顔の数を選んでください。",
    "selection_buttons": ["[Range①]個以下", "[Range②]個", "[Range③]個", "[Range④]個"]
  },
  "detailed_analysis_comment": "[각 선택지에 대한 상세 해설 - 일본어로]"
}
```
""",
    },
    
    "IQ": {
        "name": "IQ 테스트",
        "description": "숫자가 몇 개 보이는지 테스트",
        "prompt_template": """### IQ 테스트 퀴즈 생성

당신은 IQ 테스트 퀴즈를 만드는 전문가입니다. 다음 규칙에 따라 퀴즈 JSON을 생성하세요.

**규칙:**
1. N은 4~8 사이의 랜덤 정수 (보이는 숫자 개수)
2. 이미지는 숫자들이 겹쳐서 보이는 착시 이미지 (예: 6, 8, 4가 겹쳐진 이미지)
3. 배경은 검정색 칠판 스타일

**버튼 범위:**
- 4개의 선택지: [N-2]個, [N-1]個, [N]個, [N+1]個

**JSON 구조:**
```json
{
  "quiz_metadata": {
    "theme": "Overlapping Numbers",
    "target_answer_n": [N],
    "total_prompted_count": [N],
    "quiz_type": "iq"
  },
  "image_generation": {
    "prompt": "A minimalist chalk drawing on blackboard showing overlapping numbers. The numbers are drawn in white chalk, creating an optical illusion. Clean lines, high contrast, artistic style."
  },
  "ui_elements": {
    "top_title": "IQが130以上なら\\nすべての数字が見える",
    "narration_script": "IQが高い人にはすべての数字が見えます。いくつの数字が見えますか？",
    "selection_buttons": ["[N-2]個", "[N-1]個", "[N]個", "[N+1]個"]
  },
  "detailed_analysis_comment": "[각 선택지에 대한 IQ 관련 해설 - 일본어로]"
}
```
""",
    },
    
    "관찰력": {
        "name": "관찰력 테스트", 
        "description": "그림 속 숨겨진 숫자 찾기",
        "prompt_template": """### 관찰력 테스트 퀴즈 생성

당신은 관찰력 테스트 퀴즈를 만드는 전문가입니다. 다음 규칙에 따라 퀴즈 JSON을 생성하세요.

**규칙:**
1. N은 6~9 사이의 랜덤 정수 (숨겨진 숫자 개수)
2. 이미지는 사람 얼굴/실루엣 안에 숫자가 숨겨진 스타일
3. 스타일: 선 그림, 모자 쓴 사람 얼굴 등

**버튼:**
- 4개의 선택지: [N-3]個, [N-2]個, [N-1]個, [N]個

**JSON 구조:**
```json
{
  "quiz_metadata": {
    "theme": "Hidden Numbers Portrait",
    "target_answer_n": [N],
    "total_prompted_count": [N],
    "quiz_type": "observation"
  },
  "image_generation": {
    "prompt": "A line art portrait of a person wearing a hat. Numbers 0-9 are cleverly hidden within the lines of the face and hat. Black ink drawing on white background, artistic sketch style."
  },
  "ui_elements": {
    "top_title": "観察力が優れていれば\\n数字が[N]個すべて見える",
    "narration_script": "観察力が高い人には全ての数字が見えます。数字がいくつ見えますか？",
    "selection_buttons": ["[N-3]個", "[N-2]個", "[N-1]個", "[N]個"]
  },
  "detailed_analysis_comment": "[각 선택지에 대한 관찰력 관련 해설 - 일본어로]"
}
```
""",
    },
    
    "노안": {
        "name": "노안 테스트",
        "description": "착시 이미지에서 숫자 찾기",
        "prompt_template": """### 노안 테스트 퀴즈 생성

당신은 노안 테스트 퀴즈를 만드는 전문가입니다. 다음 규칙에 따라 퀴즈 JSON을 생성하세요.

**규칙:**
1. 착시 패턴 (회전하는 원, 지그재그 패턴) 안에 숫자가 숨겨진 이미지
2. N은 4~7 사이 (보이는 숫자 개수)

**버튼:**
- 3개의 선택지: "[N]つ", "4~6つ", "3つ以下"

**JSON 구조:**
```json
{
  "quiz_metadata": {
    "theme": "Optical Illusion Pattern",
    "target_answer_n": [N],
    "total_prompted_count": [N],
    "quiz_type": "presbyopia"
  },
  "image_generation": {
    "prompt": "An optical illusion with spiral zigzag pattern in black and white. Hidden numbers are embedded within the pattern. Creates a rotating visual effect."
  },
  "ui_elements": {
    "top_title": "老眼が始まっている人は\\n数字が3つ以下に見えます",
    "narration_script": "老眼が始まっている人には数字が少なく見えます。いくつ見えますか？",
    "selection_buttons": ["[N]つ", "4~6つ", "3つ以下"]
  },
  "detailed_analysis_comment": "[각 선택지에 대한 노안/시력 관련 해설 - 일본어로]"
}
```
""",
    },
    
    "성격": {
        "name": "성격 테스트",
        "description": "동물 개수로 성격 파악",
        "prompt_template": """### 성격 테스트 퀴즈 생성

당신은 성격 테스트 퀴즈를 만드는 전문가입니다. 다음 규칙에 따라 퀴즈 JSON을 생성하세요.

**규칙:**
1. 귀여운 동물들 (오리, 고양이, 강아지 등)이 여러 마리 있는 이미지
2. N은 13~22 사이 (실제 동물 수)
3. 동물 종류는 랜덤 선택

**버튼:**
- 3개의 선택지로 범위 표시: "20~22羽", "16~19羽", "13~15羽" (오리의 경우)

**JSON 구조:**
```json
{
  "quiz_metadata": {
    "theme": "Cute Animals Count",
    "target_answer_n": [N],
    "total_prompted_count": [N],
    "quiz_type": "personality",
    "animal_type": "[동물 종류]"
  },
  "image_generation": {
    "prompt": "Cute cartoon [animals] in various poses on a warm beige background. Kawaii style illustration, soft colors, adorable expressions. Multiple [animals] scattered across the image."
  },
  "ui_elements": {
    "top_title": "繊細な性格の持ち主は\\n違って見える絵",
    "narration_script": "繊細な人には違う数が見えます。何羽見えますか？",
    "selection_buttons": ["20~22羽", "16~19羽", "13~15羽"]
  },
  "detailed_analysis_comment": "[각 선택지에 대한 성격 분석 해설 - 일본어로]"
}
```
""",
    },
    
    "우울": {
        "name": "우울증 테스트",
        "description": "이중 이미지에서 무엇이 보이는지",
        "prompt_template": """### 우울증 테스트 퀴즈 생성

당신은 심리 테스트 퀴즈를 만드는 전문가입니다. 다음 규칙에 따라 퀴즈 JSON을 생성하세요.

**규칙:**
1. 이중 이미지 (개구리/말, 토끼/오리 등)
2. 두 가지 해석이 가능한 착시 그림
3. 선택지는 2개

**JSON 구조:**
```json
{
  "quiz_metadata": {
    "theme": "Dual Image Illusion",
    "target_answer_n": 2,
    "total_prompted_count": 2,
    "quiz_type": "depression",
    "image_options": ["[옵션1]", "[옵션2]"]
  },
  "image_generation": {
    "prompt": "A famous optical illusion showing both a [animal1] and a [animal2] depending on perspective. Vintage illustration style, sepia tones."
  },
  "ui_elements": {
    "top_title": "現在、うつ状態の人には\\n[옵션2]が見える絵",
    "narration_script": "この絵が何に見えますか？最初に見えたものを選んでください。",
    "selection_buttons": ["[옵션1]", "[옵션2]"]
  },
  "detailed_analysis_comment": "[각 선택지에 대한 심리 분석 해설 - 일본어로]"
}
```
""",
    },
    
    "지능": {
        "name": "지능 테스트",
        "description": "고지능자만 보이는 숫자",
        "prompt_template": """### 지능 테스트 퀴즈 생성

당신은 지능 테스트 퀴즈를 만드는 전문가입니다. 다음 규칙에 따라 퀴즈 JSON을 생성하세요.

**규칙:**
1. 겹쳐진 숫자들이 보이는 이미지
2. N은 5~8 사이 (보이는 숫자 개수)
3. 검정 배경에 흰색/황금색 숫자

**버튼:**
- 4개의 선택지: [N-4]個, [N-2]個, [N]個, [N+1]個

**JSON 구조:**
```json
{
  "quiz_metadata": {
    "theme": "Intelligence Numbers",
    "target_answer_n": [N],
    "total_prompted_count": [N],
    "quiz_type": "intelligence"
  },
  "image_generation": {
    "prompt": "Elegant overlapping numbers in gold/white on black background. Numbers are stacked vertically creating artistic composition. Minimalist style, high contrast."
  },
  "ui_elements": {
    "top_title": "知能が高い人だけに\\n見える絵",
    "narration_script": "知能が高い人にはすべての数字が見えます。いくつ見えますか？",
    "selection_buttons": ["[N-4]個", "[N-2]個", "[N]個", "[N+1]個"]
  },
  "detailed_analysis_comment": "[각 선택지에 대한 지능 관련 해설 - 일본어로]"
}
```
""",
    },
    
    "겸손": {
        "name": "겸손함 테스트",
        "description": "무엇이 먼저 보이는지로 성격 파악",
        "prompt_template": """### 겸손함 테스트 퀴즈 생성

당신은 성격 테스트 퀴즈를 만드는 전문가입니다. 다음 규칙에 따라 퀴즈 JSON을 생성하세요.

**규칙:**
1. 자연 풍경 사진에서 여러 가지가 보이는 이미지 (눈산, 개, 사람 실루엣 등)
2. 3개의 선택지
3. 무엇이 먼저 보이는지로 성격 판단

**JSON 구조:**
```json
{
  "quiz_metadata": {
    "theme": "Nature Perception",
    "target_answer_n": 3,
    "total_prompted_count": 3,
    "quiz_type": "humility",
    "visible_objects": ["[객체1]", "[객체2]", "[객체3]"]
  },
  "image_generation": {
    "prompt": "A snowy mountain landscape where the rock formations resemble a [animal] and a [person] silhouette. Natural photography style, winter atmosphere."
  },
  "ui_elements": {
    "top_title": "謙虚な人は\\n違って見える絵",
    "narration_script": "この絵で最初に何が見えましたか？",
    "selection_buttons": ["雪山", "犬", "人"]
  },
  "detailed_analysis_comment": "[각 선택지에 대한 성격 분석 해설 - 일본어로]"
}
```
""",
    },
}

# 템플릿 별칭 (한글/영어/일본어 대응)
TEMPLATE_ALIASES = {
    # 치매
    "치매": "치매", "dementia": "치매", "認知症": "치매", "인지": "치매",
    # IQ
    "iq": "IQ", "아이큐": "IQ", "IQ": "IQ",
    # 관찰력
    "관찰력": "관찰력", "observation": "관찰력", "観察": "관찰력", "관찰": "관찰력",
    # 노안
    "노안": "노안", "presbyopia": "노안", "老眼": "노안", "시력": "노안",
    # 성격  
    "성격": "성격", "personality": "성격", "性格": "성격",
    # 우울
    "우울": "우울", "depression": "우울", "うつ": "우울", "우울증": "우울",
    # 지능
    "지능": "지능", "intelligence": "지능", "知能": "지능",
    # 겸손
    "겸손": "겸손", "humility": "겸손", "謙虚": "겸손",
}


def normalize_quiz_json(quiz_json: dict) -> dict:
    """
    퀴즈 JSON의 필드 타입을 정리합니다.
    딕셔너리나 리스트가 문자열이어야 할 필드에 있으면 변환합니다.
    """
    # detailed_analysis_comment가 딕셔너리면 문자열로 변환
    if "detailed_analysis_comment" in quiz_json:
        comment = quiz_json["detailed_analysis_comment"]
        if isinstance(comment, dict):
            # 딕셔너리인 경우 값들을 줄바꿈으로 연결
            lines = []
            for key, value in comment.items():
                if isinstance(value, str):
                    lines.append(f"{key}: {value}")
                else:
                    lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
            quiz_json["detailed_analysis_comment"] = "\n\n".join(lines)
        elif isinstance(comment, list):
            quiz_json["detailed_analysis_comment"] = "\n\n".join(str(item) for item in comment)
        elif not isinstance(comment, str):
            quiz_json["detailed_analysis_comment"] = str(comment)
    
    # ui_elements 정리
    if "ui_elements" in quiz_json:
        ui = quiz_json["ui_elements"]
        
        # top_title 정리
        if "top_title" in ui:
            title = ui["top_title"]
            if isinstance(title, dict):
                ui["top_title"] = json.dumps(title, ensure_ascii=False)
            elif isinstance(title, list):
                ui["top_title"] = "\n".join(str(item) for item in title)
            elif not isinstance(title, str):
                ui["top_title"] = str(title)
        
        # narration_script 정리
        if "narration_script" in ui:
            script = ui["narration_script"]
            if isinstance(script, dict):
                ui["narration_script"] = json.dumps(script, ensure_ascii=False)
            elif isinstance(script, list):
                ui["narration_script"] = " ".join(str(item) for item in script)
            elif not isinstance(script, str):
                ui["narration_script"] = str(script)
        
        # selection_buttons 정리 (리스트여야 함)
        if "selection_buttons" in ui:
            buttons = ui["selection_buttons"]
            if isinstance(buttons, str):
                # 문자열이면 쉼표로 분리
                ui["selection_buttons"] = [b.strip() for b in buttons.split(",")]
            elif isinstance(buttons, list):
                # 리스트의 각 항목이 문자열인지 확인
                ui["selection_buttons"] = [str(b) if not isinstance(b, str) else b for b in buttons]
            elif isinstance(buttons, dict):
                ui["selection_buttons"] = list(buttons.values())
            else:
                ui["selection_buttons"] = [str(buttons)]
    
    # image_generation 정리
    if "image_generation" in quiz_json:
        img = quiz_json["image_generation"]
        if "prompt" in img:
            prompt = img["prompt"]
            if not isinstance(prompt, str):
                img["prompt"] = str(prompt)
    
    return quiz_json


def get_template_list() -> str:
    """사용 가능한 템플릿 목록 반환"""
    lines = ["📋 사용 가능한 퀴즈 유형:"]
    for key, template in QUIZ_TEMPLATES.items():
        lines.append(f"  • {key}: {template['name']} - {template['description']}")
    return "\n".join(lines)


def resolve_template(keyword: str) -> Optional[str]:
    """키워드를 템플릿 키로 변환"""
    keyword_lower = keyword.lower().strip()
    
    # 직접 매칭
    if keyword_lower in QUIZ_TEMPLATES:
        return keyword_lower
    
    # 별칭 매칭
    for alias, template_key in TEMPLATE_ALIASES.items():
        if alias.lower() == keyword_lower:
            return template_key
    
    # 부분 매칭
    for key in QUIZ_TEMPLATES.keys():
        if keyword_lower in key.lower() or key.lower() in keyword_lower:
            return key
    
    return None


def generate_quiz_json(template_key: str, custom_theme: Optional[str] = None) -> dict:
    """
    Gemini API를 사용하여 퀴즈 JSON 생성
    
    Args:
        template_key: 템플릿 키 (치매, IQ, 관찰력 등)
        custom_theme: 사용자 지정 테마 (None이면 랜덤)
    
    Returns:
        생성된 퀴즈 JSON dict
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError("google-genai 패키지가 필요합니다: pip install google-genai")
    
    # 템플릿 확인
    resolved_key = resolve_template(template_key)
    if not resolved_key:
        raise ValueError(f"알 수 없는 템플릿: {template_key}\n{get_template_list()}")
    
    template = QUIZ_TEMPLATES[resolved_key]
    
    # API 키 로드
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
    
    print(f"🎲 {template['name']} 퀴즈 JSON 생성 중...")
    
    client = genai.Client(api_key=api_key)
    
    # 사용자 요청 구성
    user_request = template["prompt_template"]
    if custom_theme:
        user_request += f"\n\n사용자 지정 테마: {custom_theme}"
    else:
        user_request += "\n\n테마는 창의적으로 랜덤 선택해주세요."
    
    user_request += "\n\n**중요: 반드시 JSON만 출력하세요. 다른 텍스트 없이 순수 JSON만 반환해주세요.**"
    
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=user_request),
            ],
        ),
    ]
    
    tools = [
        types.Tool(googleSearch=types.GoogleSearch()),
    ]
    
    generate_content_config = types.GenerateContentConfig(

        tools=tools,
    )
    
    # API 호출
    response_text = ""
    for chunk in client.models.generate_content_stream(
        model="gemini-flash-latest",
        contents=contents,
        config=generate_content_config,
    ):
        if chunk.text:
            response_text += chunk.text
    
    # JSON 파싱
    try:
        # JSON 블록 추출 (```json ... ``` 형식인 경우)
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 순수 JSON인 경우
            json_str = response_text.strip()
            # { 로 시작하는 부분 찾기
            start_idx = json_str.find('{')
            end_idx = json_str.rfind('}')
            if start_idx != -1 and end_idx != -1:
                json_str = json_str[start_idx:end_idx+1]
        
        quiz_json = json.loads(json_str)
        
        # 필수 필드 검증
        required_fields = ["quiz_metadata", "image_generation", "ui_elements"]
        for field in required_fields:
            if field not in quiz_json:
                raise ValueError(f"필수 필드 누락: {field}")
        
        # 필드 타입 정리 (딕셔너리 -> 문자열 변환)
        quiz_json = normalize_quiz_json(quiz_json)
        
        theme = quiz_json.get("quiz_metadata", {}).get("theme", "Unknown")
        quiz_type = quiz_json.get("quiz_metadata", {}).get("quiz_type", resolved_key)
        target_n = quiz_json.get("quiz_metadata", {}).get("target_answer_n", 0)
        
        print(f"   ✅ 퀴즈 생성 완료!")
        print(f"   📌 유형: {template['name']}")
        print(f"   📌 테마: {theme}")
        print(f"   🎯 정답: {target_n}")
        
        return quiz_json
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
        print(f"응답 내용: {response_text[:500]}...")
        raise


def save_quiz_json(quiz_json: dict, output_path: str = None) -> str:
    """
    생성된 퀴즈 JSON을 파일로 저장
    
    Args:
        quiz_json: 퀴즈 JSON dict
        output_path: 저장 경로 (None이면 자동 생성)
    
    Returns:
        저장된 파일 경로
    """
    if output_path is None:
        theme = quiz_json.get("quiz_metadata", {}).get("theme", "quiz")
        safe_theme = re.sub(r'[^\w\s-]', '', theme).replace(' ', '_').lower()[:30]
        output_dir = Path(__file__).parent.parent / "resources" / "generated_quizzes"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 고유한 파일명 생성
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"{safe_theme}_{timestamp}.json"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(quiz_json, f, ensure_ascii=False, indent=2)
    
    print(f"   💾 JSON 저장: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="퀴즈 JSON 자동 생성기 v2")
    parser.add_argument("template", nargs="?", default="치매", 
                       help="퀴즈 템플릿 (치매/IQ/관찰력/노안/성격/우울/지능/겸손)")
    parser.add_argument("--theme", "-t", help="퀴즈 테마 (지정하지 않으면 랜덤)")
    parser.add_argument("--output", "-o", help="출력 JSON 파일 경로")
    parser.add_argument("--list", "-l", action="store_true", help="사용 가능한 템플릿 목록 표시")
    parser.add_argument("--print-only", action="store_true", help="파일 저장 없이 출력만")
    
    args = parser.parse_args()
    
    if args.list:
        print(get_template_list())
        exit(0)
    
    try:
        quiz_json = generate_quiz_json(args.template, args.theme)
        
        if args.print_only:
            print(json.dumps(quiz_json, ensure_ascii=False, indent=2))
        else:
            save_quiz_json(quiz_json, args.output)
            
    except Exception as e:
        print(f"❌ 오류: {e}")
        exit(1)
