import { defineConfig } from 'eslint/config';

export default defineConfig([
  { ignores: ['node_modules/**', 'dist/**'] },
  {
    rules: {
      'no-undef': 'error',
      'no-unused-vars': 'error',
      'no-eval': 'error',
      'eqeqeq': 'error'
    }
  },
  {
    files: ['extension/content.js'],
    languageOptions: { globals: { document: 'readonly', MutationObserver: 'readonly' } }
  },
  {
    files: ['test/**/*.js'],
    languageOptions: { globals: { document: 'readonly', getComputedStyle: 'readonly', MutationObserver: 'readonly' } }
  }
]);
