// Day11 - zustand-store.ts  Zustand 全局聊天 store 示例
// store.ts 落位：app/store.ts；组件落位：app/chat/page.tsx
// 安装：npm install zustand

// ============ app/store.ts ============
'use client';
import { create } from 'zustand';

type ChatMessage = { id: number; role: 'user' | 'assistant'; text: string };

type ChatStore = {
  messages: ChatMessage[];
  isStreaming: boolean;
  addMessage: (msg: ChatMessage) => void;
  setStreaming: (v: boolean) => void;
  clear: () => void;
};

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  isStreaming: false,
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  setStreaming: (v) => set({ isStreaming: v }),
  clear: () => set({ messages: [] }),
}));

// ============ 组件中使用（多个组件共享同一 store） ============
// app/chat/page.tsx
'use client';
import { useState } from 'react';
import { useChatStore } from './store';

export default function ChatPage() {
  // 用 selector 精确订阅，只取用到的切片，避免多余重渲染
  const messages = useChatStore((s) => s.messages);
  const addMessage = useChatStore((s) => s.addMessage);
  const setStreaming = useChatStore((s) => s.setStreaming);
  const [input, setInput] = useState('');

  const send = () => {
    if (!input.trim()) return;
    addMessage({ id: Date.now(), role: 'user', text: input.trim() });
    setInput('');
    setStreaming(true);
    // ... 此处可接真实大模型，异步收到回复后再 setStreaming(false)
  };

  return (
    <main style={{ padding: 40, maxWidth: 600, margin: '0 auto' }}>
      <h2>聊天（Zustand 共享状态）</h2>
      <div style={{ minHeight: 200, border: '1px solid #eee', padding: 16, marginBottom: 12 }}>
        {messages.length === 0 ? (
          <p style={{ color: '#888' }}>还没有消息</p>
        ) : (
          messages.map((m) => (
            <p key={m.id} style={{ textAlign: m.role === 'user' ? 'right' : 'left' }}>
              <b>{m.role === 'user' ? '我' : 'AI'}：</b>{m.text}
            </p>
          ))
        )}
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder="输入消息"
          style={{ flex: 1, padding: 8 }}
        />
        <button onClick={send}>发送</button>
      </div>
    </main>
  );
}