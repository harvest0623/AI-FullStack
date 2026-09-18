# Day12 - 样式方案与 UI

> 本章节掌握 Next.js 中的样式组织方式。从全局 CSS、CSS Modules、预处理器，到主流的 Tailwind CSS 与 CSS-in-JS，配合响应式设计、主题切换与图片字体优化，构建专业美观且高性能的界面。

---

## 目录

- [一、学习目标](#一学习目标)
- [二、理论知识](#二理论知识)
  - [2.1 样式方案总览](#21-样式方案总览)
  - [2.2 全局 CSS 与 reset](#22-全局-css-与-reset)
  - [2.3 CSS Modules](#23-css-modules)
  - [2.4 Tailwind CSS](#24-tailwind-css)
  - [2.5 CSS-in-JS](#25-css-in-js)
  - [2.6 预处理器 Sass](#26-预处理器-sass)
- [三、核心概念解析](#三核心概念解析)
  - [3.1 响应式设计](#31-响应式设计)
  - [3.2 主题切换](#32-主题切换)
  - [3.3 图片与字体优化](#33-图片与字体优化)
  - [3.4 断点与栅格](#34-断点与栅格)
- [四、关键知识点总结](#四关键知识点总结)
- [五、实战练习](#五实战练习)

---

## 一、学习目标

完成本节内容后，你应当能够：

1. **理解样式方案差异**：说清全局 CSS / CSS Modules / Tailwind / CSS-in-JS 的适用场景。
2. **使用 CSS Modules**：实现局部作用域样式，避免类名冲突。
3. **用 Tailwind 快速布局**：掌握工具类设计与响应式断点。
4. **实现响应式与主题**：适配多屏与深色模式。
5. **优化图片与字体**：用 next/image 和 next/font 提升性能。

---

## 二、理论知识

### 2.1 样式方案总览

Next.js 无需额外配置即可使用多种样式方案：

| 方案 | 特点 | 适用 |
| --- | --- | --- |
| **全局 CSS** | `app/globals.css`，作用全局 | 变量、reset、基础样式 |
| **CSS Modules** | `<name>.module.css`，类名局部化 | 组件级局部样式 |
| **Tailwind CSS** | 工具类，直接在 className 组合 | 快速布局、团队规范 |
| **CSS-in-JS** | 样式写在 JS/TSX 里 | 主题化、动态样式 |
| **Sass** | 变量/嵌套/混合宏 | 复杂 CSS 组织 |

### 2.2 全局 CSS 与 reset

全局样式在根布局导入：

```tsx
// app/layout.tsx
import './globals.css';

export default function RootLayout({ children }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
```

```css
/* app/globals.css —— CSS 变量 + 基础样式 */
:root {
  --primary: #7c3aed;
  --bg: #ffffff;
  --text: #1f2937;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, 'PingFang SC', sans-serif;
}
```

用 CSS 变量集中管理主题色，全局统一。

### 2.3 CSS Modules

`<name>.module.css` 生成的类名会被**自动 hash 局部化**，多个组件可用同名类互不冲突：

```css
/* button.module.css */
.button {
  padding: 10px 16px;
  border-radius: 8px;
  background: #7c3aed;
  color: #fff;
  border: none;
  cursor: pointer;
}
.button:hover {
  opacity: 0.9;
}
```

```tsx
// button.tsx（Server Component 也可用 CSS Modules）
import styles from './button.module.css';

export default function Button({ children }) {
  return <button className={styles.button}>{children}</button>;
}
```

关键：`styles.button` 引用编译后的哈希类名，天然隔离，是**局部样式**的首选。

### 2.4 Tailwind CSS

Tailwind 提供**工具类**，无需写 CSS 文件，直接在 `className` 里组合实现样式：

```tsx
<button className="px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700">
  提交
</button>
```

常用工具类示例：

```tsx
<div className="flex items-center justify-between p-6 max-w-3xl mx-auto">
  <h1 className="text-2xl font-bold">标题</h1>
  <span className="text-sm text-gray-500">副文本</span>
</div>
```

- **布局**：`flex`、`grid`、`items-center`、`justify-between`、`gap-4`
- **间距**：`p-4`（padding）、`m-2`（margin）、`space-x-4`
- **尺寸**：`w-full`、`h-16`、`max-w-md`
- **排版**：`text-lg`、`font-semibold`、`text-center`
- **颜色**：`bg-purple-600`、`text-white`、`border-gray-200`
- **响应式**：`md:grid-cols-2`（在小屏单列、中屏及以上两列）

Tailwind 通过 `tailwind.config.ts` 定制主题色、断点等。

### 2.5 CSS-in-JS

把样式作为 JS 对象/函数写在组件里，便于动态与主题化。常用库：`@emotion/react`、`styled-components`、`vanilla-extract` 等。

在 Next.js 服务端组件中，推荐用 **CSS-in-JS with Server Components 兼容方案**（或仅用于客户端组件）。简单动态样式也可直接用内联 `style`：

```tsx
export default function Card({ active }) {
  return (
    <div style={{ padding: 16, border: active ? '2px solid #7c3aed' : '1px solid #eee' }}>
      ...
    </div>
  );
}
```

### 2.6 预处理器 Sass

需要 Sass 则安装 `sass`，直接用 `.scss` 文件：

```bash
npm install sass
```

```scss
$primary: #7c3aed;

.card {
  padding: 16px;
  border: 1px solid lighten($primary, 40%);
  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
}
```

利用嵌套、变量、混合宏组织复杂样式。

---

## 三、核心概念解析

### 3.1 响应式设计

**移动优先**使用 Tailwind 断点前缀，或 CSS 媒体查询：

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* 手机1列 → 平板2列 → 桌面3列 */}
</div>
```

```css
/* 纯 CSS 等价 */
.grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}
@media (min-width: 768px) { .grid { grid-template-columns: repeat(2, 1fr); } }
@media (min-width: 1024px) { .grid { grid-template-columns: repeat(3, 1fr); } }
```

### 3.2 主题切换

结合 CSS 变量 + 数据属性或类，实现深浅主题：

```css
[data-theme='dark'] {
  --bg: #0f172a;
  --text: #e2e8f0;
  --primary: #a78bfa;
}
```

用 Zustand/Context 保存主题状态，切换时设置 `document.documentElement.dataset.theme`。

### 3.3 图片与字体优化

**next/image** 提供自动优化、懒加载、响应式尺寸：

```tsx
import Image from 'next/image';

<Image
  src="/logo.png"
  alt="Logo"
  width={200}
  height={80}
  priority         // 首屏关键图用 priority 快速加载
  className="object-contain"
/>
```

> 外部图片域名需在 `next.config.ts` 的 `images.remotePatterns` 中配置。

**next/font** 自动优化字体，避免布局偏移（CLS）与额外请求：

```tsx
import { Inter } from 'next/font/google';

const inter = Inter({ subsets: ['latin'] });

// 在布局中应用
<body className={inter.className}>{children}</body>
```

### 3.4 断点与栅格

Tailwind 默认断点：`sm(640)`、`md(768)`、`lg(1024)`、`xl(1280)`、`2xl(1536)`。据此组合响应式布局，界面在不同屏幕自适应。

---

## 四、关键知识点总结

- **多种方案并存**：全局 CSS（变量/reset）、CSS Modules（局部）、Tailwind（工具类）、CSS-in-JS（动态）。
- **CSS Modules**：`xxx.module.css` + `styles.class`，类名 hash 局部化。
- **Tailwind**：工具类快速布局，`md:` 等前缀做响应式，配置 `tailwind.config.ts`。
- **响应式**：移动优先，断点前缀 / 媒体查询。
- **主题**：CSS 变量 + data-theme + Zustand/Context 管理。
- **图片**：`next/image` 自动优化、优先级、懒加载。
- **字体**：`next/font` 自托管优化，避免 CLS。
- **配色原则**：用 CSS 变量集中管理主题色，符合品牌基调。

---

## 五、实战练习

### 练习一：styles_tour.js —— 样式方案对比演示

**任务描述**：运行脚本，展示全局 CSS / CSS Modules / Tailwind / CSS-in-JS 的写法与适用场景对比。

**运行方式**

```bash
cd Code
node styles_tour.js
```

### 练习二：CSS Modules 卡片

用 `card.module.css` + 组件实现一个带 hover、局部作用域的卡片组件，验证类名隔离。

### 练习三：响应式 Tailwind 页面 + 主题切换

用 Tailwind 构建 `grid grid-cols-1 md:grid-cols-2` 的响应式商品栅格，并用 CSS 变量实现深浅主题切换。

---

## 下节预告

下一节 **Day13** 将进入 **认证授权与中间件**：用 NextAuth（Auth.js）、Session、Cookie 与 `middleware.ts` 构建完整的登录、路由保护与权限控制体系，保障 AI 应用安全。