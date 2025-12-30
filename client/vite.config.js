import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'health-endpoint',
      configureServer(server) {
        server.middlewares.use('/health', (req, res, next) => {
          if (req.method === 'GET') {
            res.setHeader('Content-Type', 'application/json');
            // Standard health check response format
            // Note: Process info not available in browser context
            // The Vite dev server process info would need to be provided separately
            // For production builds, this would need to be handled by the web server
            res.end(JSON.stringify({
              status: 'healthy',
              service: 'web-client',
              version: '1.0.0',
              process_info: {
                pid: process.pid || 0,
                uptime_seconds: process.uptime ? Math.round(process.uptime() * 100) / 100 : 0.0,
                cpu_percent: 0.0, // Not available in Node.js without external library
                memory_mb: process.memoryUsage ? Math.round(process.memoryUsage().heapUsed / (1024 * 1024) * 100) / 100 : 0.0,
                memory_percent: 0.0, // Would need system memory info
                threads: 0, // Node.js is single-threaded (worker threads not counted here)
                open_files: 0, // Would need external library
                note: 'Process info limited in Vite dev server context'
              }
            }));
          } else {
            next();
          }
        });
      },
    },
  ],
  server: {
    port: 3000,
    host: true,
  },
  build: {
    outDir: 'dist',
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
    css: true,
  },
});
