import { ApiProperty } from '@nestjs/swagger';

/**
 * 统一响应 DTO
 *
 * 设计意图：
 *   后端接口返回给前端的统一信封格式。无论成功还是失败，前端都能用同一套
 *   解析逻辑处理：先看 success，再取 data 或 error。
 *
 * 为什么用泛型 <T>：
 *   data 的具体结构因接口而异（文章、用户、订单...）。用泛型让 TypeScript
 *   在编译期检查调用方传入的响应 DTO 类型，同时 Swagger 也能基于泛型参数
 *   生成对应的 schema。
 *
 * 注意：这个类只用于"响应文档化"和"代码类型约束"，不参与请求校验。
 * 因为响应不会经过 ValidationPipe，class-validator 装饰器在这里不必要。
 */
export class ApiResponseDto<T> {
  @ApiProperty({
    description: '业务是否成功',
    example: true,
  })
  success: boolean;

  @ApiProperty({
    description: '业务数据，失败时为 null',
    example: { id: 1, title: 'Hello NestJS' },
  })
  data: T | null;

  @ApiProperty({
    description: '提示信息，成功时可省略，失败时面向用户',
    example: '操作成功',
  })
  message?: string;

  @ApiProperty({
    description: '响应时间戳（ISO 字符串），便于排查',
    example: '2025-07-26T08:00:00.000Z',
  })
  timestamp: string;
}
