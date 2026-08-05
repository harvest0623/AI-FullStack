import {
  registerDecorator,
  ValidationOptions,
  ValidationArguments,
} from 'class-validator';

/**
 * 自定义校验装饰器集合
 *
 * class-validator 内置的装饰器（@IsString、@IsEmail 等）覆盖了通用场景，
 * 但业务规则（如"日期必须晚于当前时间"、"字符串不能全空白"）需要自定义。
 *
 * 自定义装饰器通过 registerDecorator 注册，底层机制与内置装饰器完全一致：
 *   1. 装饰器在类定义时被调用，把校验规则注册到 class-validator 的元数据中。
 *   2. ValidationPipe 实例化 DTO 后，class-validator 遍历所有规则逐字段执行。
 *   3. 校验失败时，错误信息会汇入 ValidationPipe 抛出的 BadRequestException。
 */

/**
 * @IsAfterNow
 *
 * 校验日期值必须严格晚于当前时间。
 * 同时接受 Date 对象与可被 new Date() 解析的字符串。
 *
 * @example
 * ```ts
 * @IsAfterNow({ message: '发布时间必须晚于当前时间' })
 * @Type(() => Date)
 * publishAt: Date;
 * ```
 */
export function IsAfterNow(validationOptions?: ValidationOptions) {
  return function (object: Object, propertyName: string) {
    registerDecorator({
      name: 'isAfterNow',
      target: object.constructor,
      propertyName: propertyName,
      options: validationOptions,
      validator: {
        validate(value: any, _args: ValidationArguments) {
          // 同时兼容 Date 实例与字符串/时间戳
          const date = value instanceof Date ? value : new Date(value);
          // 无效日期直接判失败
          if (isNaN(date.getTime())) {
            return false;
          }
          return date.getTime() > Date.now();
        },
        defaultMessage(args: ValidationArguments) {
          return `${args.property} 必须晚于当前时间`;
        },
      },
    });
  };
}

/**
 * @IsNotBlank
 *
 * 校验字符串不能为 null、undefined、空字符串或纯空白字符。
 * 与 @IsNotEmpty 的区别：@IsNotEmpty 只检查长度 > 0，"   " 也能通过；
 * @IsNotBlank 会先 trim 再判断，纯空白字符串会被拒绝。
 *
 * @example
 * ```ts
 * @IsNotBlank({ message: '用户名不能为空白' })
 * username: string;
 * ```
 */
export function IsNotBlank(validationOptions?: ValidationOptions) {
  return function (object: Object, propertyName: string) {
    registerDecorator({
      name: 'isNotBlank',
      target: object.constructor,
      propertyName: propertyName,
      options: validationOptions,
      validator: {
        validate(value: any, _args: ValidationArguments) {
          return typeof value === 'string' && value.trim().length > 0;
        },
        defaultMessage(args: ValidationArguments) {
          return `${args.property} 不能为空或纯空白字符`;
        },
      },
    });
  };
}
