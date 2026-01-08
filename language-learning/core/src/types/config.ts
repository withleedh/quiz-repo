// 채널 설정 타입 정의

export interface ChannelMeta {
  name: string;                    // "귀가 뚫리는 영어"
  targetLanguage: string;          // "English"
  nativeLanguage: string;          // "Korean"
  youtubeChannelId?: string;       // YouTube 채널 ID
}

export interface ThemeConfig {
  logo: string;                    // 로고 이미지 경로
  introSound: string;              // 인트로 효과음 경로
  backgroundStyle: "illustration" | "photo" | "gradient";
  primaryColor: string;            // 남성 화자 / 주요 색상
  secondaryColor: string;          // 여성 화자 / 보조 색상
}

export interface ColorConfig {
  maleText: string;                // 남성 화자 텍스트 색상
  femaleText: string;              // 여성 화자 텍스트 색상
  nativeText: string;              // 모국어 텍스트 색상
  wordMeaning: string;             // 단어 뜻 텍스트 색상
  background: string;              // Step 3 하단 배경색
}

export interface LayoutConfig {
  step3ImageRatio: number;         // 이미지 영역 비율 (0~1)
  subtitlePosition: "center" | "bottom";
  speakerIndicator: "left" | "none";
}

export interface TTSConfig {
  provider: "openai" | "google" | "elevenlabs" | "edge-tts";
  maleVoice: string;               // 남성 음성 ID
  femaleVoice: string;             // 여성 음성 ID
  targetLanguageCode: string;      // "en-US", "ja-JP" 등
  speed?: number;                  // 재생 속도 (기본 1.0)
}

export interface ContentConfig {
  sentenceCount: number;           // 대화 문장 수 (기본 12)
  repeatCount: number;             // 반복 횟수 (기본 10)
  difficulty: "beginner" | "intermediate" | "advanced";
}

export interface ScheduleConfig {
  publishTime: string;             // "06:00"
  timezone: string;                // "Asia/Seoul"
}

export interface CategoryConfig {
  dayOfWeek: number;               // 0=일, 1=월, ..., 6=토
  name: string;                    // "일상 이야기"
  description: string;             // 카테고리 설명
  promptHint?: string;             // AI 프롬프트 힌트
}

export interface ChannelConfig {
  channelId: string;               // 고유 ID
  meta: ChannelMeta;
  theme: ThemeConfig;
  colors: ColorConfig;
  layout: LayoutConfig;
  tts: TTSConfig;
  content: ContentConfig;
  schedule: ScheduleConfig;
  categories?: CategoryConfig[];   // 요일별 카테고리 (선택)
}

// 대본 데이터 타입
export interface WordMeaning {
  word: string;
  meaning: string;
}

export interface Sentence {
  id: number;
  speaker: "M" | "F";
  target: string;                  // 학습 언어 문장
  native: string;                  // 모국어 해석
  words: WordMeaning[];
}

export interface Script {
  channelId: string;
  date: string;
  category: string;
  metadata: {
    topic: string;
    style: string;
    title: {
      target: string;
      native: string;
    };
  };
  sentences: Sentence[];
}
