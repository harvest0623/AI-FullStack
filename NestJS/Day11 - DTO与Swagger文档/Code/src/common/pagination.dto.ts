import { ApiPropertyOptional } from '@nestjs/swagger';
import { Type } from 'class-transformer';
import { IsInt, IsOptional, Max, Min } from 'class-validator';

/**
 * 分页基类 DTO（可复用）
 *
 * 设计意图：
 *   把"分页查询参数"封装为基类，所有需要分页的查询 DTO 都可以用 IntersectionType
 *   与之组合，避免在每个资源的 QueryDto 里重复声明 page / pageSize。
 *
 * 与 @Query 的配合：
 *   - 查询参数都是字符串，需要 @Type(() => Number) 显式转 number
 *   - 即便全局 ValidationPipe 开启了 enableImplicitConversion，显式声明依然更清晰
 *
 * 与 Swagger 的配合：
 *   - @ApiPropertyOptional 让该字段在文档里显示为"可选"
 *   - example / description 让文档更易读
 */
export class PaginationDto {
  @ApiPropertyOptional({
    description: '当前页码，从 1 开始计数',
    minimum: 1,
    default: 1,
    example: 1,
  })
  @IsOptional()
  @Type(() => Number)
  @IsInt({ message: 'page 必须是整数' })
  @Min(1, { message: 'page 最小为 1' })
  page?: number = 1;

  @ApiPropertyOptional({
    description: '每页条数，1~100 之间',
    minimum: 1,
    maximum: 100,
    default: 10,
    example: 10,
  })
  @IsOptional()
  @Type(() => Number)
  @IsInt({ message: 'pageSize 必须是整数' })
  @Min(1, { message: 'pageSize 最小为 1' })
  @Max(100, { message: 'pageSize 最大为 100' })
  pageSize?: number = 10;
}

/**
 * 计算分页偏移量的工具方法
 *
 * 数据库层（TypeORM / Prisma）通常需要 skip / take 而非 page / pageSize，
 * 这里在 Service 层调用此函数做转换，让控制器只关心 page / pageSize。
 */
export function calcOffset(pagination: PaginationDto): {
  page: number;
  pageSize: number;
  skip: number;
  take: number;
} {
  const page = pagination.page ?? 1;
  const pageSize = pagination.pageSize ?? 10;
  return {
    page,
    pageSize,
    skip: (page - 1) * pageSize,
    take: pageSize,
  };
}
