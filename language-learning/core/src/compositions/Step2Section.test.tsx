/**
 * Step2Section Component Tests (TDD)
 * 
 * Step 2: 자막 보며 듣기
 * - 배경 이미지 어둡게
 * - 영어 자막만 표시 (중앙)
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Step2Section } from './Step2Section';

describe('Step2Section', () => {
  const mockSentence = {
    id: 1,
    speaker: 'M' as const,
    target: 'Good morning. I am here for the sunrise tour.',
    native: '좋은 아침이에요.',
    words: [],
  };

  // Test 1: 영어 자막이 표시되어야 한다
  it('should display English subtitle', () => {
    render(<Step2Section sentence={mockSentence} stepNumber={2} totalSteps={4} />);

    expect(screen.getByText(/Good morning/i)).toBeInTheDocument();
  });

  // Test 2: 한글 자막은 표시되지 않아야 한다
  it('should NOT display Korean translation', () => {
    render(<Step2Section sentence={mockSentence} stepNumber={2} totalSteps={4} />);

    expect(screen.queryByText(/좋은 아침이에요/)).not.toBeInTheDocument();
  });

  // Test 3: Step 2 표시기가 나타나야 한다
  it('should display Step 2 indicator', () => {
    render(<Step2Section sentence={mockSentence} stepNumber={2} totalSteps={4} />);

    expect(screen.getByText(/Step 2/i)).toBeInTheDocument();
  });

  // Test 4: 어두운 오버레이가 있어야 한다
  it('should have dark overlay', () => {
    render(<Step2Section sentence={mockSentence} stepNumber={2} totalSteps={4} />);

    const overlay = screen.getByTestId('dark-overlay');
    expect(overlay).toBeInTheDocument();
  });
});
