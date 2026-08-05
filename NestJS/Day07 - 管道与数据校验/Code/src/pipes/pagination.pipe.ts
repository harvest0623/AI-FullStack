import {
  PipeTransform,
  Injectable,
  ArgumentMetadata,
} from '@nestjs/common';

/**
 * 分页参数转换结果
 *
 * - page:     当前页码（从 1 开始）
 * - pageSize: 每页条数
 * - skip:     数据库偏移量，等价于 (page - 1) * pageSize，直接传给 TypeORM 的 skip()
 * - take:     数据库取数上限，等价于 pageSize，直接传给 TypeORM 的 take()
 */
export interface PaginationOptions {
  page: number;
  pageSize: number;
  skip: number;
  take: number;
}

/**
 * PaginationPipe：把散落的 page / pageSize 查询参数转换成结构化的分页对象
 *
 * 设计要点：
 *   1. 通过 metadata.type === 'query' 过滤，只处理查询参数。
 *   2. page 默认 1，最小 1；pageSize 默认 10，范围 1~100。
 *   3. 自动计算 skip / take，控制器拿到后可直接传给数据库查询。
 *
 * 使用方式见 src/articles/articles.controller.ts 的 GET /articles/paginated 路由：
 *   @Get('paginated')
 *   @UsePipes(new PaginationPipe())
 *   findPaginated(@Query() pagination: PaginationOptions) { ... }
 *
 * 这里通过方法级 @UsePipes 挂载，演示 Pipe 的方法级应用层级。
 * PaginationOptions 是 interface（运行时不存在），因此全局 ValidationPipe 不会尝试校验它。
 */
@Injectable()
export class PaginationPipe implements PipeTransform<any, PaginationOptions> {
  transform(value: any, metadata: ArgumentMetadata): PaginationOptions {
    // 只处理查询参数
    if (metadata.type !== 'query') {
      return value;
    }

    // 解析 page，默认 1，最小 1
    const page = Math.max(1, parseInt(value?.page, 10) || 1);

    // 解析 pageSize，默认 10，范围 1~100（防止恶意请求超大 pageSize 拖垮数据库）
    const pageSize = Math.min(100, Math.max(1, parseInt(value?.pageSize, 10) || 10));

    return {
      page,
      pageSize,
      skip: (page - 1) * pageSize,
      take: pageSize,
    };
  }
}
