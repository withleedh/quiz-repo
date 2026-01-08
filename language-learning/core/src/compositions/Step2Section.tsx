/**
 * Step2Section - 자막 보며 듣기
 * 
 * 화면 구성:
 * - 배경 이미지 + 어두운 오버레이 (50%)
 * - 영어 자막만 중앙에 표시
 * - 한글 자막 없음
 */

import React from 'react';
import { AbsoluteFill } from 'remotion';
import { Sentence } from '../types/config';

export interface Step2SectionProps {
  sentence: Sentence;
  stepNumber: number;
  totalSteps: number;
  backgroundImage?: string;
  overlayOpacity?: number;
}

export const Step2Section: React.FC<Step2SectionProps> = ({
  sentence,
  stepNumber,
  totalSteps,
  backgroundImage,
  overlayOpacity = 0.5,
}) => {
  return (
    <AbsoluteFill
      style={{
        backgroundImage: backgroundImage ? `url(${backgroundImage})` : undefined,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundColor: backgroundImage ? undefined : '#1a1a2e',
      }}
    >
      {/* 어두운 오버레이 */}
      <div
        data-testid="dark-overlay"
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: `rgba(0, 0, 0, ${overlayOpacity})`,
        }}
      />

      {/* Step 표시기 */}
      <div
        style={{
          position: 'absolute',
          top: 40,
          left: 40,
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          padding: '12px 24px',
          borderRadius: 8,
          zIndex: 1,
        }}
      >
        <div
          style={{
            color: '#f0a500',
            fontSize: 24,
            fontWeight: 700,
          }}
        >
          Step {stepNumber}
        </div>
        <div
          style={{
            color: '#ffffff',
            fontSize: 16,
          }}
        >
          자막 보며 듣기
        </div>
      </div>

      {/* 영어 자막 (중앙) */}
      <div
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          zIndex: 1,
          textAlign: 'center',
          maxWidth: '80%',
        }}
      >
        <div
          data-testid="english-subtitle"
          style={{
            color: '#ffffff',
            fontSize: 48,
            fontWeight: 600,
            textShadow: '2px 2px 8px rgba(0, 0, 0, 0.8)',
            fontFamily: 'Georgia, serif',
            lineHeight: 1.4,
          }}
        >
          {sentence.target}
        </div>
      </div>

      {/* 스텝 카운터 */}
      <div
        style={{
          position: 'absolute',
          top: 40,
          right: 40,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          padding: '8px 16px',
          borderRadius: 8,
          color: '#888',
          fontSize: 14,
          zIndex: 1,
        }}
      >
        {stepNumber} / {totalSteps}
      </div>
    </AbsoluteFill>
  );
};
