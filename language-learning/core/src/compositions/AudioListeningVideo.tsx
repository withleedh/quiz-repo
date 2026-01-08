/**
 * AudioListeningVideo - 오디오 포함 전체 영상 컴포지션
 * 
 * 오디오 파일을 기반으로 정확한 타이밍에 맞춰 영상 재생
 */

import React from 'react';
import { Sequence, AbsoluteFill, Audio, staticFile, useVideoConfig } from 'remotion';
import { Script, ColorConfig, ChannelConfig } from '../types/config';
import { IntroSection, StepDescription } from './IntroSection';
import { Step1Section } from './Step1Section';
import { Step2Section } from './Step2Section';
import { Step3Section } from './Step3Section';

export interface AudioListeningVideoProps {
  script: Script;
  config: ChannelConfig;
  audioBasePath: string;  // 오디오 파일 기본 경로
  audioDurations?: number[];  // 각 문장별 오디오 길이 (초)
}

// 4단계 설명
const DEFAULT_STEPS: StepDescription[] = [
  { step: 1, title: '자막 없이 듣기', description: '자막 없이 전체 내용을 들어보세요' },
  { step: 2, title: '자막 보며 듣기', description: '자막과 함께 들으며 내용을 파악하세요' },
  { step: 3, title: '문장별 반복 듣기', description: '문장을 10번씩 반복해서 익히세요' },
  { step: 4, title: '다시 자막 없이 듣기', description: '얼마나 잘 들리는지 확인하세요' },
];

// 타이밍 설정
const TIMINGS = {
  INTRO_FRAMES: 300,           // 10초 @ 30fps
  DEFAULT_SENTENCE_SECONDS: 5, // 기본 문장 길이 (5초)
  REPEAT_COUNT: 10,            // 10회 반복
  OUTRO_FRAMES: 300,           // 10초
  FPS: 30,
};

export const AudioListeningVideo: React.FC<AudioListeningVideoProps> = ({
  script,
  config,
  audioBasePath,
  audioDurations,
}) => {
  const { fps } = useVideoConfig();
  
  const sentenceCount = script.sentences.length;
  const repeatCount = config.content.repeatCount || TIMINGS.REPEAT_COUNT;
  
  // 각 문장별 프레임 수 계산 (오디오 길이 기반)
  const sentenceFrames = script.sentences.map((_, index) => {
    const duration = audioDurations?.[index] ?? TIMINGS.DEFAULT_SENTENCE_SECONDS;
    return Math.ceil(duration * fps);
  });
  
  // 전체 스크립트 프레임 수
  const fullScriptFrames = sentenceFrames.reduce((a, b) => a + b, 0);
  
  // Step 3의 각 문장 10회 반복 프레임
  const step3SentenceFramesArray = sentenceFrames.map(f => f * repeatCount);
  const step3TotalFrames = step3SentenceFramesArray.reduce((a, b) => a + b, 0);

  // 각 섹션 시작 프레임
  let currentFrame = 0;
  
  const introStart = currentFrame;
  currentFrame += TIMINGS.INTRO_FRAMES;
  
  const step1Start = currentFrame;
  currentFrame += fullScriptFrames;
  
  const step2Start = currentFrame;
  currentFrame += fullScriptFrames;
  
  const step3Start = currentFrame;
  currentFrame += step3TotalFrames;
  
  const step4Start = currentFrame;
  currentFrame += fullScriptFrames;
  
  const outroStart = currentFrame;

  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      {/* ===== 인트로 ===== */}
      <Sequence from={introStart} durationInFrames={TIMINGS.INTRO_FRAMES}>
        <IntroSection 
          channelName={config.meta.name}
          steps={DEFAULT_STEPS}
        />
      </Sequence>

      {/* ===== Step 1: 자막 없이 듣기 + 전체 오디오 ===== */}
      <Sequence from={step1Start} durationInFrames={fullScriptFrames}>
        <Step1Section 
          stepNumber={1}
          totalSteps={4}
        />
        <Audio src={staticFile(`${audioBasePath}/full_script.mp3`)} />
      </Sequence>

      {/* ===== Step 2: 자막 보며 듣기 + 전체 오디오 ===== */}
      <Sequence from={step2Start} durationInFrames={fullScriptFrames}>
        {/* 전체 오디오 */}
        <Audio src={staticFile(`${audioBasePath}/full_script.mp3`)} />
        
        {/* 문장별로 자막 표시 */}
        {script.sentences.map((sentence, index) => {
          // 누적 오프셋 계산
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

      {/* ===== Step 3: 문장별 10회 반복 ===== */}
      <Sequence from={step3Start} durationInFrames={step3TotalFrames}>
        {script.sentences.map((sentence, sentenceIndex) => {
          // 이전 문장들의 누적 프레임
          const sentenceOffset = step3SentenceFramesArray.slice(0, sentenceIndex).reduce((a, b) => a + b, 0);
          const paddedId = String(sentence.id).padStart(2, '0');
          const singleSentenceFrame = sentenceFrames[sentenceIndex];
          const repeatTotalFrames = step3SentenceFramesArray[sentenceIndex];
          
          return (
            <Sequence 
              key={sentence.id} 
              from={sentenceOffset} 
              durationInFrames={repeatTotalFrames}
            >
              {/* 10회 반복 오디오 */}
              <Audio src={staticFile(`${audioBasePath}/sentence_${paddedId}_x10.mp3`)} />
              
              {/* 10회 반복 화면 - 각 반복마다 카운터 업데이트 */}
              {Array.from({ length: repeatCount }).map((_, repeatIdx) => (
                <Sequence 
                  key={repeatIdx}
                  from={repeatIdx * singleSentenceFrame}
                  durationInFrames={singleSentenceFrame}
                >
                  <Step3Section
                    sentence={sentence}
                    colors={config.colors}
                    repeatIndex={repeatIdx + 1}
                    totalRepeats={repeatCount}
                  />
                </Sequence>
              ))}
            </Sequence>
          );
        })}
      </Sequence>

      {/* ===== Step 4: 다시 자막 없이 듣기 ===== */}
      <Sequence from={step4Start} durationInFrames={fullScriptFrames}>
        <Step1Section 
          stepNumber={4}
          totalSteps={4}
          instruction="다시 자막 없이 듣기"
        />
        <Audio src={staticFile(`${audioBasePath}/full_script.mp3`)} />
      </Sequence>

      {/* ===== 아웃트로 ===== */}
      <Sequence from={outroStart} durationInFrames={TIMINGS.OUTRO_FRAMES}>
        <OutroSection 
          channelName={config.meta.name}
          sentenceCount={sentenceCount}
        />
      </Sequence>
    </AbsoluteFill>
  );
};

// 아웃트로 컴포넌트
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

// 전체 영상 길이 계산
export function calculateAudioVideoDuration(
  sentenceCount: number,
  repeatCount: number = 10,
  audioDurations?: number[]  // 각 문장별 초 단위 길이
): number {
  const fps = TIMINGS.FPS;
  
  // 오디오 길이 기반 또는 기본값
  const sentenceFrames = audioDurations
    ? audioDurations.map(d => Math.ceil(d * fps))
    : Array(sentenceCount).fill(TIMINGS.DEFAULT_SENTENCE_SECONDS * fps);
  
  const fullScriptFrames = sentenceFrames.reduce((a, b) => a + b, 0);
  const step3TotalFrames = sentenceFrames.reduce((a, f) => a + f * repeatCount, 0);

  return (
    TIMINGS.INTRO_FRAMES +
    fullScriptFrames * 3 + // Step 1, 2, 4
    step3TotalFrames +     // Step 3
    TIMINGS.OUTRO_FRAMES
  );
}
