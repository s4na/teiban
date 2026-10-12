import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite-plus';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: { '/api': 'http://127.0.0.1:8080' },
  },
  lint: {
    options: { typeAware: true, typeCheck: true },
    ignorePatterns: ['dist/**'],
  },
  fmt: { singleQuote: true, ignorePatterns: ['dist/**'] },
  test: { include: ['src/**/*.test.{ts,tsx}'] },
});
