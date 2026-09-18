// Day12 - card.tsx  CSS Modules 组件示例
// 与 card.module.css 配套。落位：app/components/Card.tsx

import styles from './card.module.css';

type CardProps = {
  title: string;
  desc: string;
  tag?: string;
};

export default function Card({ title, desc, tag }: CardProps) {
  return (
    <div className={styles.card}>
      <h3 className={styles.title}>{title}</h3>
      <p className={styles.desc}>{desc}</p>
      {tag && <span className={styles.tag}>{tag}</span>}
    </div>
  );
}

// ============ 使用方式 ============
// import Card from '@/app/components/Card';
//
// <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
//   <Card title="AI 对话" desc="基于 Next.js 的流式对话应用" tag="前端" />
//   <Card title="RAG 服务" desc="检索增强生成的后端集成" tag="后端" />
// </div>