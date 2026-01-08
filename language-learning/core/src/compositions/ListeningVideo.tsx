/**
 * ListeningVideo - 전체 영상 컴포지션
 * 
 * 4단계 학습 영상 구조:
 * 1. 인트로 (채널로고 + 4단계 설명) - 10초
 * 2. Step 1: 자막 없이 듣기 - 대본 길이
 * 3. Step 2: 자막 보며 듣기 - 대본 길이
 * 4. Step 3: 문장별 10회 반복 - 문장수 x 반복횟수 x 문장길이
 * 5. Step 4: 다시 자막 없이 듣기 - 대본 길이
 * 6. 아웃트로 - 10초
 */

import React from 'react';
import { Sequence, AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';
import { Script, ColorConfig, ChannelConfig } from '../types/config';
import { IntroSection, StepDescription } from './IntroSection';
import { Step1Section } from './Step1Section';
import { Step2Section } from './Step2Section';
import { Step3Section } from './Step3Section';

export interface ListeningVideoProps {
  script: Script;
  config: ChannelConfig;
  audioDurations?: {
    fullScript: number;      // 전체 대본 오디오 길이 (프레임)
    sentences: number[];     // 각 문장별 오디오 길이 (프레임)
  };
}

// 기본 타이밍 설정 (오디오 없을 때 폴백)
const DEFAULT_TIMINGS = {
  INTRO_FRAMES: 300,           // 10초 @ 30fps
  SENTENCE_FRAMES: 90,         // 3초 (평균 문장 길이)
  REPEAT_GAP_FRAMES: 15,       // 0.5초 간격
  OUTRO_FRAMES: 300,           // 10초
};

// 4단계 설명
const DEFAULT_STEPS: StepDescription[] = [
  { step: 1, title: '자막 없이 듣기', description: '자막 없이 전체 내용을 들어보세요' },
  { step: 2, title: '자막 보며 듣기', description: '자막과 함께 들으며 내용을 파악하세요' },
  { step: 3, title: '문장별 반복 듣기', description: '문장을 10번씩 반복해서 익히세요' },
  { step: 4, title: '다시 자막 없이 듣기', description: '얼마나 잘 들리는지 확인하세요' },
];

export const ListeningVideo: React.FC<ListeningVideoProps> = ({
  script,
  config,
  audioDurations,
}) => {
  const { fps } = useVideoConfig();
  
  // 타이밍 계산
  const sentenceCount = script.sentences.length;
  const repeatCount = config.content.repeatCount;
  
  // 각 문장별 프레임 수 (오디오 기반 또는 기본값)
  const sentenceFrames = audioDurations?.sentences || 
    script.sentences.map(() => DEFAULT_TIMINGS.SENTENCE_FRAMES);
  
  // 전체 대본 프레임 수
  const fullScriptFrames = audioDurations?.fullScript || 
    sentenceFrames.reduce((a, b) => a + b, 0);
  
  // Step 3의 전체 프레임 수 (문장당 반복 * 반복횟수 + 간격)
  const step3Frames = sentenceFrames.reduce(
    (total, frames) => total + (frames * repeatCount) + (repeatCount * DEFAULT_TIMINGS.REPEAT_GAP_FRAMES),
    0
  );

  // 각 섹션 시작 프레임 계산
  let currentFrame = 0;
  
  const introStart = currentFrame;
  currentFrame += DEFAULT_TIMINGS.INTRO_FRAMES;
  
  const step1Start = currentFrame;
  currentFrame += fullScriptFrames;
  
  const step2Start = currentFrame;
  currentFrame += fullScriptFrames;
  
  const step3Start = currentFrame;
  currentFrame += step3Frames;
  
  const step4Start = currentFrame;
  currentFrame += fullScriptFrames;
  
  const outroStart = currentFrame;
  
  // Step 3 내의 문장별 시작 프레임 계산
  const step3SentenceStarts: number[] = [];
  let step3CurrentFrame = 0;
  for (let i = 0; i < sentenceCount; i++) {
    step3SentenceStarts.push(step3CurrentFrame);
    step3CurrentFrame += sentenceFrames[i] * repeatCount + (repeatCount * DEFAULT_TIMINGS.REPEAT_GAP_FRAMES);
  }

  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      {/* 인트로 */}
      <Sequence from={introStart} durationInFrames={DEFAULT_TIMINGS.INTRO_FRAMES}>
        <IntroSection 
          channelName={config.meta.name}
          steps={DEFAULT_STEPS}
        />
      </Sequence>

      {/* Step 1: 자막 없이 듣기 */}
      <Sequence from={step1Start} durationInFrames={fullScriptFrames}>
        <Step1Section 
          stepNumber={1}
          totalSteps={4}
        />
      </Sequence>

      {/* Step 2: 자막 보며 듣기 - 문장별로 표시 */}
      <Sequence from={step2Start} durationInFrames={fullScriptFrames}>
        {script.sentences.map((sentence, index) => {
          const sentenceStart = sentenceFrames.slice(0, index).reduce((a, b) => a + b, 0);
          return (
            <Sequence key={sentence.id} from={sentenceStart} durationInFrames={sentenceFrames[index]}>
              <Step2Section 
                sentence={sentence}
                stepNumber={2}
                totalSteps={4}
              />
            </Sequence>
          );
        })}
      </Sequence>

      {/* Step 3: 문장별 10회 반복 */}
      <Sequence from={step3Start} durationInFrames={step3Frames}>
        {script.sentences.map((sentence, sentenceIndex) => {
          const singleSentenceFrames = sentenceFrames[sentenceIndex];
          const totalRepeatFrames = singleSentenceFrames * repeatCount + (repeatCount * DEFAULT_TIMINGS.REPEAT_GAP_FRAMES);
          
          return (
            <Sequence 
              key={sentence.id} 
              from={step3SentenceStarts[sentenceIndex]} 
              durationInFrames={totalRepeatFrames}
            >
              {/* 반복 인덱스는 Remotion 내부에서 계산 */}
              <Step3SentenceRepeater
                sentence={sentence}
                colors={config.colors}
                repeatCount={repeatCount}
                singleFrames={singleSentenceFrames}
              />
            </Sequence>
          );
        })}
      </Sequence>

      {/* Step 4: 다시 자막 없이 듣기 */}
      <Sequence from={step4Start} durationInFrames={fullScriptFrames}>
        <Step1Section 
          stepNumber={4}
          totalSteps={4}
          instruction="다시 자막 없이 듣기"
        />
      </Sequence>

      {/* 아웃트로 */}
      <Sequence from={outroStart} durationInFrames={DEFAULT_TIMINGS.OUTRO_FRAMES}>
        <OutroSection 
          channelName={config.meta.name}
          sentenceCount={sentenceCount}
        />
      </Sequence>
    </AbsoluteFill>
  );
};

// Step 3 문장 반복 헬퍼 컴포넌트
interface Step3SentenceRepeaterProps {
  sentence: Script['sentences'][0];
  colors: ColorConfig;
  repeatCount: number;
  singleFrames: number;
}

const Step3SentenceRepeater: React.FC<Step3SentenceRepeaterProps> = ({
  sentence,
  colors,
  repeatCount,
  singleFrames,
}) => {
  const frame = useCurrentFrame();
  const gapFrames = DEFAULT_TIMINGS.REPEAT_GAP_FRAMES;
  const totalPerRepeat = singleFrames + gapFrames;
  const currentRepeat = Math.floor(frame / totalPerRepeat) + 1;

  return (
    <Step3Section
      sentence={sentence}
      colors={colors}
      repeatIndex={Math.min(currentRepeat, repeatCount)}
      totalRepeats={repeatCount}
    />
  );
};

// 간단한 아웃트로 컴포넌트
interface OutroSectionProps {
  channelName: string;
  sentenceCount: number;
}

const OutroSection: React.FC<OutroSectionProps> = ({
  channelName,
  sentenceCount,
}) => {
  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(135deg, #0f0e17 0%, #1a1a2e 100%)',
        justifyContent: 'center',
        alignItems: 'center',
        display: 'flex',
        flexDirection: 'column',
        gap: 40,
      }}
    >
      <div style={{ fontSize: 64, color: '#4ecdc4' }}>
        오늘의 학습 완료! 🎊
      </div>
      <div style={{ fontSize: 32, color: '#ffffff' }}>
        {sentenceCount}개 문장을 반복 청취했습니다
      </div>
      <div style={{ fontSize: 24, color: '#888888', marginTop: 40 }}>
        🔔 {channelName} 구독하기
      </div>
    </AbsoluteFill>
  );
};

// 전체 영상 길이 계산 함수 (Root.tsx에서 사용)
export function calculateTotalDuration(
  sentenceCount: number,
  repeatCount: number,
  audioDurations?: { fullScript: number; sentences: number[] }
): number {
  const fullScriptFrames = audioDurations?.fullScript || (sentenceCount * DEFAULT_TIMINGS.SENTENCE_FRAMES);
  const step3Frames = audioDurations?.sentences 
    ? audioDurations.sentences.reduce(
        (total, frames) => total + (frames * repeatCount) + (repeatCount * DEFAULT_TIMINGS.REPEAT_GAP_FRAMES),
        0
      )
    : sentenceCount * (DEFAULT_TIMINGS.SENTENCE_FRAMES * repeatCount + repeatCount * DEFAULT_TIMINGS.REPEAT_GAP_FRAMES);

  return (
    DEFAULT_TIMINGS.INTRO_FRAMES +
    fullScriptFrames * 3 + // Step 1, 2, 4
    step3Frames +
    DEFAULT_TIMINGS.OUTRO_FRAMES
  );
}
