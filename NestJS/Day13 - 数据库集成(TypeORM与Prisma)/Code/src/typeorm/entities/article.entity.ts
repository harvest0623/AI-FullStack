import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  ManyToOne,
  JoinColumn,
} from 'typeorm';
import { User } from './user.entity';

/**
 * Article 实体
 *
 * 多篇文章属于一个 User（N ↔ 1 关系）。
 * 外键列 authorId 落在 articles 表上，通过 @JoinColumn 显式声明。
 */
@Entity('articles')
export class Article {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ length: 200 })
  title: string;

  @Column({ type: 'text', nullable: true })
  content: string | null;

  @Column({ default: 0 })
  viewCount: number;

  // 外键列：与 @ManyToOne 配合，数据库实际存在的字段
  @Column({ name: 'author_id' })
  authorId: number;

  // 关系字段：仅在查询时通过 relations 加载，不入库
  @ManyToOne(() => User, (user) => user.articles, { eager: false })
  @JoinColumn({ name: 'author_id' })
  author: User;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
