export async function readHealth(response: Response): Promise<boolean> {
  if (!response.ok) throw new Error(`API returned ${response.status}`);
  const body: unknown = await response.json();
  if (typeof body !== 'object' || body === null || !('ok' in body) || body.ok !== true) {
    throw new Error('Unexpected health response');
  }
  return true;
}
