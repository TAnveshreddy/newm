import { createApp } from './app';
import { getConfig } from './config';

/**
 * Backend entry point. In production, HTTPS/TLS is terminated by Azure Front
 * Door / App Service; the app itself listens on plain HTTP behind them.
 */
function main(): void {
  const cfg = getConfig();
  const app = createApp();
  app.listen(cfg.port, () => {
    // eslint-disable-next-line no-console
    console.log(
      JSON.stringify({
        ts: new Date().toISOString(),
        msg: 'backend started',
        port: cfg.port,
        env: cfg.env,
        mockMode: cfg.mockMode,
      }),
    );
    if (cfg.mockMode && cfg.env === 'production') {
      // eslint-disable-next-line no-console
      console.warn('WARNING: MOCK_MODE is enabled in production. Disable it before serving real users.');
    }
  });
}

main();
