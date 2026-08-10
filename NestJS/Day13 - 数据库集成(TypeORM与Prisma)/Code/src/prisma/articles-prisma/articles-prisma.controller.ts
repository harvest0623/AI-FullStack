import {
  Controller,
  Get,
  Post,
  Patch,
  Delete,
  Body,
  Param,
  Query,
  ParseIntPipe,
  HttpCode,
  HttpStatus,
} from '@nestjs/common';
import {
  ArticlesPrismaService,
  CreateArticleDto,
  UpdateArticleDto,
} from './articles-prisma.service';

/**
 * Prisma 版 Articles Controller
 *
 * 路由前缀：/api/v1/prisma/articles
 *
 * 与 TypeORM 版完全对齐业务，方便对比同一业务在两种范式下的代码差异。
 */
@Controller('prisma/articles')
export class ArticlesPrismaController {
  constructor(private readonly service: ArticlesPrismaService) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  create(@Body() dto: CreateArticleDto) {
    return this.service.create(dto);
  }

  @Get()
  findAll() {
    return this.service.findAll();
  }

  @Get('search')
  findByAuthorEmail(@Query('email') email: string) {
    return this.service.findByAuthorEmail(email);
  }

  @Get(':id')
  findOne(@Param('id', ParseIntPipe) id: number) {
    return this.service.findOne(id);
  }

  @Patch(':id')
  update(
    @Param('id', ParseIntPipe) id: number,
    @Body() dto: UpdateArticleDto,
  ) {
    return this.service.update(id, dto);
  }

  @Delete(':id')
  @HttpCode(HttpStatus.OK)
  remove(@Param('id', ParseIntPipe) id: number) {
    return this.service.remove(id);
  }

  @Post(':id/view')
  incrementView(@Param('id', ParseIntPipe) id: number) {
    return this.service.incrementView(id);
  }
}
