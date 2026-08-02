import { Test } from '@nestjs/testing';
import { AppController } from './app.controller';
import { AppService } from './app.service';

/**
 * 控制器单元测试示例
 *
 * NestJS 默认使用 Jest 作为测试框架。
 * 单元测试的核心思路：把被测类的依赖（AppService）用 mock 替换，
 *   只验证控制器自身的「请求响应映射」逻辑，不验证 Service。
 *
 * 运行方式：npm run test
 */
describe('AppController', () => {
  let appController: AppController;

  beforeEach(async () => {
    // Test.createTestingModule 构建一个测试用模块
    // overrideProvider(AppService).useValue({...}) 把真实 Service 替换为桩对象
    const moduleRef = await Test.createTestingModule({
      controllers: [AppController],
      providers: [AppService],
    })
      .overrideProvider(AppService)
      .useValue({ getHello: () => 'Hello NestJS! Welcome to Day01.' })
      .compile();

    appController = moduleRef.get<AppController>(AppController);
  });

  describe('getHello', () => {
    it('应返回欢迎字符串', () => {
      expect(appController.getHello()).toBe('Hello NestJS! Welcome to Day01.');
    });
  });
});
