import { Module } from '@nestjs/common';
import { UploadController } from './upload.controller';

/**
 * 文件上传模块
 *
 * 真实项目中可能还需要：
 *   - UploadService：负责把文件转存到 OSS、写库表记录
 *   - FileFilter：捕获 MulterError（如 LIMIT_FILE_SIZE），转换成自定义错误响应
 *   - 上传记录 Repository：与用户/资源关联
 *
 * 本 Demo 仅演示 Controller 层，省略 Service。
 */
@Module({
  controllers: [UploadController],
})
export class UploadModule {}
