# 04 - 认证系统

## 概述

认证系统负责用户身份验证、Token 管理和会话状态维护。

## 核心文件

| 文件 | 职责 |
|------|------|
| `api/auth.ts` | 认证 API (登录/注册/Token) |
| `contexts/AuthContext.tsx` | 认证状态 Context |
| `components/auth/LoginDialog.tsx` | 登录对话框 UI |

## 认证流程

```
┌─────────────────────────────────────────────────────────┐
│                      应用启动                            │
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│                  AuthProvider 初始化                      │
│              调用 getAuthStatus() 检查登录状态              │
└─────────────────────────────────────────────────────────┘
              │
              ▼
    ┌─────────────────────┐
    │   有 Token ?        │
    └─────────────────────┘
       │              │
      Yes            No
       │              │
       ▼              ▼
  ┌─────────┐   ┌─────────────────────┐
  │ 验证    │   │ 显示 LoginDialog     │
  │ Token   │   │  (登录/注册/设备码)   │
  └─────────┘   └─────────────────────┘
       │
       ▼
  ┌─────────────────────┐
  │ Token 有效 → logged_in │
  │ Token 无效 → logged_out│
  └─────────────────────┘
```

## API 层 (api/auth.ts)

### 类型定义

```typescript
interface AuthStatus {
  status: 'logged_out' | 'pending' | 'logged_in'
  is_logged_in: boolean
  user_info?: UserInfo
  tokenExpired?: boolean
}

interface UserInfo {
  id: string
  username: string
  email: string
  image_url?: string
  provider?: string
  created_at?: string
  updated_at?: string
}

interface DeviceAuthResponse {
  status: string
  code: string
  expires_at: string
  message: string
}

interface DeviceAuthPollResponse {
  status: 'pending' | 'authorized' | 'expired' | 'error'
  message?: string
  token?: string
  user_info?: UserInfo
}
```

### API 函数

| 函数 | 说明 | 端点 |
|------|------|------|
| `auth_register(username, email, password)` | 用户注册 | POST `/api/auth/register` |
| `auth_login(username, password)` | 用户名密码登录 | POST `/api/auth/login` |
| `startDeviceAuth()` | 启动设备码登录 | POST `/api/device/auth` |
| `pollDeviceAuth(deviceCode)` | 轮询设备码授权 | GET `/api/device/poll?code=xxx` |
| `getAuthStatus()` | 获取认证状态 | 检查 Token |
| `logout()` | 登出 | 清除 localStorage |
| `getAccessToken()` | 获取 Token | localStorage 读取 |
| `authenticatedFetch(url, options)` | 带 Token 的请求 | 封装 Authorization |
| `refreshToken(token)` | 刷新 Token | GET `/api/device/refresh-token` |

### Token 类型

| 类型 | 前缀 | 刷新方式 |
|------|------|----------|
| 本地注册 | `local_<uuid>` | POST `/api/auth/refresh-token` |
| 设备码 | 其他 | GET `/api/device/refresh-token` |

### Token 刷新逻辑

```typescript
export async function getAuthStatus(): Promise<AuthStatus> {
  const token = localStorage.getItem('jaaz_access_token')
  const userInfo = localStorage.getItem('jaaz_user_info')

  if (token && userInfo) {
    try {
      if (token.startsWith('local_')) {
        // 本地 Token 刷新
        const response = await fetch('/api/auth/refresh-token', {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (response.ok) {
          const data = await response.json()
          if (data.valid === false) {
            // Token 无效，移除
            localStorage.removeItem('jaaz_access_token')
            localStorage.removeItem('jaaz_user_info')
            return { status: 'logged_out', is_logged_in: false }
          }
          if (data.new_token) {
            localStorage.setItem('jaaz_access_token', data.new_token)
          }
        }
      } else {
        // 设备码 Token 刷新
        const newToken = await refreshToken(token)
        localStorage.setItem('jaaz_access_token', newToken)
      }

      return {
        status: 'logged_in',
        is_logged_in: true,
        user_info: JSON.parse(userInfo),
      }
    } catch (error) {
      // 网络错误时保持登录状态
      return { status: 'logged_in', is_logged_in: true }
    }
  }

  return { status: 'logged_out', is_logged_in: false }
}
```

## AuthContext (contexts/AuthContext.tsx)

```typescript
interface AuthContextType {
  authStatus: AuthStatus
  isLoading: boolean
  refreshAuth: () => Promise<void>
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [authStatus, setAuthStatus] = useState<AuthStatus>({
    status: 'logged_out',
    is_logged_in: false,
  })
  const [isLoading, setIsLoading] = useState(true)

  const refreshAuth = async () => {
    setIsLoading(true)
    const status = await getAuthStatus()
    if (status.tokenExpired) {
      toast.error('登录状态已过期，请重新登录')
    }
    setAuthStatus(status)
    setIsLoading(false)
  }

  useEffect(() => {
    refreshAuth()
  }, [])

  return (
    <AuthContext.Provider value={{ authStatus, isLoading, refreshAuth }}>
      {children}
    </AuthContext.Provider>
  )
}
```

## 登录方式

### 1. 用户名密码登录

```typescript
const handleLogin = async (username: string, password: string) => {
  const { token, user_info } = await auth_login(username, password)
  saveAuthData(token, user_info)
  await updateJaazApiKey(token)
  refreshAuth()
}
```

### 2. 用户注册

```typescript
const handleRegister = async (username: string, email: string, password: string) => {
  await auth_register(username, email, password)
  // 自动登录
  await handleLogin(username, password)
}
```

### 3. 设备码登录

```typescript
// 启动设备码登录
const startDeviceLogin = async () => {
  const { code } = await startDeviceAuth()
  // Electron: 打开浏览器
  window.electronAPI?.openBrowserUrl(`${BASE_API_URL}/auth/device?code=${code}`)
  // Web: window.open(...)
}

// 轮询授权状态
const pollAuth = async (code: string) => {
  const result = await pollDeviceAuth(code)
  if (result.status === 'authorized') {
    saveAuthData(result.token!, result.user_info!)
    refreshAuth()
  }
}
```

## Token 存储

```typescript
// localStorage keys
'jaaz_access_token'   // Token 字符串
'jaaz_user_info'      // UserInfo JSON 字符串
```

## 登出

```typescript
export async function logout(): Promise<void> {
  localStorage.removeItem('jaaz_access_token')
  localStorage.removeItem('jaaz_user_info')
  await clearJaazApiKey()
}
```

## 认证请求封装

```typescript
export async function authenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getAccessToken()

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  return fetch(url, { ...options, headers })
}
```

## Provider 配置更新

登录后需要更新后端 Provider 的 API Key：

```typescript
// api/config.ts
export async function updateJaazApiKey(token: string): Promise<void> {
  const config = await getConfig()
  if (config.jaaz) {
    config.jaaz.api_key = token
    await updateConfig(config)
  }
}
```

## 登录对话框 (LoginDialog.tsx)

**功能**:
- 用户名密码登录/注册 Tab
- 设备码登录 Tab
- Token 过期提示

**状态**:
- `mode`: 'login' | 'register'
- `deviceCode`: 设备码
- `isPolling`: 是否正在轮询
