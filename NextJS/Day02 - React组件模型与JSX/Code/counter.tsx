// Day02 - counter.tsx  计数器组件（useState + 事件处理）
// 放到 app/counter/page.tsx 使用，实际演示状态驱动重渲染。
// 由于使用 useState 交互，需标记 'use client'（客户端组件）。

'use client';

import { useState } from 'react';

export default function Counter() {
  const [count, setCount] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);

  const add = (n: number) => {
    setCount((c) => c + n);
    setLogs((l) => [`前一次：${count} → 加${n}`, ...l].slice(0, 5));
  };

  const reset = () => {
    setCount(0);
    setLogs([]);
  };

  return (
    <main style={{ padding: 40, fontFamily: 'sans-serif' }}>
      <h2>计数器（验证 useState 重渲染）</h2>
      <p style={{ fontSize: 40, fontWeight: 'bold' }}>{count}</p>
      <div style={{ display: 'flex', gap: 8 }}>
        <button onClick={() => add(-1)}>-1</button>
        <button onClick={() => add(1)}>+1</button>
        <button onClick={reset}>清零</button>
      </div>

      <h3>操作日志</h3>
      {logs.length === 0 ? (
        <p>暂无操作</p>
      ) : (
        <ul>
          {logs.map((l, i) => (
            <li key={i}>{l}</li>
          ))}
        </ul>
      )}
    </main>
  );
}