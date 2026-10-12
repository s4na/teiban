import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { readHealth } from './api';
import './style.css';

function App() {
  const [status, setStatus] = useState('接続確認中');
  useEffect(() => {
    const controller = new AbortController();
    void fetch('/api/health', { signal: controller.signal })
      .then(readHealth)
      .then(() => setStatus('Go APIに接続できました'))
      .catch(() => {
        if (!controller.signal.aborted) setStatus('Go APIに接続できません');
      });
    return () => controller.abort();
  }, []);
  return (
    <main>
      <h1>VoidZero＋Go</h1>
      <p role="status">{status}</p>
    </main>
  );
}

const root = document.getElementById('root');
if (!root) throw new Error('Missing root element');
createRoot(root).render(<App />);
