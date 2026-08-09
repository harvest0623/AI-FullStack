import { ApiProperty } from '@nestjs/swagger';
import { OmitType } from '@nestjs/mapped-types';
import { ArticleStatus } from './create-article.dto';

/**
 * 文章响应 DTO
 *
 * 为什么需要响应 DTO？
 *   Entity（数据库模型）通常包含内部字段（如 authorId、isDeleted、createdAt），
 *   不希望暴露给前端。响应 DTO 通过 OmitType / PickType 派生自"完整模型"，
 *   只暴露前端需要的字段。
 *
 * OmitType(CreateArticleDto, ['authorId']) 的作用：
 *   以 CreateArticleDto 为基础，移除 authorId 字段，得到一个新类。
 *   派生类自动继承所有装饰器，Swagger 文档会基于此生成响应 schema。
 *
 * 实际项目里通常会基于 Entity 而非 CreateDto 派生 ResponseDto。
 * 这里因为本项目用内存数据演示没有真正的 Entity，所以从 CreateDto 派生。
 * 关键是演示"派生 + 加字段"的思路。
 */
export class ArticleResponseDto extends OmitType(CreateArticleDto, [
  'authorId',
] as const) {
  @ApiProperty({
    description: '文章 ID',
    example: 1,
  })
  id: number;

  @ApiProperty({
    description: '文章状态',
    enum: ArticleStatus,
    example: ArticleStatus.PUBLISHED,
  })
  status: ArticleStatus;

  @ApiProperty({
    description: '创建时间（ISO 字符串）',
    example: '2025-07-26T08:00:00.000Z',
  })
  createdAt: string;

  @ApiProperty({
    description: '更新时间（ISO 字符串）',
    example: '2025-07-26T08:30:00.000Z',
  })
  updatedAt: string;
}

/**
 * 文章列表响应 DTO（包含分页元信息）
 *
 * 用于 GET /articles 的响应文档化。
 * 前端拿到后能从 total 知道总数，进而渲染分页器。
 */
export class ArticleListResponseDto {
  @ApiProperty({
    description: '当前页码',
    example: 1,
  })
  page: number;

  @ApiProperty({
    description: '每页条数',
    example: 10,
  })
  pageSize: number;

  @ApiProperty({
    description: '符合条件的总条数',
    example: 42,
  })
  total: number;

  @ApiProperty({
    description: '文章列表',
    type: [ArticleResponseDto],
    example: [
      {
        id: 1,
        title: 'NestJS Swagger 入门',
        content: '...',
        status: 'published',
        createdAt: '2025-07-26T08:00:00.000Z',
        updatedAt: '2025-07-26T08:00:00.000Z',
      },
    ],
  })
  list: ArticleResponseDto[];
}
