import {
  IsInt,
  IsOptional,
  IsString,
  IsEnum,
  Min,
  Max,
} from 'class-validator';
import { Type } from 'class-transformer';

/**
 * 排序字段枚举
 */
export enum SortField {
  CREATED_AT = 'createdAt',
  UPDATED_AT = 'updatedAt',
  TITLE = 'title',
}

/**
 * 排序方向枚举
 */
export enum SortOrder {
  ASC = 'asc',
  DESC = 'desc',
}

/**
 * 文章查询 DTO
 *
 * 用于 GET /articles 的查询参数校验。
 *
 * 关键点：
 *   1. @Type(() => Number) + @IsInt：把查询参数的字符串 "2" 转成数字 2 并校验为整数。
 *      （main.ts 中 ValidationPipe 开启了 transform: true + enableImplicitConversion: true，
 *       实际上 @Type 可以省略，但显式声明更清晰、更可控。）
 *   2. @Min / @Max：限制 page >= 1，1 <= pageSize <= 100。
 *   3. @IsEnum：sort / order 必须是枚举成员，传入非法值会被拒绝。
 *   4. @IsOptional：所有字段都可选，缺省时由控制器或服务层提供默认值。
 *
 * 与 PaginationPipe 的区别：
 *   QueryArticleDto 侧重"校验查询参数合法性"（page 是不是整数、sort 是不是合法枚举）。
 *   PaginationPipe 侧重"转换分页参数结构"（算出 skip / take）。
 *   本章在 GET /articles 用 QueryArticleDto，在 GET /articles/paginated 用 PaginationPipe。
 */
export class QueryArticleDto {
  /** 关键词搜索：可选字符串 */
  @IsOptional()
  @IsString()
  keyword?: string;

  /** 当前页码：可选，最小 1 */
  @IsOptional()
  @Type(() => Number)
  @IsInt({ message: 'page 必须是整数' })
  @Min(1, { message: 'page 最小为 1' })
  page?: number;

  /** 每页条数：可选，范围 1~100 */
  @IsOptional()
  @Type(() => Number)
  @IsInt({ message: 'pageSize 必须是整数' })
  @Min(1, { message: 'pageSize 最小为 1' })
  @Max(100, { message: 'pageSize 最大为 100' })
  pageSize?: number;

  /** 排序字段：必须是 SortField 枚举成员 */
  @IsOptional()
  @IsEnum(SortField, {
    message: 'sort 必须是 createdAt / updatedAt / title 之一',
  })
  sort?: SortField;

  /** 排序方向：必须是 SortOrder 枚举成员 */
  @IsOptional()
  @IsEnum(SortOrder, { message: 'order 必须是 asc 或 desc' })
  order?: SortOrder;

  /** 按标签筛选：可选字符串 */
  @IsOptional()
  @IsString()
  tag?: string;
}
