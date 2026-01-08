/**
 * Step3Section - 문장별 10회 반복 섹션
 * 
 * 화면 구성:
 * - 상단 40%: 배경 이미지
 * - 하단 60%: 검은 배경 + 자막
 *   - 영어 문장 (남:파랑 / 여:핑크)
 *   - 한글 해석 (흰색)
 *   - 단어별 뜻 (회색)
 *   - 반복 카운터
 */

import React from 'react';
import { AbsoluteFill } from 'remotion';
import { Sentence, ColorConfig } from '../types/config';

export interface Step3SectionProps {
  sentence: Sentence;
  colors: ColorConfig;
  repeatIndex: number;
  totalRepeats: number;
  backgroundImage?: string;
  imageRatio?: number;
}

export const Step3Section: React.FC<Step3SectionProps> = ({
  sentence,
  colors,
  repeatIndex,
  totalRepeats,
  backgroundImage,
  imageRatio = 0.4,
}) => {
  // 화자에 따른 색상 선택
  const textColor = sentence.speaker === 'M' ? colors.maleText : colors.femaleText;
  
  // 단어 뜻 문자열 생성
  const wordMeaningsText = sentence.words
    .map((w: { word: string; meaning: string }) => `${w.word}: ${w.meaning}`)
    .join(' / ');

  return (
    <AbsoluteFill style={{ backgroundColor: colors.background }}>
      {/* 상단: 배경 이미지 영역 */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: `${imageRatio * 100}%`,
          backgroundImage: backgroundImage ? `url(${backgroundImage})` : undefined,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundColor: backgroundImage ? undefined : '#1a1a2e',
        }}
      />

      {/* 하단: 자막 영역 */}
      <div
        style={{
          position: 'absolute',
          top: `${imageRatio * 100}%`,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: colors.background,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          padding: '20px 60px',
          gap: 20,
        }}
      >
        {/* 영어 문장 */}
        <div
          data-testid="target-text"
          style={{
            color: textColor,
            fontSize: 48,
            fontWeight: 600,
            textAlign: 'center',
            lineHeight: 1.4,
            fontFamily: 'Georgia, serif',
          }}
        >
          {sentence.target}
        </div>

        {/* 한글 해석 */}
        <div
          data-testid="native-text"
          style={{
            color: colors.nativeText,
            fontSize: 32,
            textAlign: 'center',
            lineHeight: 1.4,
            fontFamily: 'sans-serif',
          }}
        >
          {sentence.native}
        </div>

        {/* 구분선 */}
        <div
          style={{
            width: '80%',
            height: 1,
            backgroundColor: '#333',
            margin: '10px 0',
          }}
        />

        {/* 단어별 뜻 */}
        <div
          data-testid="word-meanings"
          style={{
            color: colors.wordMeaning,
            fontSize: 20,
            textAlign: 'center',
            fontFamily: 'sans-serif',
          }}
        >
          {wordMeaningsText}
        </div>

        {/* 반복 카운터 */}
        <div
          data-testid="repeat-counter"
          style={{
            position: 'absolute',
            bottom: 20,
            right: 40,
            color: colors.wordMeaning,
            fontSize: 18,
          }}
        >
          {repeatIndex} / {totalRepeats}
        </div>
      </div>
    </AbsoluteFill>
  );
};
