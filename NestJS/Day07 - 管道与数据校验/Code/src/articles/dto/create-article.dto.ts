import {
  IsString,
  IsInt,
  IsEmail,
  IsOptional,
  IsEnum,
  IsArray,
  IsDate,
  IsNotEmpty,
  MinLength,
  MaxLength,
  Min,
  Max,
  ValidateNested,
} from 'class-validator';
import { Type } from 'class-transformer';
import { IsAfterNow } from '../../common/custom-validators';

/**
 * 文章状态枚举
 *
 * @IsEnum 会校验传入值是否是该枚举的成员之一。
 * 传入 "draft" / "published" / "archived" 通过，传入 "deleted" 报错。
 */
export enum ArticleStatus {
  DRAFT = 'draft',
  PUBLISHED = 'published',
  ARCHIVED = 'archived',
}

/**
 * 文章元信息 DTO（嵌套对象示例）
 *
 * 用于演示 @ValidateNested + @Type 的嵌套校验。
 * 嵌套 DTO 必须自身也有 class-validator 装饰器，否则校验不会递归进入。
 */
export class ArticleMetaDto {
  @IsString()
  @MinLength(1, { message: 'meta.key 不能为空' })
  key: string;

  @IsString()
  @IsNotEmpty({ message: 'meta.value 不能为空' })
  value: string;
}

/**
 * 创建文章 DTO
 *
 * 本 DTO 演示 class-validator 的全部常用装饰器：
 *   @IsString @IsInt @IsEmail @IsOptional @IsEnum
 *   @MinLength @MaxLength @Min @Max
 *   @IsArray @IsDate @IsNotEmpty
 *   @ValidateNested + @Type（嵌套对象）
 *   @IsAfterNow（自定义校验装饰器）
 *
 * 配合 main.ts 中全局注册的 ValidationPipe（whitelist + forbidNonWhitelisted + transform），
 * 所有字段会被自动校验，多余字段会被拒绝，类型会被自动转换。
 */
export class CreateArticleDto {
  // ============ 字符串类 ============

  /** 文章标题：3~100 字符 */
  @IsString({ message: 'title 必须是字符串' })
  @MinLength(3, { message: '标题至少 3 个字符' })
  @MaxLength(100, { message: '标题最多 100 个字符' })
  title: string;

  /** 文章内容：至少 10 字符 */
  @IsString()
  @MinLength(10, { message: '内容至少 10 个字符' })
  content: string;

  /** 作者邮箱：必须是合法邮箱格式 */
  @IsEmail({}, { message: 'authorEmail 邮箱格式不正确' })
  authorEmail: string;

  // ============ 可选字段 ============

  /** 作者名称：可选字符串 */
  @IsOptional()
  @IsString()
  author?: string;

  // ============ 枚举类 ============

  /** 文章状态：必须是 ArticleStatus 枚举成员 */
  @IsOptional()
  @IsEnum(ArticleStatus, {
    message: 'status 必须是 draft / published / archived 之一',
  })
  status?: ArticleStatus;

  // ============ 数组类 ============

  /** 标签列表：必须是字符串数组，每个元素都是字符串 */
  @IsOptional()
  @IsArray({ message: 'tags 必须是数组' })
  @IsString({ each: true, message: 'tags 中每个元素必须是字符串' })
  tags?: string[];

  // ============ 数字类 ============

  /** 预计阅读时长（分钟）：0~1000 的整数 */
  @IsOptional()
  @IsInt({ message: 'readTime 必须是整数' })
  @Min(0, { message: 'readTime 不能为负' })
  @Max(1000, { message: 'readTime 不能超过 1000' })
  readTime?: number;

  // ============ 日期类 + 自定义校验装饰器 ============

  /** 发布时间：必须是 Date 且晚于当前时间 */
  @IsOptional()
  @Type(() => Date)
  @IsDate({ message: 'publishAt 必须是合法日期' })
  @IsAfterNow({ message: 'publishAt 必须晚于当前时间' })
  publishAt?: Date;

  // ============ 嵌套对象 ============

  /** 元信息列表：嵌套对象数组，每个元素都会被 ArticleMetaDto 校验 */
  @IsOptional()
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => ArticleMetaDto)
  metadata?: ArticleMetaDto[];
}

/**
 * 更新文章 DTO
 *
 * PartialType 是 @nestjs/swagger 提供的工具，这里手写为全可选字段。
 * 所有字段都加了 @IsOptional()，允许部分更新时只传需要修改的字段。
 */
export class UpdateArticleDto {
  @IsOptional()
  @IsString()
  @MinLength(3)
  @MaxLength(100)
  title?: string;

  @IsOptional()
  @IsString()
  @MinLength(10)
  content?: string;

  @IsOptional()
  @IsEmail()
  authorEmail?: string;

  @IsOptional()
  @IsEnum(ArticleStatus)
  status?: ArticleStatus;

  @IsOptional()
  @IsArray()
  @IsString({ each: true })
  tags?: string[];
}
