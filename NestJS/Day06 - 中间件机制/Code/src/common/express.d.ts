/**
 * Express.Request 类型扩展
 *
 * 在 NestJS 默认的 Express 平台中，
 * 控制器通过 @Req() 注入的 Request 对象就是 Express 的 Request。
 * 当我们需要在中间件、守卫、拦截器中给 req 注入额外字段时，
 * 就需要通过 declare module 扩展 Request 类型，
 * 否则 TypeScript 会报错 "Property 'requestId' does not exist on type 'Request'"。
 *
 * 本文件演示：RequestIdMiddleware 会在每个请求开始时把 requestId 挂到 req 上，
 * 后续 LoggerMiddleware / AuthMiddleware / ArticlesController 都能读到。
 *
 * 使用方式：
 *   @Get()
 *   list(@Req() req: Request) {
 *     return { requestId: req.requestId }; // 这里访问 requestId 不会报类型错误
 *   }
 *
 * 注意：必须以 .d.ts 结尾，并且要被 tsconfig 包含进编译范围，
 * 否则类型扩展不会生效。NestJS 默认 src/**/*.ts 都会被编译。
 */

declare module 'express' {
  interface Request {
    /**
     * 当前请求唯一标识。
     * 由 RequestIdMiddleware 注入，每个请求都会存在。
     */
    requestId?: string;
  }
}
