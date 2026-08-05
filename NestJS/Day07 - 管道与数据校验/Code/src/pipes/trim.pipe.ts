import {
  PipeTransform,
  Injectable,
  ArgumentMetadata,
} from '@nestjs/common';

/**
 * TrimPipe：递归去除请求体中所有字符串字段的两端空格
 *
 * 设计要点：
 *   1. 通过 metadata.type 过滤，只处理 body 类型，不影响路径参数和查询参数。
 *   2. 递归遍历对象与数组，对所有 string 类型的值调用 trim()。
 *   3. 返回新对象而非修改原对象，避免副作用。
 *
 * 注册方式：通过 APP_PIPE 注册为全局管道（见 app.module.ts）。
 * 这样所有控制器的 @Body() 都会自动净化字符串空格，控制器无需感知此逻辑。
 *
 * 执行时机说明：
 *   TrimPipe 通过 APP_PIPE 注册，与 main.ts 中 useGlobalPipes 注册的 ValidationPipe 共存。
 * 当两者同时存在时，建议关注执行顺序：理想情况下应先 trim 再 validate，
 * 如果顺序不符合预期，可以把两个 Pipe 都放在同一个注册位置（如都用 useGlobalPipes 或都用 APP_PIPE）。
 */
@Injectable()
export class TrimPipe implements PipeTransform {
  transform(value: any, metadata: ArgumentMetadata) {
    // 只处理请求体，路径参数和查询参数保持原样
    if (metadata.type !== 'body') {
      return value;
    }

    // null / undefined 直接返回
    if (value === null || value === undefined) {
      return value;
    }

    return this.trimDeep(value);
  }

  /**
   * 递归 trim 字符串
   * - string: 直接 trim
   * - Array: 对每个元素递归
   * - Object: 对每个属性值递归，返回新对象
   * - 其他类型（number / boolean / Date）: 原样返回
   */
  private trimDeep(value: any): any {
    if (typeof value === 'string') {
      return value.trim();
    }

    if (Array.isArray(value)) {
      return value.map((item) => this.trimDeep(item));
    }

    if (typeof value === 'object') {
      const result: Record<string, any> = {};
      for (const key of Object.keys(value)) {
        result[key] = this.trimDeep(value[key]);
      }
      return result;
    }

    return value;
  }
}
