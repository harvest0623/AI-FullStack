import { Controller, Get } from '@nestjs/common';
import { AppService } from './app.service';

/**
 * 根控制器
 *
 * @Controller() 类装饰器：声明这是一个控制器，可接收路由前缀
 *   例如 @Controller('users') 表示该控制器下所有路由都以 /users 开头
 *   不传参数时，前缀为空（再叠加 main.ts 中的全局 /api 前缀）
 *
 * 控制器的职责：接收 HTTP 请求、调用 Service、返回响应
 *   严禁在控制器里写业务逻辑（数据库访问、复杂计算、外部调用），这些都下沉到 Service
 */
@Controller()
export class AppController {
  /**
   * 构造函数注入（Constructor Injection）
   *
   * TS 的「参数属性」语法：构造函数参数加修饰符（private/public/readonly）后，
   * TS 会自动声明同名类属性并赋值。等价于：
   *   private readonly appService: AppService;
   *   constructor(appService: AppService) { this.appService = appService; }
   *
   * DI 容器依赖 emitDecoratorMetadata 元数据，读到本类构造函数参数类型是 AppService，
   * 在实例化 AppController 时会自动从容器中取 AppService 实例注入进来。
   */
  constructor(private readonly appService: AppService) {}

  /**
   * @Get() 方法装饰器：声明 GET 路由
   *   不传路径时，路由为控制器前缀本身
   *   叠加全局前缀 /api 后，实际路径为 GET /api
   *
   * 返回值会被 NestJS 自动序列化：
   *   - string → text/html 或 application/json（取决于内容）
   *   - object/array → JSON
   *   - Promise → 等待 resolve 后再返回
   */
  @Get()
  getHello(): string {
    return this.appService.getHello();
  }
}
