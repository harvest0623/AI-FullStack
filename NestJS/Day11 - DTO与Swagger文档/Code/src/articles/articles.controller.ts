import {
  Body,
  Controller,
  Delete,
  Get,
  HttpCode,
  HttpStatus,
  Param,
  ParseIntPipe,
  Patch,
  Post,
  Query,
} from '@nestjs/common';
import {
  ApiBadRequestResponse,
  ApiBearerAuth,
  ApiBody,
  ApiCreatedResponse,
  ApiNotFoundResponse,
  ApiOkResponse,
  ApiOperation,
  ApiParam,
  ApiProperty,
  ApiQuery,
  ApiTags,
  ApiUnauthorizedResponse,
} from '@nestjs/swagger';
import { IsInt, Min } from 'class-validator';

import { ArticlesService } from './articles.service';
import { CreateArticleDto, ArticleStatus } from './dto/create-article.dto';
import { UpdateArticleDto } from './dto/update-article.dto';
import { QueryArticleDto } from './dto/query-article.dto';
import {
  ArticleResponseDto,
  ArticleListResponseDto,
} from './dto/article-response.dto';

/**
 * 一个仅用于 Swagger 文档演示的小 DTO（不需要独立文件）
 *
 * 用于演示 @ApiBody 自定义请求体描述，常见于"请求体不是某个 DTO 全部"
 * 或者"需要为某个接口单独说明字段"的场景。
 */
class PublishArticleDto {
  @ApiProperty({
    description: '执行发布操作的管理员 ID',
    example: 1,
  })
  @IsInt()
  @Min(1)
  operatorId: number;
}

/**
 * 文章控制器（完整 CRUD + Swagger 装饰器）
 *
 * 装饰器分工速查：
 *   类级别：@ApiTags 把接口归类到"文章"分组
 *   方法级别：
 *     @ApiOperation        描述接口用途
 *     @ApiOkResponse       200/201 响应
 *     @ApiCreatedResponse  201 响应（POST 创建）
 *     @ApiNotFoundResponse 404 响应
 *     @ApiBadRequestResponse 400 响应（校验失败）
 *     @ApiUnauthorizedResponse 401 响应（未登录）
 *     @ApiBearerAuth       标记该接口需要 Bearer Token
 *   参数级别：
 *     @ApiParam  路径参数
 *     @ApiQuery  查询参数（@Query() 整体接收时可不加，DTO 字段会自动文档化）
 *     @ApiBody   请求体（@Body() 整体接收时可不加，DTO 会自动文档化）
 *
 * 重要原则：
 *   1. @Body() / @Query() 整体接收 DTO 时，Swagger 会自动读取 DTO 的
 *      @ApiProperty 生成文档，无需在每个方法上重复 @ApiBody / @ApiQuery。
 *   2. @ApiResponse 系列装饰器最好显式声明，因为返回结构由你控制，
 *      Swagger 无法自动推断 404 / 400 时的响应结构。
 *   3. @ApiOperation 的 summary 尽量短，description 写详细。
 */
@ApiTags('文章')
@ApiBearerAuth() // 整个控制器默认需要登录（个别接口可在方法上覆盖）
@Controller('articles')
export class ArticlesController {
  constructor(private readonly articlesService: ArticlesService) {}

  /**
   * GET /articles
   *
   * 列表查询接口。@Query() 整体接收 QueryArticleDto，Swagger 自动读取
   * DTO 字段生成 query 参数文档，无需逐个 @ApiQuery。
   */
  @Get()
  @ApiOperation({
    summary: '分页查询文章列表',
    description:
      '支持关键词搜索、状态过滤、字段排序、分页。所有参数可选，缺省时返回第 1 页前 10 条。',
  })
  @ApiOkResponse({
    description: '查询成功，返回分页列表',
    type: ArticleListResponseDto,
  })
  findAll(@Query() query: QueryArticleDto) {
    return this.articlesService.findAll(query);
  }

  /**
   * GET /articles/:id
   *
   * @ApiParam 显式声明路径参数，让文档更明确（也可以省略让 Swagger 自动推断）
   * @ApiNotFoundResponse 标注 404 时的响应结构
   */
  @Get(':id')
  @ApiOperation({ summary: '获取文章详情' })
  @ApiParam({
    name: 'id',
    description: '文章 ID',
    example: 1,
    type: Number,
  })
  @ApiOkResponse({
    description: '文章详情',
    type: ArticleResponseDto,
  })
  @ApiNotFoundResponse({ description: '文章不存在' })
  findOne(@Param('id', ParseIntPipe) id: number) {
    return this.articlesService.findOne(id);
  }

  /**
   * POST /articles
   *
   * 创建接口。@Body() 整体接收 CreateArticleDto，Swagger 自动读取
   * DTO 的 @ApiProperty 生成请求体 schema。
   *
   * @ApiCreatedResponse 标注 201 响应（创建成功），
   * 注意：NestJS 默认 POST 返回 200，需要手动 @HttpCode(201) 才会变 201。
   */
  @Post()
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({
    summary: '创建文章',
    description: '需要登录，请求体需通过 class-validator 校验。',
  })
  @ApiBody({
    description: '文章内容',
    type: CreateArticleDto,
  })
  @ApiCreatedResponse({
    description: '创建成功',
    type: ArticleResponseDto,
  })
  @ApiBadRequestResponse({ description: '请求参数校验失败' })
  @ApiUnauthorizedResponse({ description: '未登录或 token 失效' })
  create(@Body() dto: CreateArticleDto) {
    return this.articlesService.create(dto);
  }

  /**
   * PATCH /articles/:id
   *
   * 部分更新。@Body() 整体接收 UpdateArticleDto（派生自 CreateArticleDto），
   * Swagger 文档会展示所有可选字段。
   */
  @Patch(':id')
  @ApiOperation({ summary: '更新文章（部分字段）' })
  @ApiParam({ name: 'id', description: '文章 ID', example: 1 })
  @ApiBody({ description: '需要更新的字段（全部可选）', type: UpdateArticleDto })
  @ApiOkResponse({
    description: '更新成功，返回更新后的文章',
    type: ArticleResponseDto,
  })
  @ApiNotFoundResponse({ description: '文章不存在' })
  @ApiBadRequestResponse({ description: '请求参数校验失败' })
  update(
    @Param('id', ParseIntPipe) id: number,
    @Body() dto: UpdateArticleDto,
  ) {
    return this.articlesService.update(id, dto);
  }

  /**
   * DELETE /articles/:id
   *
   * @HttpCode(204) 让响应没有 body，符合 RESTful 习惯。
   * 因此 @ApiResponse 也不需要 type。
   */
  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiOperation({ summary: '删除文章' })
  @ApiParam({ name: 'id', description: '文章 ID', example: 1 })
  @ApiNotFoundResponse({ description: '文章不存在' })
  @ApiUnauthorizedResponse({ description: '未登录或无权限' })
  remove(@Param('id', ParseIntPipe) id: number) {
    return this.articlesService.remove(id);
  }

  /**
   * POST /articles/:id/publish
   *
   * 演示 @ApiBody 接收一个独立的 DTO（PublishArticleDto）。
   * 同时演示一个"动作型"接口（不是 CRUD）的文档化方式。
   */
  @Post(':id/publish')
  @ApiOperation({
    summary: '发布文章',
    description: '把文章状态从 draft 改为 published，需要管理员权限。',
  })
  @ApiParam({ name: 'id', description: '文章 ID', example: 3 })
  @ApiBody({ type: PublishArticleDto })
  @ApiOkResponse({
    description: '发布成功',
    type: ArticleResponseDto,
  })
  @ApiNotFoundResponse({ description: '文章不存在' })
  @ApiUnauthorizedResponse({ description: '无管理员权限' })
  publish(
    @Param('id', ParseIntPipe) id: number,
    @Body() body: PublishArticleDto,
  ) {
    // 这里只做文档演示，实际逻辑直接复用 update
    return this.articlesService.update(id, {
      status: ArticleStatus.PUBLISHED,
    });
  }
}
