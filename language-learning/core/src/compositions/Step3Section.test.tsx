/**
 * Step3Section Component Tests
 * 
 * TDD: 테스트를 먼저 작성하고, 최소한의 코드로 통과시킨다.
 * 
 * 사용자 관점에서 테스트:
 * - 영어 문장이 표시되는가?
 * - 한글 해석이 표시되는가?
 * - 단어 뜻이 표시되는가?
 * - 남성 화자는 파란색으로 표시되는가?
 * - 여성 화자는 핑크색으로 표시되는가?
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Step3Section } from './Step3Section';

describe('Step3Section', () => {
  const mockSentence = {
    id: 1,
    speaker: 'M' as const,
    target: 'Good morning. I am here for the sunrise tour.',
    native: '좋은 아침이에요. 저는 일출 투어를 하러 왔어요.',
    words: [
      { word: 'Good morning', meaning: '좋은 아침' },
      { word: 'sunrise', meaning: '일출' },
      { word: 'tour', meaning: '투어' },
    ],
  };

  const mockColors = {
    maleText: '#87CEEB',
    femaleText: '#FF69B4',
    nativeText: '#FFFFFF',
    wordMeaning: '#888888',
    background: '#000000',
  };

  // Test 1: 영어 문장이 화면에 표시되어야 한다
  it('should display the English sentence', () => {
    render(
      <Step3Section 
        sentence={mockSentence}
        colors={mockColors}
        repeatIndex={1}
        totalRepeats={10}
      />
    );

    const targetText = screen.getByTestId('target-text');
    expect(targetText).toHaveTextContent(/Good morning/i);
    expect(targetText).toHaveTextContent(/sunrise tour/i);
  });

  // Test 2: 한글 해석이 화면에 표시되어야 한다
  it('should display the Korean translation', () => {
    render(
      <Step3Section 
        sentence={mockSentence}
        colors={mockColors}
        repeatIndex={1}
        totalRepeats={10}
      />
    );

    expect(screen.getByText(/좋은 아침이에요/)).toBeInTheDocument();
  });

  // Test 3: 단어별 뜻이 표시되어야 한다
  it('should display word meanings', () => {
    render(
      <Step3Section 
        sentence={mockSentence}
        colors={mockColors}
        repeatIndex={1}
        totalRepeats={10}
      />
    );

    const wordMeanings = screen.getByTestId('word-meanings');
    expect(wordMeanings).toHaveTextContent(/Good morning/);
    expect(wordMeanings).toHaveTextContent(/일출/);
  });

  // Test 4: 남성 화자의 텍스트는 설정된 색상으로 표시되어야 한다
  it('should display male speaker text with configured color', () => {
    render(
      <Step3Section 
        sentence={mockSentence}
        colors={mockColors}
        repeatIndex={1}
        totalRepeats={10}
      />
    );

    const englishText = screen.getByTestId('target-text');
    expect(englishText).toHaveStyle({ color: '#87CEEB' });
  });

  // Test 5: 여성 화자의 텍스트는 핑크색으로 표시되어야 한다
  it('should display female speaker text with pink color', () => {
    const femaleSentence = { ...mockSentence, speaker: 'F' as const };
    
    render(
      <Step3Section 
        sentence={femaleSentence}
        colors={mockColors}
        repeatIndex={1}
        totalRepeats={10}
      />
    );

    const englishText = screen.getByTestId('target-text');
    expect(englishText).toHaveStyle({ color: '#FF69B4' });
  });

  // Test 6: 반복 횟수가 표시되어야 한다
  it('should display repeat counter', () => {
    render(
      <Step3Section 
        sentence={mockSentence}
        colors={mockColors}
        repeatIndex={5}
        totalRepeats={10}
      />
    );

    expect(screen.getByText(/5.*10/)).toBeInTheDocument();
  });
});
