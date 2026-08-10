import { Module } from '@nestjs/common';

/**
 * Security 模块
 *
 * 本模块仅作"配置说明"的载体，并不真正注册任何 Provider/Controller。
 * 原因：helmet / cors / compression 都是 Express 中间件，在 main.ts 直接 app.use() 即可，
 * 不需要进入 NestJS 容器。Throttler 已在 AppModule 通过 ThrottlerModule.forRootAsync 配置。
 *
 * 文件清单：
 *   - helmet.config.ts   helmet 中间件配置（启用方法 / 关键头说明 / CSP 调整）
 *   - cors.config.ts     CORS 白名单配置（origin 模式 / credentials 注意事项）
 *   - throttler.config.ts 限流配置（TTL/Limit / 多策略 / 分布式存储）
 *
 * 实际启用方式（参考 main.ts）：
 *   app.use(helmet());
 *   app.enableCors(buildCorsOptions(config));
 *   app.use(compression({ threshold: 1024 }));
 *
 * 生产环境安全清单：
 *   ✓ helmet          安全 HTTP 头
 *   ✓ cors            白名单跨域
 *   ✓ compression     gzip 压缩
 *   ✓ throttler       IP 限流
 *   ✓ ValidationPipe  全局参数校验（防注入）
 *   ✓ JWT 鉴权         防止未授权访问（Day14）
 *   ✓ 参数白名单       whitelist:true 自动剔除未声明字段
 *   ✓ HTTPS           反向代理层终止 TLS
 *   ✓ 密钥管理         .env 不入库，用 k8s secret / Vault
 *   ✓ 依赖审计         npm audit / snyk 定期扫描
 */
@Module({})
export class SecurityModule {}
