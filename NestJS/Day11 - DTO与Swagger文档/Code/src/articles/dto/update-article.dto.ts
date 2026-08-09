import { PartialType, OmitType } from '@nestjs/mapped-types';

import { CreateArticleDto } from './create-article.dto';

/**
 * 更新文章 DTO
 *
 * PartialType(OmitType(CreateArticleDto, ['authorId'])) 的两层派生：
 *   1. OmitType(CreateArticleDto, ['authorId'])
 *      以 CreateArticleDto 为基础，剔除 authorId 字段（更新时不允许改作者）
 *   2. PartialType(...)
 *      把剩余字段全部变成可选，便于"部分更新"场景（PATCH 语义）
 *
 * 派生类自动继承父类的所有装饰器：
 *   - class-validator 装饰器（@IsString @MinLength ...）→ PartialType 内部追加 @IsOptional
 *   - Swagger 装饰器（@ApiProperty）→ PartialType 内部转成 @ApiPropertyOptional
 *
 * 这就是"DTO 复用"的核心思想：CreateArticleDto → UpdateArticleDto 一行代码搞定，
 * 不会出现"加了字段忘了同步 UpdateDto"的脏数据问题。
 *
 * @nestjs/mapped-types 提供的全部派生工具：
 *   - PartialType  全部字段变可选（PATCH 用）
 *   - PickType     选取部分字段（如改密码 DTO 只需 password）
 *   - OmitType     剔除部分字段（如响应 DTO 隐藏 password）
 *   - IntersectionType  合并多个 DTO（如 QueryDto = Pagination + Filter）
 */
export class UpdateArticleDto extends PartialType(
  OmitType(CreateArticleDto, ['authorId'] as const),
) {}
