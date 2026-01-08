/**
 * IntroSection - 인트로 섹션
 * 
 * 화면 구성:
 * - 채널 로고/이름
 * - 4단계 학습 설명
 */

import React from 'react';
import { AbsoluteFill } from 'remotion';

export interface StepDescription {
  step: number;
  title: string;
  description: string;
  color?: string;
}

export interface IntroSectionProps {
  channelName: string;
  steps: StepDescription[];
  logo?: string;
}

// 스텝별 색상
const STEP_COLORS = ['#e74c3c', '#f0a500', '#3498db', '#9b59b6'];

export const IntroSection: React.FC<IntroSectionProps> = ({
  channelName,
  steps,
  logo,
}) => {
  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 60,
        gap: 40,
      }}
    >
      {/* 채널 로고/이름 */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 20,
          marginBottom: 20,
        }}
      >
        {logo && (
          <img
            src={logo}
            alt="Channel Logo"
            style={{ width: 80, height: 80 }}
          />
        )}
        <div
          style={{
            fontSize: 48,
            fontWeight: 700,
            color: '#ffffff',
            fontFamily: 'sans-serif',
          }}
        >
          🎧 {channelName}
        </div>
      </div>

      {/* 4단계 설명 */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 20,
          width: '100%',
          maxWidth: 800,
        }}
      >
        {steps.map((step, index) => (
          <div
            key={step.step}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 24,
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              borderRadius: 12,
              padding: '16px 24px',
              borderLeft: `4px solid ${step.color || STEP_COLORS[index]}`,
            }}
          >
            {/* 스텝 번호 */}
            <div
              style={{
                width: 48,
                height: 48,
                backgroundColor: step.color || STEP_COLORS[index],
                borderRadius: 8,
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                fontSize: 24,
                fontWeight: 700,
                color: '#ffffff',
              }}
            >
              {step.step}
            </div>

            {/* 스텝 내용 */}
            <div style={{ flex: 1 }}>
              <div
                style={{
                  fontSize: 24,
                  fontWeight: 600,
                  color: '#ffffff',
                  marginBottom: 4,
                }}
              >
                {step.title}
              </div>
              <div
                style={{
                  fontSize: 16,
                  color: '#aaaaaa',
                }}
              >
                {step.description}
              </div>
            </div>
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
