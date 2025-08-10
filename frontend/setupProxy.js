const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  console.log('🔧 Configurando proxy para Tailscale...');
  console.log('🌐 Backend URL:', 'https://100.81.201.68:8001');
  
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'https://100.81.201.68:8001',
      changeOrigin: true,
      secure: false, // Permitir certificados autofirmados
      logLevel: 'debug',
      headers: {
        'X-Forwarded-Proto': 'https',
        'X-Forwarded-Host': '100.81.201.68',
      },
      onError: (err, req, res) => {
        console.error('❌ Error en proxy API:', err);
        console.error('   Request URL:', req.url);
        console.error('   Request method:', req.method);
        console.error('   Backend URL:', 'https://100.81.201.68:8001');
      },
      onProxyReq: (proxyReq, req, res) => {
        console.log('🔍 Proxy request:', req.method, req.url);
        console.log('🔍 Target URL:', proxyReq.path);
        console.log('🔍 Target host:', proxyReq.getHeader('host'));
      },
      onProxyRes: (proxyRes, req, res) => {
        console.log('✅ Proxy response:', proxyRes.statusCode, req.url);
        console.log('🔍 Content-Type:', proxyRes.headers['content-type']);
      }
    })
  );
  
  console.log('✅ Proxy configurado para /api -> https://100.81.201.68:8001');
};