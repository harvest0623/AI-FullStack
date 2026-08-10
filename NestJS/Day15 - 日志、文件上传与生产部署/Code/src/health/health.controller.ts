import { Controller, Get } from '@nestjs/common';
import {
  HealthCheck,
  HealthCheckService,
  HttpHealthIndicator,
  MemoryHealthIndicator,
  DiskHealthIndicator,
  DNSHealthIndicator,
  HealthCheckResult,
} from '@nestjs/terminus';
import * as os from 'os';

/**
 * 健康检查 Controller
 *
 * 暴露 /health 端点，给 k8s liveness/readiness probe / docker HEALTHCHECK 用。
 *
 * 关键 API：
 *   - HealthCheckService.check(indicators[])：并行执行多个指标，任一失败则整体失败
 *   - @HealthCheck() 装饰器：包裹方法，统一返回 { status, info, error, details }
 *   - 各 Indicator：
 *       - HttpHealthIndicator：ping 外部 HTTP 服务
 *       - DNSHealthIndicator：DNS 解析检查
 *       - MemoryHealthIndicator：堆内存阈值检查
 *       - DiskHealthIndicator：磁盘可用空间检查
 *       - TypeOrmHealthIndicator / PrismaHealthIndicator / MongooseHealthIndicator / RedisHealthIndicator...
 *
 * 返回结构：
 *   {
 *     status: 'ok' | 'error',
 *     info:  { 每个健康指标的详情 },
 *     error: { 失败指标的详情 },
 *     details: { 全部指标的详情 }
 *   }
 *
 * 状态码：200（全部 ok） / 503（至少一项 error）
 *
 * k8s 三种探针的使用建议：
 *   - livenessProbe   /health/live     失败就重启
 *   - readinessProbe  /health/ready    失败就从负载均衡剔除
 *   - startupProbe    /health          启动期探活
 */
@Controller('health')
export class HealthController {
  constructor(
    private readonly health: HealthCheckService,
    private readonly http: HttpHealthIndicator,
    private readonly dns: DNSHealthIndicator,
    private readonly memory: MemoryHealthIndicator,
    private readonly disk: DiskHealthIndicator,
  ) {}

  /**
   * 完整健康检查：组合多个指标
   * GET /api/v1/health
   */
  @Get()
  @HealthCheck()
  check(): Promise<HealthCheckResult> {
    return this.health.check([
      // 1) 内存：堆内存使用不超过 300MB
      () => this.memory.checkHeap('memory_heap', 300 * 1024 * 1024),
      // 2) 内存：RSS 使用不超过 500MB
      () => this.memory.checkRss('memory_rss', 500 * 1024 * 1024),
      // 3) DNS：能否解析公共域名（演示用）
      () => this.dns.pingCheck('dns', 'localhost'),
      // 4) 磁盘：检查当前工作目录所在盘可用空间 > 1GB
      () => this.disk.checkStorage('storage', { path: process.cwd(), threshold: 1 * 1024 * 1024 * 1024 }),
    ]);
  }

  /**
   * 存活探针：轻量级，仅返回进程存活
   * k8s livenessProbe 使用，失败即重启 Pod
   * GET /api/v1/health/live
   */
  @Get('live')
  @HealthCheck()
  live(): Promise<HealthCheckResult> {
    return this.health.check([
      () => this.memory.checkHeap('memory_heap', 300 * 1024 * 1024),
    ]);
  }

  /**
   * 就绪探针：检查依赖项（数据库、Redis、外部 API）
   * k8s readinessProbe 使用，失败则从 Service Endpoints 剔除
   * GET /api/v1/health/ready
   *
   * 真实项目里这里应该 ping 数据库、Redis、消息队列等下游依赖。
   * 本 Demo 用 HttpHealthIndicator 演示。
   */
  @Get('ready')
  @HealthCheck()
  ready(): Promise<HealthCheckResult> {
    return this.health.check([
      // 演示：检查自身根路由是否可访问
      // 实战中替换为：TypeOrmHealthIndicator.pingCheck('database') 等
      () =>
        this.http.pingCheck('app_root', `http://localhost:${process.env.PORT || 3000}/api/v1`),
    ]);
  }

  /**
   * 进程信息（自定义健康指标演示）
   * GET /api/v1/health/process
   */
  @Get('process')
  process() {
    const mem = process.memoryUsage();
    return {
      pid: process.pid,
      uptime: process.uptime(),
      platform: process.platform,
      nodeVersion: process.version,
      cpus: os.cpus().length,
      memory: {
        rss: this.formatBytes(mem.rss),
        heapUsed: this.formatBytes(mem.heapUsed),
        heapTotal: this.formatBytes(mem.heapTotal),
        external: this.formatBytes(mem.external),
      },
      loadavg: os.loadavg(),
    };
  }

  private formatBytes(bytes: number): string {
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  }
}
