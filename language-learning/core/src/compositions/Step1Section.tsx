/**
 * Step1Section - 자막 없이 듣기
 * 
 * 화면 구성:
 * - 배경 이미지 전체 표시
 * - Step 표시기
 * - 자막 없음
 */

import React from 'react';
import { AbsoluteFill } from 'remotion';

export interface Step1SectionProps {
  stepNumber: number;
  totalSteps: number;
  backgroundImage?: string;
  instruction?: string;
}

export const Step1Section: React.FC<Step1SectionProps> = ({
  stepNumber,
  totalSteps,
  backgroundImage,
  instruction = '자막 없이 듣기',
}) => {
  return (
    <AbsoluteFill
      data-testid="background-container"
      style={{
        backgroundImage: backgroundImage ? `url(${backgroundImage})` : undefined,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundColor: backgroundImage ? undefined : '#1a1a2e',
      }}
    >
      {/* Step 표시기 */}
      <div
        style={{
          position: 'absolute',
          top: 40,
          left: 40,
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          padding: '12px 24px',
          borderRadius: 8,
          display: 'flex',
          flexDirection: 'column',
          gap: 4,
        }}
      >
        <div
          style={{
            color: '#4ecdc4',
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
          {instruction}
        </div>
      </div>

      {/* 총 스텝 표시 */}
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
        }}
      >
        {stepNumber} / {totalSteps}
      </div>
    </AbsoluteFill>
  );
};
