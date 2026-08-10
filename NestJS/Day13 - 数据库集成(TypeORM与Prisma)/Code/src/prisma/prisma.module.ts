import { Global, Module } from '@nestjs/common';
import { PrismaService } from './prisma.service';

/**
 * PrismaModule
 *
 * @Global()：标记为全局模块，PrismaService 在整个应用里都可注入，
 *           子模块不用重复 imports: [PrismaModule]。
 *
 * providers + exports：把 PrismaService 注册为单例并对外暴露。
 */
@Global()
@Module({
  providers: [PrismaService],
  exports: [PrismaService],
})
export class PrismaModule {}
