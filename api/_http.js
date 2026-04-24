export function sendJson(res, status, data) {
  res.statusCode = status;
  res.setHeader('content-type', 'application/json; charset=utf-8');
  res.end(JSON.stringify(data));
}

export function methodNotAllowed(res) {
  sendJson(res, 405, { ok: false, error: 'Method not allowed' });
}

export function readRawBody(req) {
  if (Buffer.isBuffer(req.body)) return Promise.resolve(req.body);
  if (typeof req.body === 'string') return Promise.resolve(Buffer.from(req.body));
  if (req.body && typeof req.body === 'object') return Promise.resolve(Buffer.from(JSON.stringify(req.body)));

  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', (chunk) => chunks.push(chunk));
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

export function parseJsonBody(rawBody) {
  if (!rawBody?.length) return {};
  return JSON.parse(rawBody.toString('utf8'));
}
