import { spawn } from 'node:child_process';
import { once } from 'node:events';

const port = 3999;
const child = spawn(process.execPath, ['src/server.js'], {
  cwd: process.cwd(),
  env: {
    ...process.env,
    PORT: String(port),
    LINE_CHANNEL_SECRET: '',
    LINE_CHANNEL_ACCESS_TOKEN: '',
    ENABLE_FARE_REFRESH: 'false'
  },
  stdio: ['ignore', 'pipe', 'pipe']
});

let output = '';
let errorOutput = '';
child.stdout.on('data', (chunk) => {
  output += chunk.toString();
});
child.stderr.on('data', (chunk) => {
  errorOutput += chunk.toString();
});

try {
  await waitForServer(port);
  await expectOk('/health');
  await expectOk('/ready');
  await expectWebhook('M3');
  await expectWebhook('TPE');
  console.log('self-test ok');
} finally {
  child.kill('SIGTERM');
  await Promise.race([
    once(child, 'exit'),
    new Promise((resolve) => setTimeout(resolve, 1000))
  ]);
  if (errorOutput.trim()) console.error(errorOutput.trim());
}

async function waitForServer(port) {
  const deadline = Date.now() + 5000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`http://localhost:${port}/health`);
      if (response.ok) return;
    } catch {
      await new Promise((resolve) => setTimeout(resolve, 150));
    }
  }
  throw new Error(`Server did not start. Output:\n${output}\n${errorOutput}`);
}

async function expectOk(path) {
  const response = await fetch(`http://localhost:${port}${path}`);
  if (!response.ok) throw new Error(`${path} returned ${response.status}`);
  const data = await response.json();
  if (!data.ok) throw new Error(`${path} returned ok=false`);
}

async function expectWebhook(text) {
  const response = await fetch(`http://localhost:${port}/webhook`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      events: [{
        type: 'message',
        replyToken: `self-test-${text}`,
        source: { type: 'user', userId: 'self-test-user' },
        message: { id: crypto.randomUUID(), type: 'text', text }
      }]
    })
  });
  if (!response.ok) throw new Error(`webhook ${text} returned ${response.status}`);
  const data = await response.json();
  if (!data.ok) throw new Error(`webhook ${text} returned ok=false`);
}
