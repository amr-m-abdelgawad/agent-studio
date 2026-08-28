import type { Plugin } from 'vite';
import { handleMockRequest } from './handlers';

export function mockApiPlugin(): Plugin {
  return {
    name: 'mock-api',
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        if (!req.url?.startsWith('/v1')) {
          next();
          return;
        }
        try {
          const url = new URL(req.url, 'http://localhost');
          const handled = await handleMockRequest(req, res, url);
          if (!handled) next();
        } catch (error) {
          console.error('Mock API error:', error);
          res.statusCode = 500;
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({ error: { code: 'internal', message: 'Internal error' } }));
        }
      });
    },
  };
}
