import {
  Body,
  Controller,
  Delete,
  Get,
  Headers,
  Param,
  Patch,
  Post,
  Query,
  UseFilters,
} from '@nestjs/common';
import { ArticlesService } from './articles.service';
import { HttpExceptionFilter } from '../filters/http-exception.filter';

/**
 * 文章控制器
 *
 * 演示三种异常触发路径，分别命中三个全局过滤器：
 *   1. 业务异常 → BusinessExceptionFilter  （携带 errorCode）
 *   2. HTTP 异常 → HttpExceptionFilter      （内置异常类）
 *   3. 未知异常 → AllExceptionsFilter       （兜底 500）
 *
 * 同时演示方法级过滤器：
 *   在 methodFilterDemo 路由上单独挂一个 HttpExceptionFilter，
 *   方法级 > 控制器级 > 全局级，优先级高的先匹配。
 *
 * 路由顺序说明：
 *   静态多段路由（demo/xxx）放在 :id 之前，避免被 :id 误匹配。
 */
@Controller('articles')
export class ArticlesController {
  constructor(private readonly articlesService: ArticlesService) {}

  // ============ 演示路由（静态，多段路径避免与 :id 冲突）============

  /**
   * GET /articles/demo/search?title=xxx
   * 触发 NotFoundException（内置 HTTP 异常）—— 走 HttpExceptionFilter
   */
  @Get('demo/search')
  findByTitle(@Query('title') title: string) {
    return this.articlesService.findByTitle(title || '不存在的关键词');
  }

  /**
   * GET /articles/demo/risky
   * 触发原生 Error —— 走 AllExceptionsFilter 兜底，返回 500
   */
  @Get('demo/risky')
  risky() {
    return this.articlesService.riskyOperation();
  }

  /**
   * GET /articles/demo/method-filter
   * 方法级过滤器演示
   *
   * @UseFilters(HttpExceptionFilter) 只在这一条路由上额外挂一个过滤器。
   * 即使该路由不抛异常，过滤器也会被实例化（只是不会触发 catch）。
   * 方法级过滤器优先级最高，全局过滤器次之。
   */
  @Get('demo/method-filter')
  @UseFilters(HttpExceptionFilter)
  methodFilterDemo() {
    return {
      message: '这条路由额外挂了方法级 HttpExceptionFilter',
      note: '方法级 > 控制器级 > 全局级',
    };
  }

  // ============ 业务路由（含动态 :id）============

  /**
   * GET /articles/:id
   * 触发 ArticleNotFoundException（业务异常）—— 走 BusinessExceptionFilter
   * 测试：GET /articles/99 → 404 + code: ARTICLE_NOT_FOUND
   */
  @Get(':id')
  findOne(@Param('id') id: string) {
    return this.articlesService.findOne(Number(id));
  }

  /**
   * PATCH /articles/:id
   * 触发 ArticleLockedException（业务异常，HTTP 423）
   * 测试：PATCH /articles/2 { "title": "新标题" } → 423 + code: ARTICLE_LOCKED
   */
  @Patch(':id')
  update(@Param('id') id: string, @Body() body: { title?: string }) {
    return this.articlesService.update(Number(id), body);
  }

  /**
   * POST /articles/:id/publish
   * 触发 ValidationException 或 UserNotFoundException
   * 测试：
   *   POST /articles/1/publish { }                  → 400 + VALIDATION_FAILED
   *   POST /articles/1/publish { "authorId": 999 }  → 404 + USER_NOT_FOUND
   */
  @Post(':id/publish')
  publish(
    @Param('id') id: string,
    @Body() body: { authorId?: number },
  ) {
    return this.articlesService.publish(Number(id), body.authorId ?? 0);
  }

  /**
   * DELETE /articles/:id
   * 触发 ForbiddenException（内置 HTTP 异常）
   * 测试：
   *   DELETE /articles/1                       → 403 + HTTP_403
   *   DELETE /articles/1  (Header: x-role=admin) → 200
   */
  @Delete(':id')
  delete(@Param('id') id: string, @Headers('x-role') role: string) {
    return this.articlesService.delete(Number(id), role || 'user');
  }
}
