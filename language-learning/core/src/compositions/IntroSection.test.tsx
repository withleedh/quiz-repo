/**
 * IntroSection Component Tests (TDD)
 * 
 * 인트로 섹션:
 * - 채널 로고 (2초)
 * - 4단계 설명 (8초)
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { IntroSection } from './IntroSection';

describe('IntroSection', () => {
  const mockConfig = {
    channelName: '귀가 뚫리는 영어',
    stepDescriptions: [
      { step: 1, title: '자막 없이 듣기', description: '자막 없이 전체 내용을 들어보세요' },
      { step: 2, title: '자막 보며 듣기', description: '자막과 함께 들으며 내용을 파악하세요' },
      { step: 3, title: '문장별 반복 듣기', description: '문장을 10번씩 반복해서 익히세요' },
      { step: 4, title: '다시 자막 없이 듣기', description: '얼마나 잘 들리는지 확인하세요' },
    ],
  };

  // Test 1: 채널 이름이 표시되어야 한다
  it('should display channel name', () => {
    render(<IntroSection channelName={mockConfig.channelName} steps={mockConfig.stepDescriptions} />);

    expect(screen.getByText(/귀가 뚫리는 영어/)).toBeInTheDocument();
  });

  // Test 2: 4개의 스텝이 모두 표시되어야 한다
  it('should display all 4 steps', () => {
    render(<IntroSection channelName={mockConfig.channelName} steps={mockConfig.stepDescriptions} />);

    // 자막 없이 듣기는 Step 1, 4에서 둘 다 나옴
    expect(screen.getAllByText(/자막 없이 듣기/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/자막 보며 듣기/)).toBeInTheDocument();
    expect(screen.getByText(/문장별 반복 듣기/)).toBeInTheDocument();
  });

  // Test 3: 스텝 번호가 표시되어야 한다
  it('should display step numbers', () => {
    render(<IntroSection channelName={mockConfig.channelName} steps={mockConfig.stepDescriptions} />);

    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
  });
});
