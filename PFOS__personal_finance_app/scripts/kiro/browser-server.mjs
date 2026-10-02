/** Owner: contracts/programs/KIRO_DEVELOPMENT_ENVIRONMENT.md. Phase 1 (KDE06). */
import { readFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { extname } from 'node:path';
import { localFile } from './validate.mjs';

const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css',
  '.svg': 'image/svg+xml', '.webmanifest': 'application/manifest+json', '.json': 'application/json',
  '.png': 'image/png', '.woff2': 'font/woff2', '.ico': 'image/x-icon' };

export function assetPath(rawUrl) {
  const path = decodeURIComponent(rawUrl.split('?')[0]);
  if (!path.startsWith('/') || path.startsWith('//')) throw new Error('PATH');
  const relative = path === '/' ? 'index.html' : path.slice(1);
  if (!/^[a-zA-Z0-9_./-]+$/.test(relative) || relative.split('/').some((part) => !part || part === '.' || part === '..')
    || !Object.hasOwn(MIME, extname(relative))) throw new Error('PATH');
  return relative;
}

export async function serveBuild(dist) {
  localFile(dist, 'index.html');
  const server = createServer((req, res) => {
    try {
      if (req.method !== 'GET' && req.method !== 'HEAD') { res.writeHead(405); res.end(); return; }
      const relative = assetPath(req.url);
      const data = readFileSync(localFile(dist, relative));
      res.writeHead(200, { 'Content-Type': MIME[extname(relative)], 'Cache-Control': 'no-store',
        'X-Content-Type-Options': 'nosniff' });
      res.end(req.method === 'HEAD' ? undefined : data);
    } catch { res.writeHead(404); res.end('Not found'); }
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  return { origin: `http://127.0.0.1:${server.address().port}`,
    close: () => new Promise((resolve, reject) => {
      server.closeAllConnections();
      server.close((error) => error ? reject(error) : resolve());
    }) };
}
