/**
 * 文章查询 DTO
 *
 * 用于规范 GET /articles 的查询参数类型。
 * 在 Day07 接入 class-validator 后，
 * 会通过 @IsInt、@IsOptional、@Type 等装饰器做严格校验。
 */
export class QueryArticleDto {
  /** 关键词搜索 */
  keyword?: string;

  /** 当前页码，默认 1 */
  page?: number;

  /** 每页条数，默认 10 */
  pageSize?: number;

  /** 排序字段 */
  sort?: 'createdAt' | 'updatedAt' | 'title';

  /** 排序方向 */
  order?: 'asc' | 'desc';

  /** 按标签筛选 */
  tag?: string;
}
