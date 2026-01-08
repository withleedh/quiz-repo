/**
 * Step1Section Component Tests (TDD)
 * 
 * Step 1: 자막 없이 듣기
 * - 배경 이미지만 표시
 * - 텍스트 없음
 * - Step 표시기 표시
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Step1Section } from './Step1Section';

describe('Step1Section', () => {
  // Test 1: Step 1 표시기가 나타나야 한다
  it('should display Step 1 indicator', () => {
    render(<Step1Section stepNumber={1} totalSteps={4} />);

    expect(screen.getByText(/Step 1/i)).toBeInTheDocument();
  });

  // Test 2: 자막 없이 청취 안내 텍스트가 표시되어야 한다
  it('should display listening instruction', () => {
    render(<Step1Section stepNumber={1} totalSteps={4} />);

    expect(screen.getByText(/자막 없이 듣기/i)).toBeInTheDocument();
  });

  // Test 3: 배경 이미지 영역이 있어야 한다
  it('should have background image container', () => {
    render(<Step1Section stepNumber={1} totalSteps={4} backgroundImage="/test.jpg" />);

    const container = screen.getByTestId('background-container');
    expect(container).toBeInTheDocument();
  });
});
