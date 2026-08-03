import { Controller, Get, Post, Put, Patch, Delete, All, Head, Options } from '@nestjs/common';
import {
  Param,
  Query,
  Body,
  Headers,
  Req,
  Res,
  HttpCode,
  Redirect,
} from '@nestjs/common';
import { Request, Response } from 'express';
import { CreateArticleDto, UpdateArticleDto } from './dto/create-article.dto';
import { QueryArticleDto } from './dto/query-article.dto';

/**
 * 文章控制器
 *
 * @Controller('articles') 中的字符串作为路由前缀，
 * 该控制器内所有路由都会以 /articles 开头。
 * 配合 main.ts 中的 setGlobalPrefix('api/v1')，
 * 最终路径形如 /api/v1/articles。
 *
 * 本控制器演示：
 * - HTTP 方法装饰器（@Get @Post @Put @Patch @Delete @All @Head @Options）
 * - 路由参数 @Param('id') 与 @Param()
 * - 查询参数 @Query('page') 与 @Query()
 * - 请求体 @Body() 配合 DTO
 * - 请求头 @Headers('authorization') 与 @Headers()
 * - @Req() / @Res() 原始请求与响应
 * - @HttpCode() 自定义状态码
 * - @Redirect() 重定向
 * - 路由通配符
 */
@Controller('articles')
export class ArticlesController {
  /**
   * GET /articles
   * 演示 @Query() 全部查询参数。
   */
  @Get()
  findAll(@Query() query: QueryArticleDto) {
    return {
      message: '获取文章列表',
      query,
      data: [
        { id: 1, title: 'NestJS 控制器入门' },
        { id: 2, title: '路由参数详解' },
      ],
    };
  }

  /**
   * GET /articles/search?keyword=xxx
   * 演示 @Query('keyword') 单个查询参数。
   * 注意：静态路由应放在动态路由之前，避免 :id 匹配到 "search"。
   */
  @Get('search')
  search(@Query('keyword') keyword: string) {
    return {
      message: '搜索文章',
      keyword,
      results: keyword ? [`匹配 "${keyword}" 的文章 1`, `匹配 "${keyword}" 的文章 2`] : [],
    };
  }

  /**
   * GET /articles/export
   * 演示 @Headers() 全部请求头与 @Headers('authorization') 单个请求头。
   */
  @Get('export')
  exportAll(@Headers() headers: Record<string, string>, @Headers('authorization') auth: string) {
    return {
      message: '导出文章（仅演示请求头读取）',
      hasAuth: !!auth,
      userAgent: headers['user-agent'],
    };
  }

  /**
   * GET /articles/:id
   * 演示 @Param('id') 路径参数。
   * 路径参数始终是 string 类型，需要手动转换为 number。
   */
  @Get(':id')
  findOne(@Param('id') id: string) {
    return {
      message: `获取文章详情`,
      id: Number(id),
      title: 'NestJS 路由参数实战',
      content: '通过 @Param 装饰器接收路径参数...',
    };
  }

  /**
   * GET /articles/:id/comments/:commentId
   * 演示多个 @Param() 同时使用。
   */
  @Get(':id/comments/:commentId')
  findComment(@Param('id') id: string, @Param('commentId') commentId: string) {
    return {
      message: '获取文章下的评论',
      articleId: Number(id),
      commentId: Number(commentId),
    };
  }

  /**
   * POST /articles
   * 演示 @Body() 请求体配合 DTO 类型。
   * 默认返回 201 状态码。
   */
  @Post()
  create(@Body() body: CreateArticleDto) {
    return {
      message: '创建文章成功',
      data: body,
      id: Math.floor(Math.random() * 1000) + 1,
    };
  }

  /**
   * PUT /articles/:id
   * 全量更新，使用 UpdateArticleDto。
   */
  @Put(':id')
  update(@Param('id') id: string, @Body() body: UpdateArticleDto) {
    return {
      message: `PUT 全量更新文章 ${id}`,
      id: Number(id),
      data: body,
    };
  }

  /**
   * PATCH /articles/:id
   * 部分更新。
   * 演示 @HttpCode(200) 把默认的 200 改写（PUT/PATCH 默认就是 200）。
   */
  @Patch(':id')
  @HttpCode(200)
  partialUpdate(@Param('id') id: string, @Body() body: UpdateArticleDto) {
    return {
      message: `PATCH 部分更新文章 ${id}`,
      id: Number(id),
      data: body,
    };
  }

  /**
   * DELETE /articles/:id
   * 演示 @HttpCode(204) 删除成功无内容返回。
   */
  @Delete(':id')
  @HttpCode(204)
  remove(@Param('id') id: string) {
    // 204 No Content 不会返回 body
    return;
  }

  /**
   * GET /articles/redirect/docs
   * 演示 @Redirect() 装饰器。
   * 第一个参数是目标 URL，第二个参数是 HTTP 状态码（默认 302）。
   */
  @Get('redirect/docs')
  @Redirect('https://docs.nestjs.com/controllers', 302)
  redirectToDocs() {
    // 该返回值可以覆盖 @Redirect 的 url 参数
    // 返回 { url: 'xxx', statusCode: 301 } 即可动态重定向
  }

  /**
   * GET /articles/ab*cd
   * 演示路由通配符匹配。
   * 例如：abcd、ab_xyz_cd、ab123cd 都能匹配。
   * 仅支持 Express 底层的正则通配，不要在生产路由中滥用。
   */
  @Get('ab*cd')
  wildcardMatch() {
    return {
      message: '命中通配符路由 ab*cd',
      pattern: 'ab*cd',
    };
  }

  /**
   * @All('all-method')
   * 演示 @All 装饰器，匹配任意 HTTP 方法。
   * 常用于通配钩子或健康检查的兜底。
   */
  @All('all-method')
  handleAnyMethod(@Req() req: Request) {
    return {
      message: '命中 @All 路由',
      method: req.method,
      path: req.path,
    };
  }

  /**
   * @Head('head-info')
   * 演示 @Head 装饰器，只返回响应头，不返回 body。
   * 客户端常用于探测资源是否存在。
   */
  @Head('head-info')
  headInfo() {
    // Head 请求由 Express 自动剥离 body
    return { message: 'Head 请求不会看到这行 body' };
  }

  /**
   * @Options('options-info')
   * 演示 @Options 装饰器，用于 CORS 预检或资源能力声明。
   */
  @Options('options-info')
  optionsInfo() {
    return { allowed: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'] };
  }

  /**
   * POST /articles/raw
   * 演示 @Req() 与 @Res() 原生 Express 对象。
   *
   * 注意：
   * 一旦使用 @Res() 注入响应对象，
   * NestJS 的拦截器、序列化等后续能力会失效。
   * 必须显式调用 res.send() / res.json() 返回响应，
   * 否则请求会一直挂起。
   */
  @Post('raw')
  rawHandler(@Req() req: Request, @Res() res: Response) {
    res.json({
      message: '通过 @Res() 手动返回响应',
      method: req.method,
      url: req.originalUrl,
      timestamp: new Date().toISOString(),
    });
  }
}
