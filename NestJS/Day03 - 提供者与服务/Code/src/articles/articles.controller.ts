// ============================================================
// ArticlesController：路由与请求响应映射
// ------------------------------------------------------------
// 演示要点：
//   1. 控制器只做 HTTP 映射，业务逻辑下沉到 ArticlesService
//   2. 构造函数注入 ArticlesService（类作为 Token）
// ============================================================

import {
  Body,
  Controller,
  Delete,
  Get,
  Param,
  ParseIntPipe,
  Post,
} from '@nestjs/common';
import { Article, ArticlesService } from './articles.service';

@Controller('articles')
export class ArticlesController {
  // 构造函数注入 ArticlesService
  constructor(private readonly articlesService: ArticlesService) {}

  @Get()
  findAll(): Article[] {
    return this.articlesService.findAll();
  }

  @Get(':id')
  findOne(@Param('id', ParseIntPipe) id: number): Article | null {
    return this.articlesService.findOne(id);
  }

  @Post()
  create(
    @Body('title') title: string,
    @Body('content') content: string,
  ): Article {
    return this.articlesService.create(title, content);
  }

  @Delete(':id')
  remove(@Param('id', ParseIntPipe) id: number): { success: boolean } {
    return { success: this.articlesService.remove(id) };
  }
}
