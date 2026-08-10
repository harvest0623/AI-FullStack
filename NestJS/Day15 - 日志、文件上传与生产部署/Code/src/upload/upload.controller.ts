import {
  Controller,
  Post,
  UseInterceptors,
  UploadedFile,
  UploadedFiles,
  BadRequestException,
  ParseFilePipe,
  MaxFileSizeValidator,
  FileTypeValidator,
  Get,
  Param,
  Res,
  NotFoundException,
} from '@nestjs/common';
import { FileInterceptor, FilesInterceptor } from '@nestjs/platform-express';
import { diskStorage, memoryStorage } from 'multer';
import { extname, join, basename } from 'path';
import { ConfigService } from '@nestjs/config';
import { MyLoggerService } from '../logger/my-logger.service';

/**
 * 文件上传 Controller
 *
 * 演示三个典型场景：
 *   1. POST /upload/single    单文件上传（diskStorage 持久化到 uploads/）
 *   2. POST /upload/multiple   多文件上传（diskStorage，最多 5 个）
 *   3. POST /upload/avatar     头像上传（memoryStorage + 严格校验：jpg/png <2MB）
 *
 * 关键 API：
 *   - @UploadedFile()      单文件，类型 Express.Multer.File
 *   - @UploadedFiles()     多文件，类型 Express.Multer.File[]
 *   - FileInterceptor(field, options)        单文件拦截器
 *   - FilesInterceptor(field, maxCount, opts) 多文件拦截器
 *   - ParseFilePipe + 内置 Validator         文件校验管道
 *
 * diskStorage vs memoryStorage：
 *   - diskStorage：直接落盘，不占内存，适合大文件、永久保存
 *   - memoryStorage：先放内存 Buffer，适合需要立即处理（压缩、转存 OSS）的小文件
 */

const UPLOAD_DEST = './uploads';
const ALLOWED_AVATAR_TYPES = /(jpg|jpeg|png)$/i;

@Controller('upload')
export class UploadController {
  private readonly logger = new MyLoggerService(UploadController.name);

  constructor(private readonly config: ConfigService) {}

  /**
   * 单文件上传（diskStorage）
   * curl -F "file=@./a.txt" http://localhost:3000/api/v1/upload/single
   */
  @Post('single')
  @UseInterceptors(
    FileInterceptor('file', {
      storage: diskStorage({
        destination: (_req, _file, cb) => cb(null, UPLOAD_DEST),
        filename: (_req, file, cb) => {
          // 文件名 = 原始名(去扩展) + 时间戳 + 随机串 + 扩展名，避免重名覆盖
          const ext = extname(file.originalname);
          const base = basename(file.originalname, ext);
          const unique = `${base}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}${ext}`;
          cb(null, unique);
        },
      }),
      limits: { fileSize: 10 * 1024 * 1024 }, // 10MB
    }),
  )
  uploadSingle(@UploadedFile() file: Express.Multer.File) {
    if (!file) throw new BadRequestException('未收到文件，请用 form-data 字段名 file 上传');
    this.logger.log(`收到单文件：${file.originalname} -> ${file.filename}`);
    return {
      message: '上传成功',
      originalName: file.originalname,
      savedAs: file.filename,
      size: file.size,
      mimetype: file.mimetype,
      path: `/api/v1/upload/files/${file.filename}`,
    };
  }

  /**
   * 多文件上传（diskStorage，最多 5 个）
   * curl -F "files=@./a.txt" -F "files=@./b.txt" http://localhost:3000/api/v1/upload/multiple
   */
  @Post('multiple')
  @UseInterceptors(
    FilesInterceptor('files', 5, {
      storage: diskStorage({
        destination: (_req, _file, cb) => cb(null, UPLOAD_DEST),
        filename: (_req, file, cb) => {
          const ext = extname(file.originalname);
          const base = basename(file.originalname, ext);
          cb(null, `${base}-${Date.now()}${ext}`);
        },
      }),
      limits: { fileSize: 5 * 1024 * 1024 }, // 5MB / file
    }),
  )
  uploadMultiple(@UploadedFiles() files: Express.Multer.File[]) {
    if (!files || files.length === 0) {
      throw new BadRequestException('未收到文件，请用 form-data 字段名 files 上传，最多 5 个');
    }
    this.logger.log(`收到 ${files.length} 个文件`);
    return {
      message: '上传成功',
      count: files.length,
      files: files.map((f) => ({
        originalName: f.originalname,
        savedAs: f.filename,
        size: f.size,
        path: `/api/v1/upload/files/${f.filename}`,
      })),
    };
  }

  /**
   * 头像上传（memoryStorage + ParseFilePipe 严格校验）
   * 仅允许 jpg/jpeg/png，且 <2MB
   *
   * 演示如何用 ParseFilePipe + 内置 Validator 做文件级校验：
   *   - MaxFileSizeValidator：限制最大字节
   *   - FileTypeValidator：基于 mimetype 校验
   *
   * curl -F "file=@./avatar.png" http://localhost:3000/api/v1/upload/avatar
   */
  @Post('avatar')
  @UseInterceptors(
    FileInterceptor('file', {
      storage: memoryStorage(), // 文件留在内存 Buffer，便于后续转存到 OSS
      limits: { fileSize: 2 * 1024 * 1024 },
    }),
  )
  uploadAvatar(
    @UploadedFile(
      new ParseFilePipe({
        validators: [
          new MaxFileSizeValidator({ maxSize: 2 * 1024 * 1024 }),
          new FileTypeValidator({ fileType: ALLOWED_AVATAR_TYPES }),
        ],
        fileIsRequired: true,
      }),
    )
    file: Express.Multer.File,
  ) {
    // 这里通常会：把 file.buffer 上传到 OSS/S3，然后返回 URL
    this.logger.log(`头像上传：${file.originalname} (${file.size} bytes)`);
    return {
      message: '头像校验通过（演示用，未真正落盘）',
      originalName: file.originalname,
      size: file.size,
      mimetype: file.mimetype,
      // 实战中此处应返回 OSS URL：{ url }
    };
  }

  /**
   * 文件下载/访问（演示 diskStorage 文件如何被取回）
   * GET /upload/files/:filename
   */
  @Get('files/:filename')
  serveFile(@Param('filename') filename: string, @Res() res: any) {
    // 防止路径穿越：仅允许文件名，不允许 /
    if (filename.includes('/') || filename.includes('..')) {
      throw new BadRequestException('非法文件名');
    }
    const filePath = join(process.cwd(), UPLOAD_DEST, filename);
    const fs = require('fs');
    if (!fs.existsSync(filePath)) {
      throw new NotFoundException('文件不存在');
    }
    return res.sendFile(filePath);
  }
}
