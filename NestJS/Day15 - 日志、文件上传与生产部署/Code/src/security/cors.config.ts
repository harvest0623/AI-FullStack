import { CorsOptions } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

/**
 * CORS 跨域配置说明
 * ------------------------------------------------------------
 * CORS（Cross-Origin Resource Sharing）由浏览器同源策略触发：
 *   - 当前端域名与后端域名不同（端口/协议/主机任一不同）
 *     浏览器会要求后端响应 Access-Control-Allow-Origin 头
 *
 * 启用方式（main.ts）：
 *   app.enableCors(buildCorsOptions(configService));
 *
 * 三种典型模式：
 *   1. 全开放：origin: true（任何源都允许，仅适合内网/演示）
 *   2. 白名单：origin: ['https://app.example.com', 'https://admin.example.com']
 *   3. 函数动态判断：根据请求头 Origin 与白名单匹配
 *
 * 关键字段：
 *   - origin：允许的源（string / string[] / boolean / function）
 *   - methods：允许的 HTTP 方法
 *   - credentials：是否允许带 Cookie（true 时 origin 不能为 *）
 *   - allowedHeaders：允许的请求头
 *   - exposedHeaders：允许前端读取的响应头
 *   - maxAge：预检请求 OPTIONS 缓存时长（秒）
 *
 * 安全提示：
 *   - 携带 Cookie（credentials:true）时，origin 必须是具体域名，
 *     不能是 true 或 *
 *   - 生产环境不要用 origin:true，否则任意网站都能发起带 Cookie 的请求
 */
export function buildCorsOptions(config: ConfigService): CorsOptions {
  const origins = (config.get<string>('CORS_ORIGINS', '') || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);

  return {
    // 白名单模式：未配置则退化为 true（开发环境方便联调）
    origin: origins.length ? origins : true,
    methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    credentials: true,
    allowedHeaders: [
      'Authorization',
      'Content-Type',
      'Accept',
      'X-Requested-With',
      'X-Request-Id',
    ],
    exposedHeaders: ['X-Request-Id', 'X-Total-Count'],
    maxAge: 86400, // 预检结果缓存 1 天
  };
}
