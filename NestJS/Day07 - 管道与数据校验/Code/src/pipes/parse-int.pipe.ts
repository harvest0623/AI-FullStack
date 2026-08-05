import {
  PipeTransform,
  Injectable,
  ArgumentMetadata,
  BadRequestException,
} from '@nestjs/common';

/**
 * 自定义 ParseIntPipe（教学用）
 *
 * 这是内置 ParseIntPipe 的极简复刻版，用于演示 PipeTransform 接口的工作机制：
 *   1. 实现 PipeTransform<string, number>，输入 string，输出 number。
 *   2. transform 方法接收 (value, metadata)：
 *      - value 是路径参数字符串，如 "123" 或 "abc"。
 *      - metadata.data 是参数名，如 @Param('id') 的 'id'，用于生成可读的错误信息。
 *   3. 转换失败时抛 BadRequestException（HTTP 400），NestJS 会自动捕获并格式化响应。
 *
 * 内置 ParseIntPipe 还处理了 Infinity、非字符串输入、自定义异常工厂等边界情况，
 * 生产环境请直接使用内置 ParseIntPipe。
 *
 * 使用方式见 src/users/users.controller.ts 的 GET /users/custom/:id 路由：
 *   @Param('id', CustomParseIntPipe) id: number
 */
@Injectable()
export class CustomParseIntPipe implements PipeTransform<string, number> {
  transform(value: string, metadata: ArgumentMetadata): number {
    // parseInt 第二个参数指定基数 10，避免 "08" 被当作八进制
    const val = parseInt(value, 10);

    // NaN 说明输入不是合法数字
    if (isNaN(val)) {
      throw new BadRequestException(
        `参数 "${metadata.data}" 必须是整数，但收到: "${value}"`,
      );
    }

    return val;
  }
}
