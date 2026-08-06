import {
  Controller,
  Get,
  Post,
  Delete,
  Param,
  Body,
  Req,
  Logger,
} from '@nestjs/common';
import { Request } from 'express';
import { Roles } from '../decorators/roles.decorator';
import { Public } from '../decorators/public.decorator';
import { Permissions } from '../decorators/permissions.decorator';

/**
 * 文章控制器 —— 演示守卫 + RBAC 全套流程
 *
 * 三类全局守卫已通过 APP_GUARD 注册（见 app.module.ts）：
 *   AuthGuard → RolesGuard → PermissionGuard
 *
 * 通过不同装饰器组合，体现「认证 / 授权 / 细粒度权限」三层防护：
 *
 *   @Public()                  → 跳过认证（公开路由）
 *   无装饰器                    → 仅需登录（任意已登录用户）
 *   @Roles('admin')             → 需要指定角色（粗粒度）
 *   @Permissions('article:x')  → 需要指定权限（细粒度）
 *
 * Mock token（在 auth.guard.ts 中可查）：
 *   - Bearer token-admin    → 拥有所有权限
 *   - Bearer token-editor   → 只能 read/create/update
 *   - Bearer token-visitor  → 只能 read
 *
 * 请求示例：
 *   curl http://localhost:3000/articles/health
 *   curl -H "Authorization: Bearer token-admin" http://localhost:3000/articles
 *   curl -H "Authorization: Bearer token-visitor" http://localhost:3000/articles/123 -X DELETE  # 403
 */
@Controller('articles')
export class ArticlesController {
  private readonly logger = new Logger(ArticlesController.name);

  // ============ 公开路由：@Public() 跳过 AuthGuard ============

  /**
   * GET /articles/health
   * 健康检查，无需登录。
   * @Public() 让全局 AuthGuard 直接放行。
   */
  @Get('health')
  @Public()
  health() {
    return { status: 'ok', timestamp: new Date().toISOString() };
  }

  /**
   * GET /articles/public-list
   * 演示「公开列表」，无需登录也能访问。
   */
  @Get('public-list')
  @Public()
  publicList() {
    return {
      message: '公开文章列表（无需登录）',
      data: [
        { id: 1, title: 'NestJS 入门（公开）' },
        { id: 2, title: '路由系统（公开）' },
      ],
    };
  }

  // ============ 受保护路由：仅需登录（任意用户） ============

  /**
   * GET /articles
   * 任意已登录用户都能访问。
   * 不标 @Roles / @Permissions，RolesGuard / PermissionGuard 会直接放行。
   */
  @Get()
  findAll(@Req() req: Request) {
    return {
      message: '文章列表（任意已登录用户可访问）',
      currentUser: req.user,
      data: [
        { id: 1, title: 'NestJS 入门' },
        { id: 2, title: '路由系统' },
      ],
    };
  }

  /**
   * GET /articles/:id
   * 查看文章详情，任意已登录用户。
   */
  @Get(':id')
  findOne(@Param('id') id: string, @Req() req: Request) {
    return {
      message: `文章详情 #${id}`,
      viewedBy: req.user?.username,
      title: 'NestJS 守卫实战',
    };
  }

  // ============ 角色控制路由：@Roles 粗粒度 ============

  /**
   * GET /articles/admin/dashboard
   * 仅 admin 角色可访问。
   * RolesGuard 会检查 user.roles ∩ ['admin']。
   */
  @Get('admin/dashboard')
  @Roles('admin')
  adminDashboard(@Req() req: Request) {
    return {
      message: '管理员后台',
      admin: req.user?.username,
      stats: { totalArticles: 100, totalUsers: 50 },
    };
  }

  /**
   * GET /articles/editor/workspace
   * admin 或 editor 都可访问（或语义）。
   */
  @Get('editor/workspace')
  @Roles('admin', 'editor')
  editorWorkspace(@Req() req: Request) {
    return {
      message: '编辑工作台',
      user: req.user?.username,
      draftCount: 3,
    };
  }

  // ============ 权限控制路由：@Permissions 细粒度 ============

  /**
   * POST /articles
   * 需要 article:create 权限。
   * editor / admin 都有，visitor 没有。
   */
  @Post()
  @Permissions('article:create')
  create(@Body() body: { title: string; content?: string }, @Req() req: Request) {
    this.logger.log(`[${req.user?.username}] 创建文章：${body.title}`);
    return {
      message: '创建成功',
      data: { id: Math.floor(Math.random() * 1000) + 1, ...body },
      createdBy: req.user?.username,
    };
  }

  /**
   * DELETE /articles/:id
   * 需要 article:delete 权限。
   * 只有 admin 有，editor / visitor 都会 403。
   */
  @Delete(':id')
  @Permissions('article:delete')
  remove(@Param('id') id: string, @Req() req: Request) {
    this.logger.log(`[${req.user?.username}] 删除文章 #${id}`);
    return {
      message: `删除成功 #${id}`,
      deletedBy: req.user?.username,
    };
  }
}
