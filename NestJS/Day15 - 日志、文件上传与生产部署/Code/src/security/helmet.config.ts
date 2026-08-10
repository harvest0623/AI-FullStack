import helmet from 'helmet';
import { NestApplication } from '@nestjs/core';

/**
 * helmet 安全头配置说明
 * ------------------------------------------------------------
 * helmet 是一组 Express 中间件，会设置多个安全相关响应头：
 *
 *   - Content-Security-Policy：限制资源加载来源，防 XSS 注入
 *   - Cross-Origin-Opener-Policy / Cross-Origin-Embedder-Policy：隔离浏览上下文
 *   - Cross-Origin-Resource-Policy：限制跨域资源加载
 *   - Origin-Agent-Cluster：协同 COOP/COEP
 *   - Referrer-Policy：控制 Referer 头泄露
 *   - Strict-Transport-Security：HSTS，强制 HTTPS（生产环境关键）
 *   - X-Content-Type-Options: nosniff：阻止 MIME 嗅探
 *   - X-DNS-Prefetch-Control：禁用 DNS 预取
 *   - X-Download-Options：禁用 IE 文件下载直接打开
 *   - X-Frame-Options: SAMEORIGIN：防点击劫持
 *   - X-Permitted-Cross-Domain-Policies：限制 Adobe 跨域策略
 *   - X-XSS-Protection: 0：现代浏览器建议关闭（已被 CSP 取代）
 *
 * 启用方式（在 main.ts 中）：
 *   app.use(helmet());
 *
 * 如需自定义策略（例如要内联 script，需放开 CSP）：
 *   app.use(
 *     helmet({
 *       contentSecurityPolicy: {
 *         directives: {
 *           defaultSrc: ["'self'"],
 *           scriptSrc: ["'self'", "'unsafe-inline'"],
 *           imgSrc: ["'self'", 'data:', 'https:'],
 *         },
 *       },
 *       crossOriginEmbedderPolicy: false,
 *     }),
 *   );
 *
 * 生产环境特别注意事项：
 *   - 若部署在 HTTPS 反向代理后，确保代理转发 X-Forwarded-Proto，
 *     helmet 才会正确发送 HSTS 头
 *   - 部分前端框架（Next.js / Nuxt SSR）需要在同源下访问，
 *     注意不要把 connectSrc 限制过死
 */
export function setupHelmet(app: NestApplication): void {
  app.use(
    helmet({
      // 生产环境启用 HSTS（最大年龄 1 年）
      strictTransportSecurity: {
        maxAge: 31536000,
        includeSubDomains: true,
        preload: true,
      },
      // 默认 CSP 策略（按需放宽）
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          scriptSrc: ["'self'"],
          styleSrc: ["'self'", "'unsafe-inline'"],
          imgSrc: ["'self'", 'data:', 'https:'],
          connectSrc: ["'self'"],
          fontSrc: ["'self'", 'data:'],
          objectSrc: ["'none'"],
          frameAncestors: ["'none'"],
        },
      },
      // 关闭 COEP，避免加载第三方图片被阻断
      crossOriginEmbedderPolicy: false,
    }),
  );
}
