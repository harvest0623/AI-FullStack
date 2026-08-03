/**
 * 创建文章 DTO
 *
 * Day02 阶段只做简单类型约束，
 * class-validator 装饰器（@IsString、@IsInt 等）会在 Day07 引入。
 * 当前通过 TypeScript 类型为后续校验做铺垫，
 * 控制器层会使用此类型作为 @Body() 的目标类型。
 */
export class CreateArticleDto {
  title: string;
  content: string;
  author: string;
  tags?: string[];
}

/**
 * 更新文章 DTO
 *
 * PartialType 在 Day07 引入，这里手动声明为可选字段。
 */
export class UpdateArticleDto {
  title?: string;
  content?: string;
  author?: string;
  tags?: string[];
}
