import { Injectable } from '@nestjs/common';

/**
 * 根服务
 *
 * @Injectable() 装饰器：标记此类为可注入的 Provider
 *   - DI 容器看到这个装饰器，会在模块的 providers 中注册它
 *   - 默认作用域是单例（Scope.DEFAULT），整个应用共享一个实例
 *   - 任何想被注入的类（Service / Repository / Guard / Pipe / Interceptor / Filter / Middleware）
 *     都必须加这个装饰器
 *
 * Service 的职责：承载业务逻辑
 *   - 数据访问、计算、外部 API 调用都放在这里
 *   - Controller 只做请求响应映射，业务下沉到 Service
 *   - 这种分层让 Service 可被多个 Controller 复用，也便于单元测试
 */
@Injectable()
export class AppService {
  /**
   * 返回欢迎语
   * 实际项目中这里可能会查数据库、调用外部服务、做计算后返回
   */
  getHello(): string {
    return 'Hello NestJS! Welcome to Day01.';
  }
}
