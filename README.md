# 🎬 심리/IQ 퀴즈 영상 자동 생성 시스템

Gemini API를 사용하여 **완전 자동으로** 다양한 유형의 심리 테스트/IQ 퀴즈 영상을 생성합니다.

## 🎯 지원 퀴즈 유형

| 유형 | 설명 | 예시 제목 |
|------|------|----------|
| 치매 | 그림 속 숨겨진 얼굴 찾기 | 認知症が始まった人は違って見える絵 |
| IQ | 숫자가 몇 개 보이는지 테스트 | IQが130以上ならすべての数字が見える |
| 관찰력 | 그림 속 숨겨진 숫자 찾기 | 観察力が優れていれば数字が9個すべて見える |
| 노안 | 착시 이미지에서 숫자 찾기 | 老眼が始まっている人は数字が3つ以下に見えます |
| 성격 | 동물 개수로 성격 파악 | 繊細な性格の持ち主は違って見える絵 |
| 우울 | 이중 이미지 (개구리/말 등) | 現在、うつ状態の人には馬が見える絵 |
| 지능 | 고지능자만 보이는 숫자 | 知能が高い人だけに見える絵 |
| 겸손 | 무엇이 먼저 보이는지로 성격 파악 | 謙虚な人は違って見える絵 |

## 🚀 빠른 시작

### 텔레그램 봇으로 사용 (권장)

```bash
cd scripts
python3 telegram_bot.py
```

텔레그램에서 봇에게 메시지를 보내면 즉시 영상 생성:
- `치매` → 치매 예방 테스트 영상 생성
- `IQ` → IQ 테스트 영상 생성
- `랜덤` → 랜덤 유형 영상 생성
- `도움말` → 사용 가능한 유형 목록

### CLI로 사용

```bash
cd scripts

# 치매 테스트 (기본)
python3 quiz_pipeline.py --auto

# 특정 유형 지정
python3 quiz_json_generator.py IQ
python3 quiz_json_generator.py 관찰력

# 템플릿 목록 보기
python3 quiz_json_generator.py --list
```

## 📂 폴더 구조

```
japan/
├── .env                      # API 키 설정
├── README.md                 # 이 문서
├── scripts/                  # 핵심 스크립트
│   ├── telegram_bot.py       # 텔레그램 봇 (메인)
│   ├── quiz_pipeline.py      # 영상 생성 파이프라인
│   ├── quiz_json_generator.py # JSON 자동 생성 (템플릿)
│   ├── image_generator.py    # 이미지 생성
│   ├── quiz_generator.py     # 영상 생성
│   ├── api.py                # TTS 생성
│   └── quiz_editor_gui.py    # GUI 에디터
├── resources/
│   ├── quiz_config.json      # 기본 설정
│   └── sounds/               # 효과음
│       ├── intro_sound.wav
│       └── popup_sound.wav
├── output/                   # 실행 결과 (타임스탬프 폴더)
│   └── YYYYMMDD_HHMMSS_테마/
│       ├── quiz_video.mp4    # 최종 영상
│       ├── image.png         # 생성된 이미지
│       ├── narration.wav     # TTS 음성
│       ├── narration.srt     # 자막
│       ├── quiz_config.json  # 퀴즈 설정
│       └── analysis.txt      # 해석 텍스트
└── backup/                   # 백업 파일
```

## 🔧 설정

### 1. 환경 변수 설정 (.env)

```env
GEMINI_API_KEY=your_gemini_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

### 2. VOICEVOX 실행 (TTS용)

TTS 생성을 위해 VOICEVOX를 실행해야 합니다.
- 다운로드: https://voicevox.hiroshiba.jp/
- 실행 후 `http://localhost:50021`에서 API 사용 가능

## 🤖 텔레그램 봇

### 설정

1. **텔레그램 봇 토큰** ([@BotFather](https://t.me/BotFather)에서 생성)
2. **.env 파일**에 토큰 추가:
```env
TELEGRAM_BOT_TOKEN=your_telegram_token
```

### 실행

```bash
cd scripts
python telegram_bot.py
```

### 명령어

| 명령어 | 설명 |
|--------|------|
| 치매 | 치매 예방 테스트 영상 생성 |
| IQ | IQ 테스트 영상 생성 |
| 관찰력 | 관찰력 테스트 영상 생성 |
| 노안 | 노안 테스트 영상 생성 |
| 성격 | 성격 테스트 영상 생성 |
| 우울 | 우울증 테스트 영상 생성 |
| 지능 | 지능 테스트 영상 생성 |
| 겸손 | 겸손함 테스트 영상 생성 |
| 랜덤 | 랜덤 유형 영상 생성 |
| 도움말 | 사용 가능한 유형 목록 |

### 동작 방식

1. 퀴즈 유형 메시지 수신
2. Gemini API로 퀴즈 JSON 생성
3. Gemini API로 착시 이미지 생성
4. VOICEVOX로 TTS 나레이션 생성
5. MoviePy로 최종 영상 생성
6. 텔레그램으로 영상 + 제목 + 해설 전송

## 🎯 파이프라인 흐름

```
1️⃣ 템플릿 선택 (치매/IQ/관찰력 등)
        ↓
2️⃣ Gemini API → 퀴즈 JSON 자동 생성
   (테마, 정답, 선택지, 해석)
        ↓
3️⃣ Gemini API → 착시 이미지 생성
        ↓
4️⃣ VOICEVOX → TTS 나레이션 생성
        ↓
5️⃣ MoviePy → 최종 영상 생성
   (효과음, 페이드인 애니메이션 포함)
        ↓
6️⃣ 텔레그램으로 전송 (영상 + 제목 + 해설)
```

## 📦 필요 패키지

```bash
pip install google-genai python-dotenv moviepy pillow requests python-telegram-bot
```

## 🎨 커스터마이징

### 효과음 변경

`resources/sounds/` 폴더의 파일을 교체하거나 `quiz_config.json`에서 경로 지정

### 화면 레이아웃

`quiz_editor_gui.py`를 실행하여 GUI로 조정 가능:
- 타이틀 위치/크기/색상
- 이미지 위치/크기
- 버튼 위치/크기/색상
- 숫자 배지 위치/크기
- 반짝이 효과

### 새 템플릿 추가

`quiz_json_generator.py`의 `QUIZ_TEMPLATES` 딕셔너리에 새 템플릿 추가

---

## 📝 라이선스

MIT License


걍 voicevox다운받아서 실행해놓고 python 3.11.7 다운받으셈
requirements 다운받고 .env랑 구글 oauth json파일 다운받아서 script폴더에 client_secrets.json 이름으로 저장하면 끝

GEMINI_API_KEY=잼민이
TELEGRAM_BOT_TOKEN=텔레

봇 시작하기전에 voicevox 실행해놓으삼