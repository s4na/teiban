import { describe, expect, it } from 'vite-plus/test';
import { readHealth } from './api';

describe('health response', () => {
  it('accepts the API contract', async () => {
    await expect(readHealth(Response.json({ ok: true }))).resolves.toBe(true);
  });
  it('rejects an HTTP failure', async () => {
    await expect(readHealth(new Response('', { status: 503 }))).rejects.toThrow('503');
  });
  it('rejects a different JSON shape', async () => {
    await expect(readHealth(Response.json({ status: 'healthy' }))).rejects.toThrow(
      'Unexpected health response',
    );
  });
});
