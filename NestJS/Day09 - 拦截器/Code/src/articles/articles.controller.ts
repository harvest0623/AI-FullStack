import {
  Controller,
  Get,
  Param,
  UseInterceptors,
} from '@nestjs/common';
import { CacheInterceptor } from '../interceptors/cache.interceptor';
import { ExcludePasswordInterceptor } from '../interceptors/exclude-password.interceptor';

/**
 * ArticlesController —— 文章业务路由
 *
 * 演示方法级拦截器的使用方式：
 * 1. @UseInterceptors(CacheInterceptor)            缓存命中
 * 2. @UseInterceptors(ExcludePasswordInterceptor)  字段脱敏
 *
 * 注意：方法级拦截器只对当前路由生效。
 * 若想让整个控制器都生效，把 @UseInterceptors() 放到 @Controller() 上方即可。
 */
@Controller('articles')
export class ArticlesController {
  // 模拟数据库数据，password 字段需要在响应中被过滤
  private readonly articles = [
    { id: 1, title: 'NestJS 拦截器入门', author: '张三', password: 'pwd-111' },
    { id: 2, title: 'AOP 面向切面编程', author: '李四', password: 'pwd-222' },
    { id: 3, title: 'RxJS 操作符实战', author: '王五', password: 'pwd-333' },
  ];

  /**
   * GET /articles
   * 演示：缓存拦截器（10 秒内重复访问会命中缓存）
   * 全局 TransformInterceptor 会自动包装为 { code, message, data }
   */
  @Get()
  @UseInterceptors(CacheInterceptor)
  findAll() {
    return this.articles;
  }

  /**
   * GET /articles/:id
   * 演示：字段过滤拦截器，剔除返回数据中的 password
   */
  @Get(':id')
  @UseInterceptors(ExcludePasswordInterceptor)
  findOne(@Param('id') id: string) {
    return this.articles.find((a) => a.id === Number(id));
  }

  /**
   * GET /articles/slow/:ms
   * 演示：全局 TimeoutInterceptor 超时控制
   * 当 :ms > 3000 时会被拦截器中断，返回 408 Request Timeout
   *
   * 该路由为 3 段路径（/articles/slow/:ms），与 /articles/:id（2 段）不会冲突。
   * 测试：访问 http://localhost:3000/articles/slow/5000
   */
  @Get('slow/:ms')
  async slow(@Param('ms') ms: string) {
    const delay = Number(ms);
    await new Promise((resolve) => setTimeout(resolve, delay));
    return { message: `沉睡 ${delay}ms 后返回` };
  }
}
