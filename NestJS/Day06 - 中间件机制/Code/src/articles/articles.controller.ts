import {
  Controller,
  Get,
  Post,
  Delete,
  Param,
  Req,
} from '@nestjs/common';
import { Request } from 'express';

// ============================================================
// Articles 控制器
// ------------------------------------------------------------
// 路由列表：
//   GET    /api/articles/public  - 公开路由（被 exclude，不走 AuthMiddleware）
//   GET    /api/articles         - 列表（需鉴权）
//   GET    /api/articles/:id     - 详情（需鉴权）
//   POST   /api/articles         - 创建（需鉴权）
//   DELETE /api/articles/:id     - 删除（需鉴权 + admin 角色，通过 adminAuthMiddleware 函数中间件）
//
// 演示重点：
//   1. 通过 @Req() 拿到注入了 requestId 的 Request 对象
//   2. DELETE 路由通过 configure() 的 forRoutes({ path, method }) 精确绑定函数中间件
//      （因 NestJS 中间件无 @Use() 装饰器，只能用 configure）
// ============================================================

@Controller('articles')
export class ArticlesController {
  @Get('public')
  getPublic() {
    return { data: '公开文章，无需鉴权' };
  }

  @Get()
  list(@Req() req: Request) {
    return {
      data: [
        { id: 1, title: 'NestJS 中间件入门' },
        { id: 2, title: '依赖注入实战' },
      ],
      requestId: req.requestId,
    };
  }

  @Get(':id')
  findOne(@Param('id') id: string, @Req() req: Request) {
    return {
      id,
      title: `Article ${id}`,
      content: '这是文章正文...',
      requestId: req.requestId,
    };
  }

  @Post()
  create(@Req() req: Request) {
    return {
      created: true,
      body: req.body,
      requestId: req.requestId,
    };
  }

  @Delete(':id')
  remove(@Param('id') id: string, @Req() req: Request) {
    // 该路由除了走 AppModule.configure 中绑定的 AuthMiddleware 之外，
    // 还通过 forRoutes({ path, method: DELETE }) 绑定了 adminAuthMiddleware（见 app.module.ts）
    return {
      deleted: id,
      requestId: req.requestId,
    };
  }
}
