import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { Cron, CronExpression, Interval, Timeout, SchedulerRegistry } from '@nestjs/schedule';
import { CronJob } from 'cron';

/**
 * 定时任务 Service
 *
 * 三种声明式调度：
 *   1. @Cron('0 * * * *')   按 cron 表达式：每小时的第 0 分钟执行
 *   2. @Interval(5000)       每 5 秒执行一次
 *   3. @Timeout(5000)        启动后 5 秒执行一次（仅一次）
 *
 * 动态调度：
 *   - SchedulerRegistry 注入：可在运行时动态添加/删除/查询任务
 *   - 适用于"用户触发后启动某定时任务"或"动态改变频率"场景
 *
 * cron 表达式（5 段式）：
 *   ┌──────── minute (0-59)
 *   │ ┌────── hour (0-23)
 *   │ │ ┌──── day of month (1-31)
 *   │ │ │ ┌── month (1-12)
 *   │ │ │ │ ─ day of week (0-7, 0 和 7 都是周日)
 *   │ │ │ │ │
 *   * * * * *
 *
 * 常用快捷宏（CronExpression 枚举）：
 *   - EVERY_MINUTE        '0 * * * * *'
 *   - EVERY_HOUR          '0 * * * *'
 *   - EVERY_DAY_AT_MIDNIGHT '0 0 * * *'
 *   - EVERY_DAY_AT_1AM    '0 1 * * *'
 *   - EVERY_WEEKEND       等等
 */
@Injectable()
export class TasksService implements OnModuleInit {
  private readonly logger = new Logger(TasksService.name);
  private dynamicCounter = 0;

  constructor(private readonly scheduler: SchedulerRegistry) {}

  onModuleInit() {
    this.logger.log('TasksService 初始化完成，定时任务已注册');
  }

  /**
   * @Cron：每分钟第 0 秒执行（演示用，频率太高会刷屏，谨慎启用）
   */
  @Cron(CronExpression.EVERY_MINUTE)
  handleEveryMinute() {
    this.logger.debug('⏰ 每分钟任务触发：检查待办状态');
    // 真实场景：扫描数据库中 overdue 订单、刷新缓存、推送提醒等
  }

  /**
   * 每天 0:30 清理过期临时文件
   */
  @Cron('30 0 * * *')
  handleDailyCleanup() {
    this.logger.log('🧹 每日 0:30 清理任务启动');
    // 例如：删除 uploads/tmp/ 下超过 7 天的文件
  }

  /**
   * @Interval：每 30 秒执行一次
   * 演示高频任务（实际生产中慎用，避免压垮 DB）
   */
  @Interval(30000)
  handleInterval() {
    this.logger.verbose('🔁 30s 间隔任务：心跳上报 / 同步指标');
  }

  /**
   * @Timeout：应用启动后 5 秒执行一次
   * 常用于"预热缓存"、"加载字典数据到内存"
   */
  @Timeout(5000)
  handleOnceAfterStart() {
    this.logger.log('🚀 应用启动 5s 后执行的一次性任务：预热缓存');
  }

  // ---------------------------------------------------------------
  //  动态调度 API：通过 SchedulerRegistry 在运行时增删任务
  // ---------------------------------------------------------------

  /**
   * 添加一个动态定时任务
   * @param name 任务名（唯一标识，用于后续删除/查询）
   * @param cronExpression cron 表达式，如 '*/10 * * * * *'
   */
  addDynamicJob(name: string, cronExpression: string): { name: string; cron: string; status: string } {
    // 若已存在同名任务，先删除
    if (this.scheduler.doesExist('cron', name)) {
      this.scheduler.deleteCronJob(name);
      this.logger.warn(`已存在同名任务 ${name}，旧任务被覆盖`);
    }

    const job = new CronJob(cronExpression, () => {
      this.dynamicCounter += 1;
      this.logger.log(`[动态任务 ${name}] 第 ${this.dynamicCounter} 次执行`);
    });

    this.scheduler.addCronJob(name, job);
    job.start();

    this.logger.log(`✅ 动态任务已添加：name=${name}, cron=${cronExpression}`);
    return { name, cron: cronExpression, status: 'running' };
  }

  /**
   * 删除动态任务
   */
  removeDynamicJob(name: string): { name: string; status: string } {
    if (!this.scheduler.doesExist('cron', name)) {
      this.logger.warn(`任务 ${name} 不存在`);
      return { name, status: 'not_found' };
    }
    this.scheduler.deleteCronJob(name);
    this.logger.log(`🗑️  动态任务已删除：name=${name}`);
    return { name, status: 'deleted' };
  }

  /**
   * 暂停动态任务（不删除）
   */
  pauseDynamicJob(name: string): { name: string; status: string } {
    const job = this.scheduler.getCronJob(name);
    job.stop();
    this.logger.log(`⏸️  动态任务已暂停：name=${name}`);
    return { name, status: 'paused' };
  }

  /**
   * 恢复动态任务
   */
  resumeDynamicJob(name: string): { name: string; status: string } {
    const job = this.scheduler.getCronJob(name);
    job.start();
    this.logger.log(`▶️  动态任务已恢复：name=${name}`);
    return { name, status: 'resumed' };
  }

  /**
   * 列出所有已注册的 cron 任务
   */
  listCronJobs(): Record<string, string> {
    const jobs = this.scheduler.getCronJobs();
    const result: Record<string, string> = {};
    jobs.forEach((job, name) => {
      result[name] = `next: ${job.nextDate()?.toISO() || 'n/a'}`;
    });
    return result;
  }
}
