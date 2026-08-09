import { Injectable, NotFoundException } from '@nestjs/common';

import { CreateUserDto, UserRole } from './dto/create-user.dto';
import { UserResponseDto } from './dto/user-response.dto';

/**
 * 用户服务（内存数据演示）
 *
 * 与 ArticlesService 类似，负责 DTO ↔ Entity 的转换。
 * 重点演示：响应时剥离 password 字段。
 */
@Injectable()
export class UsersService {
  private users: Array<{
    id: number;
    username: string;
    email: string;
    password: string; // 内部字段，绝不出现在响应里
    role: UserRole;
    nickname?: string;
    createdAt: string;
  }> = [
    {
      id: 1,
      username: 'alice',
      email: 'alice@example.com',
      password: 'p@ssw0rd123',
      role: UserRole.ADMIN,
      nickname: '小红',
      createdAt: '2025-07-20T08:00:00.000Z',
    },
    {
      id: 2,
      username: 'bob',
      email: 'bob@example.com',
      password: 'bobsecret',
      role: UserRole.EDITOR,
      createdAt: '2025-07-21T08:00:00.000Z',
    },
  ];

  private nextId = 3;

  findAll(): UserResponseDto[] {
    return this.users.map(this.toResponse);
  }

  findOne(id: number): UserResponseDto {
    const user = this.users.find((u) => u.id === id);
    if (!user) {
      throw new NotFoundException(`用户 ${id} 不存在`);
    }
    return this.toResponse(user);
  }

  create(dto: CreateUserDto): UserResponseDto {
    const user = {
      id: this.nextId++,
      username: dto.username,
      email: dto.email,
      password: dto.password, // 入库前应做哈希，本项目仅演示
      role: dto.role ?? UserRole.READER,
      nickname: dto.nickname,
      createdAt: new Date().toISOString(),
    };
    this.users.push(user);
    return this.toResponse(user);
  }

  /**
   * Entity → Response DTO
   *
   * 关键：用解构把 password 显式剥离，模拟响应 DTO 隐藏敏感字段。
   * 真实项目里通常用 class-transformer 的 @Exclude + plainToInstance 自动完成。
   */
  private toResponse(user: {
    id: number;
    username: string;
    email: string;
    password: string;
    role: UserRole;
    nickname?: string;
    createdAt: string;
  }): UserResponseDto {
    const { password: _omit, ...rest } = user;
    return rest as UserResponseDto;
  }
}
