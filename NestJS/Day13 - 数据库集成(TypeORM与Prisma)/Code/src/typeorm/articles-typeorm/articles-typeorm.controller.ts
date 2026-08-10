import {
  Controller,
  Get,
  Post,
  Patch,
  Delete,
  Body,
  Param,
  ParseIntPipe,
  HttpCode,
  HttpStatus,
} from '@nestjs/common';
import {
  ArticlesTypeormService,
  CreateArticleDto,
  UpdateArticleDto,
} from './articles-typeorm.service';

/**
 * TypeORM 版 Articles Controller
 *
 * 路由前缀：/api/v1/typeorm/articles（全局前缀 + 此处 @Controller）
 *
 * 与 prisma 版完全对齐，方便对比同一业务在两种范式下的代码差异。
 */
@Controller('typeorm/articles')
export class ArticlesTypeormController {
  constructor(private readonly service: ArticlesTypeormService) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  create(@Body() dto: CreateArticleDto) {
    return this.service.create(dto);
  }

  @Get()
  findAll() {
    return this.service.findAll();
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
