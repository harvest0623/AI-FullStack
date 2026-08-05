import {
  Controller,
  Get,
  Post,
  Query,
  Body,
  UsePipes,
} from '@nestjs/common';
import { CreateArticleDto } from './dto/create-article.dto';
import { QueryArticleDto } from './dto/query-article.dto';
import {
  PaginationPipe,
  PaginationOptions,
} from '../pipes/pagination.pipe';

/**
 * 文章控制器
 *
 * 演示 Pipe 的三个应用层级中的两个：
 *   1. 全局级：ValidationPipe（main.ts useGlobalPipes）+ TrimPipe（app.module.ts APP_PIPE）
 *      → 对所有路由的 @Body() / @Query() 自动生效
 *   2. 方法级：@UsePipes(new PaginationPipe())
 *      → 仅对 GET /articles/paginated 生效
 *
 * 参数级 Pipe 的演示见 users.controller.ts（@Param('id', ParseIntPipe)）。
 */
@Controller('articles')
export class ArticlesController {
  /**
   * GET /articles
   *
   * 全局 ValidationPipe 自动校验 QueryArticleDto：
   *   - page / pageSize 被转换成数字并校验范围
   *   - sort / order 被校验为合法枚举值
   *   - 多余的查询参数会被 whitelist 剥离或被 forbidNonWhitelisted 拒绝
   */
  @Get()
  findAll(@Query() query: QueryArticleDto) {
    return {
      message: '获取文章列表',
      query,
      data: [
        { id: 1, title: 'NestJS 管道入门' },
        { id: 2, title: 'class-validator 实战' },
      ],
      total: 2,
    };
  }

  /**
   * GET /articles/paginated?page=2&pageSize=5
   *
   * 演示方法级 @UsePipes：
   *   PaginationPipe 把 @Query() 的 { page, pageSize } 转换成结构化的 PaginationOptions，
   *   自动计算 skip / take，控制器拿到后可直接传给数据库查询。
   *
   * 注意：PaginationOptions 是 interface，运行时不存在类型元数据，
   *       因此全局 ValidationPipe 不会尝试校验它，不会与 PaginationPipe 冲突。
   *
   * 静态路由 paginated 必须放在动态路由 :id 之前（本控制器没有 :id 的 GET 路由，但仍保持良好习惯）。
   */
  @Get('paginated')
  @UsePipes(new PaginationPipe())
  findPaginated(@Query() pagination: PaginationOptions) {
    return {
      message: '分页查询文章',
      page: pagination.page,
      pageSize: pagination.pageSize,
      skip: pagination.skip,
      take: pagination.take,
      data: [
        { id: pagination.skip + 1, title: `文章 ${pagination.skip + 1}` },
        { id: pagination.skip + 2, title: `文章 ${pagination.skip + 2}` },
      ],
    };
  }

  /**
   * POST /articles
   *
   * 全局 ValidationPipe + TrimPipe 协同工作：
   *   1. TrimPipe（APP_PIPE）去除 body 中所有字符串字段的两端空格
   *   2. ValidationPipe（useGlobalPipes）校验 DTO：
   *      - title: 3~100 字符
   *      - content: 至少 10 字符
   *      - authorEmail: 合法邮箱
   *      - status: ArticleStatus 枚举
   *      - tags: 字符串数组
   *      - readTime: 0~1000 整数
   *      - publishAt: Date 且晚于当前时间（自定义 @IsAfterNow）
   *      - metadata: 嵌套对象数组（@ValidateNested + @Type）
   *   3. 多余字段（如 isAdmin）会被 forbidNonWhitelisted 拒绝
   *
   * 控制器方法体收到的 body 已经是 CreateArticleDto 实例（transform: true），
   * 所有字段类型正确、值合法，无需手动校验。
   */
  @Post()
  create(@Body() body: CreateArticleDto) {
    return {
      message: '创建文章成功',
      id: Math.floor(Math.random() * 1000) + 1,
      data: body,
    };
  }
}
