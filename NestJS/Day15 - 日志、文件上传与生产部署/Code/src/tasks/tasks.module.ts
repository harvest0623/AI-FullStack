import { Controller, Get, Post, Delete, Param, Body, Query } from '@nestjs/common';
import { Module } from '@nestjs/common';
import { TasksService } from './tasks.service';

/**
 * Tasks Controller：暴露动态调度 API
 *
 * 演示如何通过 HTTP 接口触发 SchedulerRegistry 的动态增删
 *   POST   /tasks/jobs/:name?cron=* * * * *   添加/覆盖动态任务
 *   DELETE /tasks/jobs/:name                  删除任务
 *   POST   /tasks/jobs/:name/pause            暂停
 *   POST   /tasks/jobs/:name/resume           恢复
 *   GET    /tasks/jobs                        列出所有任务
 */
@Controller('tasks')
class TasksController {
  constructor(private readonly tasks: TasksService) {}

  @Post('jobs/:name')
  addJob(
    @Param('name') name: string,
    @Body('cron') cron: string,
    @Query('cron') cronQuery?: string,
  ) {
    // 优先取 body.cron，其次取 query.cron，最后默认每 10 秒
    const cronExpr = cron || cronQuery || '*/10 * * * * *';
    return this.tasks.addDynamicJob(name, cronExpr);
  }

  @Delete('jobs/:name')
  removeJob(@Param('name') name: string) {
    return this.tasks.removeDynamicJob(name);
  }

  @Post('jobs/:name/pause')
  pauseJob(@Param('name') name: string) {
    return this.tasks.pauseDynamicJob(name);
  }

  @Post('jobs/:name/resume')
  resumeJob(@Param('name') name: string) {
    return this.tasks.resumeDynamicJob(name);
  }

  @Get('jobs')
  listJobs() {
    return this.tasks.listCronJobs();
  }
}

/**
 * Tasks 模块
 *
 * ScheduleModule.forRoot() 必须在根模块（AppModule）注册一次，
 * 本模块只需要把 TasksService 注册为 Provider 即可，装饰器自动生效。
 */
@Module({
  controllers: [TasksController],
  providers: [TasksService],
  exports: [TasksService],
})
export class TasksModule {}
