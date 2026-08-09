import { ApiPropertyOptional } from '@nestjs/swagger';
import { IntersectionType } from '@nestjs/mapped-types';
import { IsEnum, IsOptional, IsString } from 'class-validator';

import { PaginationDto } from '../../common/pagination.dto';
import { ArticleStatus } from './create-article.dto';

/**
 * 文章排序字段枚举
 *
 * 枚举不仅用于校验，也用于 Swagger 文档展示合法值。
 * 比给前端写"sort 只能传 createdAt / updatedAt / title"的注释强多了。
 */
export enum ArticleSortField {
  CREATED_AT = 'createdAt',
  TITLE = 'title',
  READ_TIME = 'readTime',
}

/**
 * 排序方向
 */
export enum SortOrder {
  ASC = 'asc',
  DESC = 'desc',
}

/**
 * 文章查询 DTO（分页查询的文档化示例）
 *
 * IntersectionType(PaginationDto, class { ... }) 的作用：
 *   把两个类的字段"合并"为一个新类，相当于多继承。
 *   - PaginationDto 提供 page / pageSize
 *   - 本类提供 keyword / status / sort / order
 *   合并后既有分页字段又有过滤字段，Swagger 文档也会一并展示。
 *
 * 这样 PaginationDto 可以被多个资源（articles / users / orders）复用，
 * 每个资源只需要在自己的 QueryDto 里补充专属字段即可。
 */
export class QueryArticleDto extends IntersectionType(
  PaginationDto,
  class {
    @ApiPropertyOptional({
      description: '关键词搜索（标题或正文包含）',
      example: 'NestJS',
    })
    @IsOptional()
    @IsString()
    keyword?: string;

    @ApiPropertyOptional({
      description: '按文章状态过滤',
      enum: ArticleStatus,
      example: ArticleStatus.PUBLISHED,
    })
    @IsOptional()
    @IsEnum(ArticleStatus, {
      message: 'status 必须是 draft / published / archived 之一',
    })
    status?: ArticleStatus;

    @ApiPropertyOptional({
      description: '排序字段',
      enum: ArticleSortField,
      default: ArticleSortField.CREATED_AT,
      example: ArticleSortField.CREATED_AT,
    })
    @IsOptional()
    @IsEnum(ArticleSortField, {
      message: 'sort 必须是 createdAt / title / readTime 之一',
    })
    sort?: ArticleSortField;

    @ApiPropertyOptional({
      description: '排序方向',
      enum: SortOrder,
      default: SortOrder.DESC,
      example: SortOrder.DESC,
    })
    @IsOptional()
    @IsEnum(SortOrder, { message: 'order 必须是 asc 或 desc' })
    order?: SortOrder;
  },
) {}
