import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import {
  IsArray,
  IsEnum,
  IsInt,
  IsString,
  MaxLength,
  MinLength,
  Min,
  Max,
  IsOptional,
} from 'class-validator';
import { Type } from 'class-transformer';

/**
 * 文章状态枚举
 *
 * Swagger 在文档里会展示枚举的所有合法值，前端工程师一眼就能看到
 * 哪些 status 可以传，比看注释直观得多。
 */
export enum ArticleStatus {
  DRAFT = 'draft',
  PUBLISHED = 'published',
  ARCHIVED = 'archived',
}

/**
 * 创建文章 DTO（请求契约）
 *
 * 这个类同时承担两个角色：
 *   1. 请求校验契约：class-validator 装饰器告诉 ValidationPipe 该怎么校验
 *   2. API 文档契约：@ApiProperty 装饰器告诉 Swagger 该字段长什么样
 *
 * 同一份装饰器，既驱动运行时校验，又驱动文档生成——这就是"代码即文档"。
 *
 * 与 Day07 的呼应：
 *   Day07 重点在 class-validator 校验装饰器本身，本章重点是给每个字段补全
 *   @ApiProperty，让 DTO 同时成为 API 文档的来源。
 */
export class CreateArticleDto {
  @ApiProperty({
    description: '文章标题，3~100 字符',
    example: 'NestJS Swagger 入门指南',
    minLength: 3,
    maxLength: 100,
  })
  @IsString({ message: 'title 必须是字符串' })
  @MinLength(3, { message: '标题至少 3 个字符' })
  @MaxLength(100, { message: '标题最多 100 个字符' })
  title: string;

  @ApiProperty({
    description: '文章正文，至少 10 字符',
    example: '本文介绍如何在 NestJS 中集成 Swagger...',
    minLength: 10,
  })
  @IsString()
  @MinLength(10, { message: '内容至少 10 个字符' })
  content: string;

  @ApiProperty({
    description: '作者 ID，必须是正整数',
    example: 1,
    minimum: 1,
  })
  @Type(() => Number)
  @IsInt({ message: 'authorId 必须是整数' })
  @Min(1, { message: 'authorId 必须为正整数' })
  authorId: number;

  @ApiPropertyOptional({
    description: '文章状态，默认 draft',
    enum: ArticleStatus,
    default: ArticleStatus.DRAFT,
    example: ArticleStatus.DRAFT,
  })
  @IsOptional()
  @IsEnum(ArticleStatus, {
    message: 'status 必须是 draft / published / archived 之一',
  })
  status?: ArticleStatus = ArticleStatus.DRAFT;

  @ApiPropertyOptional({
    description: '文章标签，字符串数组',
    type: [String],
    example: ['NestJS', 'Swagger', 'DTO'],
  })
  @IsOptional()
  @IsArray({ message: 'tags 必须是数组' })
  @IsString({ each: true, message: 'tags 中每个元素必须是字符串' })
  tags?: string[];

  @ApiPropertyOptional({
    description: '预计阅读时长（分钟），0~1000',
    example: 5,
    minimum: 0,
    maximum: 1000,
  })
  @IsOptional()
  @Type(() => Number)
  @IsInt({ message: 'readTime 必须是整数' })
  @Min(0, { message: 'readTime 不能为负' })
  @Max(1000, { message: 'readTime 不能超过 1000' })
  readTime?: number;
}
