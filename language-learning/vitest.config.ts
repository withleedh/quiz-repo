import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./core/src/test/setup.ts'],
    include: ['core/**/*.test.{ts,tsx}'],
  },
});
