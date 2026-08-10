import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  OneToMany,
} from 'typeorm';
import { Article } from './article.entity';

/**
 * User 实体
 *
 * 一个 User 可以拥有多篇 Article（1 ↔ N 关系）。
 * User 一侧持有 @OneToMany 反向引用，外键不落在 User 表上。
 */
@Entity('users')
export class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ unique: true })
  email: string;

  @Column({ length: 100, nullable: true })
  name: string | null;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;

  // 反向关系：当前 User 名下的所有文章
  @OneToMany(() => Article, (article) => article.author)
  articles: Article[];
}
