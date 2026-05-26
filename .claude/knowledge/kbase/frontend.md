# 前端知识

> 本文档沉淀 LLM Knowledge Base 项目的前端相关知识。

---

## 一、组件规范

### 组件结构
- 所有组件为函数组件（Function Component），无 class 组件
- 组件文件使用 PascalCase 命名（`Import.tsx`, `ErrorAlert.tsx`）
- 页面组件在 `frontend/src/pages/` 下，UI 组件在 `frontend/src/components/` 下

### 典型组件模式

```tsx
// 页面组件（pages/Import.tsx）
import { useState, type FormEvent } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api, type IngestResponse } from '../services/api';

export default function Import() {
  const [url, setUrl] = useState('');
  const [recentImports, setRecentImports] = useState<IngestResponse[]>([]);

  const ingestUrlMutation = useMutation({
    mutationFn: (vars: { url: string; tags: string[] }) =>
      api.ingestUrl(vars.url, vars.tags),
    onSuccess: (data) => { addImport(data); setUrl(''); setTags(''); },
  });

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    ingestUrlMutation.mutate({ url: url.trim(), tags: parsedTags });
  };

  return ( /* JSX */ );
}
```

### 关键模式总结
- **状态管理**: 使用 `useState` 管理本地 UI 状态
- **API 调用**: 使用 `useMutation`/`useQuery` from `@tanstack/react-query` 管理服务端状态
- **类型导入**: 使用 `type` 关键字导入类型（`import { api, type IngestResponse } from '../services/api'`）
- **错误处理**: 使用 `ErrorAlert` 组件展示 API 错误
- **空值检查**: 表单提交前做空值守卫（`if (!url.trim()) return`）
- **导入清理**: mutation onSuccess 时会重置表单输入

## 二、样式规范

### 前端（SPA）
- **框架**: TailwindCSS 4
- **入口**: `frontend/src/index.css` 仅包含 `@import "tailwindcss";`
- **构建**: 通过 `@tailwindcss/vite` 插件集成到 Vite
- **无额外 CSS**: 不使用自定义 CSS 文件或 CSS Modules
- **图标**: 使用 `lucide-react` 图标库

### 官网
- **框架**: TailwindCSS 3（与前端版本不同）
- **动画**: 使用 `framer-motion` 实现滚动动画
- **自定义组件**: 基础 UI 组件在 `website/components/ui/` 下（button, logo, icon-box, scroll-reveal）
- **全局样式**: `website/app/globals.css`

## 三、状态管理

### 方案
项目没有使用 Redux 或 Zustand 等全局状态管理库。状态管理方案：

| 状态类型 | 方案 | 示例 |
|---------|------|------|
| 服务端状态 | TanStack React Query | 文档列表、导入结果 |
| 认证状态 | 自定义 `useAuth` hook + localStorage | token, user, authMode |
| UI 状态 | React `useState` | 表单输入、弹窗显示 |
| URL 状态 | React Router | 当前页面路由 |

### 认证状态管理（useAuth hook）

`useAuth` hook 是项目中最重要的自定义 hook，管理：

- **token 持久化**: 存储在 `llm_kb_token`（localStorage key）
- **用户信息**: `llm_kb_user`（localStorage key，JSON 序列化）
- **认证模式**: `auth_mode`（localStorage key，值为 `'local'` 或 `'cloud'`）
- **初始化**: 使用 `loadInitialState` 函数从 localStorage 恢复登录状态

```tsx
const {
  user,          // UserInfo | null
  loading,       // boolean
  authMode,      // 'local' | 'cloud'
  setAuthMode,   // (mode: AuthMode) => void
  login,         // (credentials) => Promise<void>
  logout,        // () => void
  setup,         // (username, password) => Promise<void>
} = useAuth();
```

### React Query 配置
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,   // 30s 内不重新请求
      retry: 1,             // 失败重试 1 次
    },
  },
});
```

## 四、API 服务层

### 架构
前端通过 `frontend/src/services/api.ts` 中的 `api` 对象与后端通信：

- 使用原生 `fetch` API（无 axios）
- 基路径为 `/api/v1`
- token 通过 `api.setToken(token)` 设置，自动附加到请求头
- 统一错误处理：非 2xx 响应 → `ApiError` 类 → 前端可捕获

### 错误展示
使用 `frontend/src/components/ErrorAlert.tsx` 组件 + `frontend/src/lib/errorMessages.ts`（中文错误消息映射）展示用户友好的错误信息。

## 五、路由与页面

### 路由结构
```tsx
<BrowserRouter>
  <Routes>
    {/* 公开路由 */}
    <Route path="/login" element={<Login />} />
    <Route path="/setup" element={<Setup />} />

    {/* 受保护路由，需要认证 */}
    <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
      <Route path="/import" element={<Import />} />
      <Route path="/library" element={<Library />} />
      <Route path="/concepts" element={<Concepts />} />
      <Route path="/chat" element={<Chat />} />
      <Route path="/settings" element={<Settings />} />
    </Route>

    {/* 默认跳转到 /import */}
    <Route path="*" element={<Navigate to="/import" replace />} />
  </Routes>
</BrowserRouter>
```

### 页面功能
| 页面 | 路径 | 功能 |
|------|------|------|
| Login | /login | 用户登录（支持 local/cloud 模式切换） |
| Setup | /setup | 首次使用初始化（创建管理员用户） |
| Import | /import | 文档导入（URL/文件/视频/GitHub） |
| Library | /library | 文档库管理 + 触发编译 |
| Concepts | /concepts | 概念词条查看 |
| Chat | /chat | 知识问答（SSE 流式） |
| Settings | /settings | LLM 配置 + API Key 管理 |

---

*由 Project Knowledge 于 2026-05-26 自动生成*
