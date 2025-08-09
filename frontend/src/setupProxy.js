const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:8001',
      changeOrigin: true,
      secure: false,
      pathRewrite: {
        '^/api': '/api', // no rewrite needed
      },
    })
  );
  
  // Proxy para archivos estáticos
  app.use(
    '/static',
    createProxyMiddleware({
      target: 'http://localhost:8001',
      changeOrigin: true,
      secure: false,
    })
  );
  
  // Proxy para descargas
  app.use(
    '/books',
    createProxyMiddleware({
      target: 'http://localhost:8001',
      changeOrigin: true,
      secure: false,
    })
  );
};
