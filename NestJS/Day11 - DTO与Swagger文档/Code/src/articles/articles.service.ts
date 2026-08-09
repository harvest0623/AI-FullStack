import { Injectable, NotFoundException } from '@nestjs/common';

import { CreateArticleDto, ArticleStatus } from './dto/create-article.dto';
import { UpdateArticleDto } from './dto/update-article.dto';
import { QueryArticleDto, ArticleSortField, SortOrder } from './dto/query-article.dto';
import { ArticleResponseDto } from './dto/article-response.dto';
import { calcOffset } from '../common/pagination.dto';

/**
 * 文章服务（内存数据演示）
 *
 * 本服务的核心职责：
 *   1. 接收 Controller 传入的 DTO（已经是 ValidationPipe 校验过的实例）
 *   2. 把 DTO 转换成内部数据模型（Entity 雏形），存进内存数组
 *   3. 把内部模型转换回响应 DTO，返回给 Controller
 *
 * DTO ↔ Entity 的转换就在这里发生。即便本项目没有真正的 Entity，
 * 你也能看到 Service 在做"加 id、加 createdAt、隐藏内部字段"这种工作。
 */
@Injectable()
export class ArticlesService {
  private articles: Array<{
    id: number;
    title: string;
    content: string;
    authorId: number;
    status: ArticleStatus;
    tags: string[];
    readTime: number;
    createdAt: string;
    updatedAt: string;
  }> = [
    {
      id: 1,
      title: 'NestJS 入门指南',
      content: 'NestJS 是一个用于构建高效、可扩展的 Node.js 服务端应用的框架...',
      authorId: 1,
      status: ArticleStatus.PUBLISHED,
      tags: ['NestJS', '后端'],
      readTime: 8,
      createdAt: '2025-07-20T08:00:00.000Z',
      updatedAt: '2025-07-20T08:00:00.000Z',
    },
    {
      id: 2,
      title: 'DTO 与数据契约',
      content: 'DTO 是 Data Transfer Object 的缩写，主要用于在层与层之间传递数据...',
      authorId: 1,
      status: ArticleStatus.PUBLISHED,
      tags: ['DTO', '架构'],
      readTime: 5,
      createdAt: '2025-07-22T08:00:00.000Z',
      updatedAt: '2025-07-22T08:00:00.000Z',
    },
    {
      id: 3,
      title: 'Swagger 实战笔记（草稿）',
      content: '本文记录 Swagger 集成的常见踩坑，包括枚举文档化、嵌套对象、Bearer 认证...',
      authorId: 2,
      status: ArticleStatus.DRAFT,
      tags: ['Swagger', '文档'],
      readTime: 12,
      createdAt: '2025-07-25T08:00:00.000Z',
      updatedAt: '2025-07-25T08:00:00.000Z',
    },
  ];

  private nextId = 4;

  /**
   * 分页 + 过滤 + 排序查询
   */
  findAll(query: QueryArticleDto): {
    page: number;
    pageSize: number;
    total: number;
    list: ArticleResponseDto[];
  } {
    const { page, pageSize, skip, take } = calcOffset(query);

    let list = [...this.articles];

    // 关键词过滤
    if (query.keyword) {
      const kw = query.keyword.toLowerCase();
      list = list.filter(
        (a) =>
          a.title.toLowerCase().includes(kw) ||
          a.content.toLowerCase().includes(kw),
      );
    }

    // 状态过滤
    if (query.status) {
      list = list.filter((a) => a.status === query.status);
    }

    // 排序
    const sortField = query.sort ?? ArticleSortField.CREATED_AT;
    const order = query.order ?? SortOrder.DESC;
    list.sort((a, b) => {
      let cmp = 0;
      if (sortField === ArticleSortField.TITLE) {
        cmp = a.title.localeCompare(b.title);
      } else if (sortField === ArticleSortField.READ_TIME) {
        cmp = a.readTime - b.readTime;
      } else {
        // createdAt 默认
        cmp = a.createdAt.localeCompare(b.createdAt);
      }
      return order === SortOrder.ASC ? cmp : -cmp;
    });

    const total = list.length;
    const paged = list.slice(skip, skip + take);

    return {
      page,
      pageSize,
      total,
      list: paged.map(this.toResponse),
    };
  }

  /**
   * 单个查询，找不到抛 404
   */
  findOne(id: number): ArticleResponseDto {
    const article = this.articles.find((a) => a.id === id);
    if (!article) {
      throw new NotFoundException(`文章 ${id} 不存在`);
    }
    return this.toResponse(article);
  }

  /**
   * 创建：把 CreateArticleDto 转换成内部模型，存库后返回响应 DTO
   */
  create(dto: CreateArticleDto): ArticleResponseDto {
    const now = new Date().toISOString();
    const article = {
      id: this.nextId++,
      title: dto.title,
      content: dto.content,
      authorId: dto.authorId,
      status: dto.status ?? ArticleStatus.DRAFT,
      tags: dto.tags ?? [],
      readTime: dto.readTime ?? 0,
      createdAt: now,
      updatedAt: now,
    };
    this.articles.push(article);
    return this.toResponse(article);
  }

  /**
   * 更新：先找到记录，应用 DTO 中的部分字段，更新 updatedAt
   */
  update(id: number, dto: UpdateArticleDto): ArticleResponseDto {
    const index = this.articles.findIndex((a) => a.id === id);
    if (index === -1) {
      throw new NotFoundException(`文章 ${id} 不存在`);
    }
    const updated = {
      ...this.articles[index],
      ...dto,
      updatedAt: new Date().toISOString(),
    };
    this.articles[index] = updated;
    return this.toResponse(updated);
  }

  /**
   * 删除
   */
  remove(id: number): { id: number; deleted: boolean } {
    const index = this.articles.findIndex((a) => a.id === id);
    if (index === -1) {
      throw new NotFoundException(`文章 ${id} 不存在`);
    }
    this.articles.splice(index, 1);
    return { id, deleted: true };
  }

  /**
   * Entity → Response DTO 的转换
   *
   * 这里用解构把 authorId 显式剥离，模拟"响应 DTO 隐藏内部字段"的场景。
   * 真实项目里通常用 class-transformer 的 plainToInstance + @Exclude 实现。
   */
  private toResponse(article: {
    id: number;
    title: string;
    content: string;
    authorId: number;
    status: ArticleStatus;
    tags: string[];
    readTime: number;
    createdAt: string;
    updatedAt: string;
  }): ArticleResponseDto {
    // 故意省略 authorId，呼应 ArticleResponseDto extends OmitType(..., ['authorId'])
    const { authorId: _omit, ...rest } = article;
    return {
      ...rest,
      status: article.status,
    } as ArticleResponseDto;
  }
}
